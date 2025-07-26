"""
Machine Learning prediction models for visa bulletin forecasting
"""
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report

from .models import (
    VisaBulletin, CategoryData, PredictionResult, TrendAnalysis,
    VisaCategory, CountryCode, BulletinStatus
)
from .database import VisaDatabase


@dataclass
class ModelFeatures:
    """Feature engineering data for ML models"""
    category: str
    country: str
    fiscal_year: int
    month: int
    days_since_epoch: int
    days_advancement: float
    volatility_score: float
    trend_slope: float
    seasonal_factor: float
    country_specific_factor: float


class TrendAnalyzer:
    """Analyzes historical trends in visa bulletin data"""
    
    def __init__(self, database: VisaDatabase):
        self.database = database
    
    def analyze_category_trend(self, category: VisaCategory, country: CountryCode,
                             start_year: int = None, end_year: int = None) -> TrendAnalysis:
        """Analyze trend for a specific category and country"""
        history = self.database.get_category_history(category, country, start_year, end_year)
        
        if len(history) < 2:
            return TrendAnalysis(
                category=category,
                country=country,
                start_date=date.today(),
                end_date=date.today(),
                total_advancement_days=0,
                average_monthly_advancement=0.0,
                volatility_score=0.0,
                trend_direction="stable"
            )
        
        # Extract date progression
        valid_dates = []
        for cat_data in history:
            if cat_data.final_action_date and cat_data.status == BulletinStatus.DATE_SPECIFIED:
                valid_dates.append(cat_data.final_action_date)
        
        if len(valid_dates) < 2:
            return TrendAnalysis(
                category=category,
                country=country,
                start_date=history[0].final_action_date or date.today(),
                end_date=history[-1].final_action_date or date.today(),
                total_advancement_days=0,
                average_monthly_advancement=0.0,
                volatility_score=0.0,
                trend_direction="stable"
            )
        
        # Calculate advancement metrics
        start_date = valid_dates[0]
        end_date = valid_dates[-1]
        total_advancement_days = (end_date - start_date).days
        
        # Calculate monthly advancements
        monthly_advancements = []
        for i in range(1, len(valid_dates)):
            days_diff = (valid_dates[i] - valid_dates[i-1]).days
            monthly_advancements.append(days_diff)
        
        avg_monthly_advancement = np.mean(monthly_advancements) if monthly_advancements else 0.0
        volatility_score = np.std(monthly_advancements) if len(monthly_advancements) > 1 else 0.0
        
        # Determine trend direction
        if avg_monthly_advancement > 5:
            trend_direction = "advancing"
        elif avg_monthly_advancement < -5:
            trend_direction = "retrogressing"
        else:
            trend_direction = "stable"
        
        return TrendAnalysis(
            category=category,
            country=country,
            start_date=start_date,
            end_date=end_date,
            total_advancement_days=total_advancement_days,
            average_monthly_advancement=avg_monthly_advancement,
            volatility_score=volatility_score,
            trend_direction=trend_direction
        )
    
    def calculate_seasonal_factors(self, category: VisaCategory, country: CountryCode) -> Dict[int, float]:
        """Calculate seasonal advancement factors by month"""
        history = self.database.get_category_history(category, country)
        
        monthly_advancements = {i: [] for i in range(1, 13)}
        
        valid_entries = [(i, cat) for i, cat in enumerate(history) 
                        if cat.final_action_date and cat.status == BulletinStatus.DATE_SPECIFIED]
        
        for i in range(1, len(valid_entries)):
            prev_idx, prev_cat = valid_entries[i-1]
            curr_idx, curr_cat = valid_entries[i]
            
            advancement_days = (curr_cat.final_action_date - prev_cat.final_action_date).days
            # Estimate month (this would be better with actual bulletin dates)
            estimated_month = (curr_idx % 12) + 1
            monthly_advancements[estimated_month].append(advancement_days)
        
        # Calculate average advancement for each month
        seasonal_factors = {}
        overall_avg = np.mean([days for month_days in monthly_advancements.values() 
                              for days in month_days]) if any(monthly_advancements.values()) else 0
        
        for month in range(1, 13):
            if monthly_advancements[month]:
                month_avg = np.mean(monthly_advancements[month])
                seasonal_factors[month] = month_avg / overall_avg if overall_avg != 0 else 1.0
            else:
                seasonal_factors[month] = 1.0
        
        return seasonal_factors


class VisaPredictionModel:
    """Base class for visa bulletin prediction models"""
    
    def __init__(self, database: VisaDatabase):
        self.database = database
        self.trend_analyzer = TrendAnalyzer(database)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.model = None
        self.is_trained = False
        self.model_version = "1.0"
    
    def extract_features(self, history: List[CategoryData], category: VisaCategory, 
                        country: CountryCode) -> List[ModelFeatures]:
        """Extract features from historical data"""
        features = []
        
        # Get seasonal factors
        seasonal_factors = self.trend_analyzer.calculate_seasonal_factors(category, country)
        
        # Country-specific factors (simplified)
        country_factors = {
            CountryCode.INDIA: 0.3,  # Slower advancement due to high demand
            CountryCode.CHINA: 0.5,  # Moderate advancement
            CountryCode.WORLDWIDE: 1.0,  # Baseline
            CountryCode.MEXICO: 0.8,
            CountryCode.PHILIPPINES: 0.7
        }
        
        valid_entries = [(i, cat) for i, cat in enumerate(history) 
                        if cat.final_action_date and cat.status == BulletinStatus.DATE_SPECIFIED]
        
        for i in range(1, len(valid_entries)):
            prev_idx, prev_cat = valid_entries[i-1]
            curr_idx, curr_cat = valid_entries[i]
            
            # Calculate advancement
            days_advancement = (curr_cat.final_action_date - prev_cat.final_action_date).days
            
            # Calculate volatility (rolling standard deviation)
            if i >= 3:
                recent_advancements = []
                for j in range(max(0, i-3), i):
                    if j < len(valid_entries) - 1:
                        prev_entry = valid_entries[j]
                        next_entry = valid_entries[j+1]
                        adv = (next_entry[1].final_action_date - prev_entry[1].final_action_date).days
                        recent_advancements.append(adv)
                volatility = np.std(recent_advancements) if len(recent_advancements) > 1 else 0.0
            else:
                volatility = 0.0
            
            # Calculate trend slope
            if i >= 2:
                x_vals = list(range(i-1, i+1))
                y_vals = []
                for j in range(i-1, i+1):
                    if j < len(valid_entries):
                        days_since_epoch = (valid_entries[j][1].final_action_date - date(1970, 1, 1)).days
                        y_vals.append(days_since_epoch)
                if len(y_vals) == 2:
                    trend_slope = y_vals[1] - y_vals[0]
                else:
                    trend_slope = 0.0
            else:
                trend_slope = 0.0
            
            # Estimate fiscal year and month (simplified)
            fiscal_year = 2024  # Would be calculated from actual data
            month = (curr_idx % 12) + 1
            
            feature = ModelFeatures(
                category=category.value,
                country=country.value,
                fiscal_year=fiscal_year,
                month=month,
                days_since_epoch=(curr_cat.final_action_date - date(1970, 1, 1)).days,
                days_advancement=days_advancement,
                volatility_score=volatility,
                trend_slope=trend_slope,
                seasonal_factor=seasonal_factors.get(month, 1.0),
                country_specific_factor=country_factors.get(country, 1.0)
            )
            features.append(feature)
        
        return features
    
    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from all available historical data"""
        all_features = []
        all_targets = []
        
        # Get data for all categories and countries
        for category in VisaCategory:
            for country in CountryCode:
                history = self.database.get_category_history(category, country)
                if len(history) < 3:  # Need minimum data
                    continue
                
                features = self.extract_features(history, category, country)
                
                # For each feature, the target is the next advancement
                for i in range(len(features) - 1):
                    all_features.append(features[i])
                    all_targets.append(features[i + 1].days_advancement)
        
        if not all_features:
            raise ValueError("No training data available")
        
        # Convert features to DataFrame
        feature_data = []
        for feature in all_features:
            feature_data.append([
                self.label_encoder.fit_transform([feature.category])[0] if hasattr(self, 'label_encoder') else hash(feature.category) % 100,
                self.label_encoder.fit_transform([feature.country])[0] if hasattr(self, 'label_encoder') else hash(feature.country) % 100,
                feature.fiscal_year,
                feature.month,
                feature.days_since_epoch,
                feature.days_advancement,
                feature.volatility_score,
                feature.trend_slope,
                feature.seasonal_factor,
                feature.country_specific_factor
            ])
        
        columns = ['category_encoded', 'country_encoded', 'fiscal_year', 'month', 
                  'days_since_epoch', 'days_advancement', 'volatility_score', 
                  'trend_slope', 'seasonal_factor', 'country_specific_factor']
        
        X = pd.DataFrame(feature_data, columns=columns)
        y = pd.Series(all_targets)
        
        return X, y
    
    def train(self) -> Dict[str, Any]:
        """Train the model and return performance metrics"""
        raise NotImplementedError("Must be implemented by subclasses")
    
    def predict(self, category: VisaCategory, country: CountryCode, 
               target_month: int, target_year: int) -> PredictionResult:
        """Make a prediction for the specified category, country, and target date"""
        raise NotImplementedError("Must be implemented by subclasses")
    
    def save_model(self, filepath: str):
        """Save the trained model to disk"""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'model_version': self.model_version,
            'is_trained': self.is_trained
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load a trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data['label_encoder']
        self.model_version = model_data['model_version']
        self.is_trained = model_data['is_trained']


class RandomForestPredictor(VisaPredictionModel):
    """Random Forest model for visa bulletin prediction"""
    
    def __init__(self, database: VisaDatabase, n_estimators: int = 100, max_depth: int = 10):
        super().__init__(database)
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
    
    def train(self) -> Dict[str, Any]:
        """Train the Random Forest model"""
        X, y = self.prepare_training_data()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate model
        train_predictions = self.model.predict(X_train)
        test_predictions = self.model.predict(X_test)
        
        train_mae = mean_absolute_error(y_train, train_predictions)
        test_mae = mean_absolute_error(y_test, test_predictions)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring='neg_mean_absolute_error')
        
        metrics = {
            'model_type': 'RandomForest',
            'train_mae': train_mae,
            'test_mae': test_mae,
            'cv_mae_mean': -cv_scores.mean(),
            'cv_mae_std': cv_scores.std(),
            'feature_importance': dict(zip(X.columns, self.model.feature_importances_)),
            'n_samples': len(X)
        }
        
        return metrics
    
    def predict(self, category: VisaCategory, country: CountryCode, 
               target_month: int, target_year: int) -> PredictionResult:
        """Make a prediction using the trained Random Forest model"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Get recent history for feature extraction
        history = self.database.get_category_history(category, country)
        if len(history) < 2:
            return PredictionResult(
                category=category,
                country=country,
                predicted_date=None,
                confidence_score=0.0,
                prediction_type="insufficient_data",
                target_month=target_month,
                target_year=target_year,
                model_version=self.model_version
            )
        
        features = self.extract_features(history, category, country)
        if not features:
            return PredictionResult(
                category=category,
                country=country,
                predicted_date=None,
                confidence_score=0.0,
                prediction_type="no_features",
                target_month=target_month,
                target_year=target_year,
                model_version=self.model_version
            )
        
        # Use the most recent feature
        latest_feature = features[-1]
        
        # Create feature vector
        feature_vector = [[
            hash(latest_feature.category) % 100,
            hash(latest_feature.country) % 100,
            target_year,
            target_month,
            latest_feature.days_since_epoch,
            latest_feature.days_advancement,
            latest_feature.volatility_score,
            latest_feature.trend_slope,
            latest_feature.seasonal_factor,
            latest_feature.country_specific_factor
        ]]
        
        # Scale features
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Make prediction
        predicted_advancement = self.model.predict(feature_vector_scaled)[0]
        
        # Calculate predicted date
        last_date = None
        for cat_data in reversed(history):
            if cat_data.final_action_date and cat_data.status == BulletinStatus.DATE_SPECIFIED:
                last_date = cat_data.final_action_date
                break
        
        if last_date:
            predicted_date = last_date + timedelta(days=int(predicted_advancement))
        else:
            predicted_date = None
        
        # Determine prediction type and confidence
        if predicted_advancement > 10:
            prediction_type = "advancement"
        elif predicted_advancement < -10:
            prediction_type = "retrogression"
        else:
            prediction_type = "stable"
        
        # Simple confidence calculation based on model variance
        try:
            predictions = [tree.predict(feature_vector_scaled)[0] for tree in self.model.estimators_]
            confidence_score = max(0.0, min(1.0, 1.0 - (np.std(predictions) / 30.0)))
        except:
            confidence_score = 0.5
        
        return PredictionResult(
            category=category,
            country=country,
            predicted_date=predicted_date,
            confidence_score=confidence_score,
            prediction_type=prediction_type,
            target_month=target_month,
            target_year=target_year,
            model_version=self.model_version
        )


class LogisticRegressionPredictor(VisaPredictionModel):
    """Logistic Regression model for visa bulletin trend classification"""
    
    def __init__(self, database: VisaDatabase):
        super().__init__(database)
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.regression_model = LinearRegression()
    
    def prepare_classification_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for trend classification"""
        X, y = self.prepare_training_data()
        
        # Convert regression targets to classification labels
        y_class = []
        for advancement in y:
            if advancement > 10:
                y_class.append('advancing')
            elif advancement < -10:
                y_class.append('retrogressing')
            else:
                y_class.append('stable')
        
        return X, pd.Series(y_class)
    
    def train(self) -> Dict[str, Any]:
        """Train the Logistic Regression model"""
        # Classification model
        X_class, y_class = self.prepare_classification_data()
        X_class_scaled = self.scaler.fit_transform(X_class)
        
        X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(
            X_class_scaled, y_class, test_size=0.2, random_state=42, stratify=y_class
        )
        
        self.model.fit(X_train_class, y_train_class)
        
        # Regression model for magnitude prediction
        X_reg, y_reg = self.prepare_training_data()
        X_reg_scaled = self.scaler.transform(X_reg)  # Use same scaler
        
        X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
            X_reg_scaled, y_reg, test_size=0.2, random_state=42
        )
        
        self.regression_model.fit(X_train_reg, y_train_reg)
        self.is_trained = True
        
        # Evaluate models
        class_predictions = self.model.predict(X_test_class)
        class_accuracy = accuracy_score(y_test_class, class_predictions)
        
        reg_predictions = self.regression_model.predict(X_test_reg)
        reg_mae = mean_absolute_error(y_test_reg, reg_predictions)
        
        metrics = {
            'model_type': 'LogisticRegression',
            'classification_accuracy': class_accuracy,
            'regression_mae': reg_mae,
            'class_report': classification_report(y_test_class, class_predictions, output_dict=True),
            'n_samples': len(X_class)
        }
        
        return metrics
    
    def predict(self, category: VisaCategory, country: CountryCode, 
               target_month: int, target_year: int) -> PredictionResult:
        """Make a prediction using the trained Logistic Regression model"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Get recent history for feature extraction
        history = self.database.get_category_history(category, country)
        if len(history) < 2:
            return PredictionResult(
                category=category,
                country=country,
                predicted_date=None,
                confidence_score=0.0,
                prediction_type="insufficient_data",
                target_month=target_month,
                target_year=target_year,
                model_version=self.model_version
            )
        
        features = self.extract_features(history, category, country)
        if not features:
            return PredictionResult(
                category=category,
                country=country,
                predicted_date=None,
                confidence_score=0.0,
                prediction_type="no_features",
                target_month=target_month,
                target_year=target_year,
                model_version=self.model_version
            )
        
        # Use the most recent feature
        latest_feature = features[-1]
        
        # Create feature vector
        feature_vector = [[
            hash(latest_feature.category) % 100,
            hash(latest_feature.country) % 100,
            target_year,
            target_month,
            latest_feature.days_since_epoch,
            latest_feature.days_advancement,
            latest_feature.volatility_score,
            latest_feature.trend_slope,
            latest_feature.seasonal_factor,
            latest_feature.country_specific_factor
        ]]
        
        # Scale features
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Make predictions
        trend_prediction = self.model.predict(feature_vector_scaled)[0]
        trend_proba = self.model.predict_proba(feature_vector_scaled)[0]
        predicted_advancement = self.regression_model.predict(feature_vector_scaled)[0]
        
        # Calculate predicted date
        last_date = None
        for cat_data in reversed(history):
            if cat_data.final_action_date and cat_data.status == BulletinStatus.DATE_SPECIFIED:
                last_date = cat_data.final_action_date
                break
        
        if last_date:
            predicted_date = last_date + timedelta(days=int(predicted_advancement))
        else:
            predicted_date = None
        
        # Confidence is the maximum probability from classification
        confidence_score = float(np.max(trend_proba))
        
        return PredictionResult(
            category=category,
            country=country,
            predicted_date=predicted_date,
            confidence_score=confidence_score,
            prediction_type=trend_prediction,
            target_month=target_month,
            target_year=target_year,
            model_version=self.model_version
        )


class ModelEvaluator:
    """Utilities for model training and evaluation"""
    
    def __init__(self, database: VisaDatabase):
        self.database = database
    
    def compare_models(self, models: List[VisaPredictionModel]) -> Dict[str, Any]:
        """Compare performance of multiple models"""
        results = {}
        
        for model in models:
            try:
                metrics = model.train()
                results[metrics['model_type']] = metrics
            except Exception as e:
                results[model.__class__.__name__] = {'error': str(e)}
        
        return results
    
    def backtest_model(self, model: VisaPredictionModel, test_months: int = 6) -> Dict[str, Any]:
        """Perform backtesting on the model"""
        # This would implement a backtesting strategy
        # For now, return placeholder results
        return {
            'backtest_periods': test_months,
            'average_error': 0.0,
            'accuracy': 0.0,
            'note': 'Backtesting not fully implemented yet'
        }
    
    def get_model_recommendations(self) -> Dict[str, str]:
        """Get recommendations for model usage"""
        return {
            'RandomForest': 'Best for regression tasks and feature importance analysis',
            'LogisticRegression': 'Best for trend classification and interpretability',
            'general': 'Use ensemble of both models for robust predictions'
        }


# Factory function for easy model creation
def create_predictor(model_type: str, database: VisaDatabase) -> VisaPredictionModel:
    """Factory function to create prediction models"""
    if model_type.lower() == 'randomforest':
        return RandomForestPredictor(database)
    elif model_type.lower() == 'logisticregression':
        return LogisticRegressionPredictor(database)
    else:
        raise ValueError(f"Unknown model type: {model_type}")