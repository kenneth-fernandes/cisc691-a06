"""
Unit tests for visa prediction models
"""
import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from visa.models import (
    VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus,
    PredictionResult, TrendAnalysis
)
from visa.database import VisaDatabase
from visa.predictor import (
    TrendAnalyzer, ModelFeatures, VisaPredictionModel,
    RandomForestPredictor, LogisticRegressionPredictor,
    ModelEvaluator, create_predictor
)


@pytest.fixture
def mock_database():
    """Create a mock database for testing"""
    db = Mock(spec=VisaDatabase)
    return db


@pytest.fixture
def sample_history():
    """Create sample historical data for testing"""
    history = []
    base_date = date(2023, 1, 1)
    
    for i in range(12):  # 12 months of data
        cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=base_date + timedelta(days=i*30 + i*10),  # Progressive advancement
            filing_date=base_date + timedelta(days=i*30 + i*15),
            status=BulletinStatus.DATE_SPECIFIED,
            notes=f"Month {i+1}"
        )
        history.append(cat_data)
    
    return history


@pytest.fixture
def sample_bulletin():
    """Create a sample visa bulletin"""
    bulletin = VisaBulletin(
        bulletin_date=date(2024, 1, 1),
        fiscal_year=2024,
        month=1,
        year=2024
    )
    
    # Add some category data
    for category in [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3]:
        for country in [CountryCode.INDIA, CountryCode.CHINA, CountryCode.WORLDWIDE]:
            cat_data = CategoryData(
                category=category,
                country=country,
                final_action_date=date(2023, 6, 1),
                filing_date=date(2023, 8, 1),
                status=BulletinStatus.DATE_SPECIFIED
            )
            bulletin.add_category_data(cat_data)
    
    return bulletin


class TestTrendAnalyzer:
    """Test the TrendAnalyzer class"""
    
    def test_init(self, mock_database):
        """Test TrendAnalyzer initialization"""
        analyzer = TrendAnalyzer(mock_database)
        assert analyzer.database == mock_database
    
    def test_analyze_category_trend_with_data(self, mock_database, sample_history):
        """Test trend analysis with sufficient data"""
        mock_database.get_category_history.return_value = sample_history
        
        analyzer = TrendAnalyzer(mock_database)
        trend = analyzer.analyze_category_trend(VisaCategory.EB2, CountryCode.INDIA)
        
        assert isinstance(trend, TrendAnalysis)
        assert trend.category == VisaCategory.EB2
        assert trend.country == CountryCode.INDIA
        assert trend.total_advancement_days > 0
        assert trend.trend_direction in ["advancing", "retrogressing", "stable"]
    
    def test_analyze_category_trend_insufficient_data(self, mock_database):
        """Test trend analysis with insufficient data"""
        mock_database.get_category_history.return_value = []
        
        analyzer = TrendAnalyzer(mock_database)
        trend = analyzer.analyze_category_trend(VisaCategory.EB2, CountryCode.INDIA)
        
        assert trend.total_advancement_days == 0
        assert trend.average_monthly_advancement == 0.0
        assert trend.trend_direction == "stable"
    
    def test_calculate_seasonal_factors(self, mock_database, sample_history):
        """Test seasonal factor calculation"""
        mock_database.get_category_history.return_value = sample_history
        
        analyzer = TrendAnalyzer(mock_database)
        factors = analyzer.calculate_seasonal_factors(VisaCategory.EB2, CountryCode.INDIA)
        
        assert isinstance(factors, dict)
        assert len(factors) == 12  # 12 months
        for month in range(1, 13):
            assert month in factors
            assert isinstance(factors[month], float)


class TestModelFeatures:
    """Test the ModelFeatures dataclass"""
    
    def test_model_features_creation(self):
        """Test creating ModelFeatures"""
        feature = ModelFeatures(
            category="EB-2",
            country="India",
            fiscal_year=2024,
            month=6,
            days_since_epoch=19000,
            days_advancement=15.0,
            volatility_score=5.2,
            trend_slope=2.1,
            seasonal_factor=1.1,
            country_specific_factor=0.3
        )
        
        assert feature.category == "EB-2"
        assert feature.country == "India"
        assert feature.fiscal_year == 2024
        assert feature.days_advancement == 15.0


class TestRandomForestPredictor:
    """Test the RandomForestPredictor class"""
    
    def test_init(self, mock_database):
        """Test RandomForestPredictor initialization"""
        predictor = RandomForestPredictor(mock_database)
        assert predictor.database == mock_database
        assert not predictor.is_trained
        assert predictor.model is not None
    
    def test_extract_features(self, mock_database, sample_history):
        """Test feature extraction"""
        # Mock the trend analyzer's seasonal factors method
        mock_database.get_category_history.return_value = sample_history
        
        predictor = RandomForestPredictor(mock_database)
        features = predictor.extract_features(sample_history, VisaCategory.EB2, CountryCode.INDIA)
        
        assert isinstance(features, list)
        assert len(features) > 0
        for feature in features:
            assert isinstance(feature, ModelFeatures)
    
    @patch('visa.predictor.RandomForestPredictor.prepare_training_data')
    def test_train_success(self, mock_prepare_data, mock_database):
        """Test successful model training"""
        # Mock training data with more samples for proper train/test split
        X = pd.DataFrame({
            'category_encoded': [1, 2, 3, 1, 2, 3, 1, 2, 3, 1],
            'country_encoded': [1, 1, 2, 1, 1, 2, 1, 1, 2, 1],
            'fiscal_year': [2023, 2023, 2024, 2023, 2023, 2024, 2023, 2023, 2024, 2023],
            'month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'days_since_epoch': [19000, 19030, 19060, 19090, 19120, 19150, 19180, 19210, 19240, 19270],
            'days_advancement': [10, 15, 20, 12, 18, 22, 14, 16, 24, 11],
            'volatility_score': [2.0, 3.0, 1.5, 2.5, 3.5, 1.0, 2.2, 3.2, 1.8, 2.1],
            'trend_slope': [1.0, 2.0, 0.5, 1.5, 2.5, 0.8, 1.2, 2.2, 0.7, 1.1],
            'seasonal_factor': [1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0],
            'country_specific_factor': [0.3, 0.3, 0.5, 0.3, 0.3, 0.5, 0.3, 0.3, 0.5, 0.3]
        })
        y = pd.Series([12, 18, 22, 14, 20, 24, 16, 18, 26, 13])
        
        mock_prepare_data.return_value = (X, y)
        
        predictor = RandomForestPredictor(mock_database)
        metrics = predictor.train()
        
        assert predictor.is_trained
        assert isinstance(metrics, dict)
        assert 'model_type' in metrics
        assert metrics['model_type'] == 'RandomForest'
        assert 'train_mae' in metrics
        assert 'test_mae' in metrics
    
    def test_predict_untrained_model(self, mock_database):
        """Test prediction with untrained model"""
        predictor = RandomForestPredictor(mock_database)
        
        with pytest.raises(ValueError, match="Model must be trained"):
            predictor.predict(VisaCategory.EB2, CountryCode.INDIA, 6, 2024)
    
    def test_predict_insufficient_data(self, mock_database):
        """Test prediction with insufficient historical data"""
        mock_database.get_category_history.return_value = []
        
        predictor = RandomForestPredictor(mock_database)
        predictor.is_trained = True  # Simulate trained model
        
        result = predictor.predict(VisaCategory.EB2, CountryCode.INDIA, 6, 2024)
        
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == "insufficient_data"
        assert result.confidence_score == 0.0
    
    def test_model_persistence(self, mock_database):
        """Test saving and loading model"""
        predictor = RandomForestPredictor(mock_database)
        predictor.is_trained = True
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
            try:
                predictor.save_model(tmp_file.name)
                
                # Create new predictor and load model
                new_predictor = RandomForestPredictor(mock_database)
                new_predictor.load_model(tmp_file.name)
                
                assert new_predictor.is_trained
                assert new_predictor.model_version == predictor.model_version
            finally:
                os.unlink(tmp_file.name)
    
    def test_save_untrained_model(self, mock_database):
        """Test saving untrained model raises error"""
        predictor = RandomForestPredictor(mock_database)
        
        with pytest.raises(ValueError, match="Model must be trained"):
            predictor.save_model("dummy_path.pkl")


class TestLogisticRegressionPredictor:
    """Test the LogisticRegressionPredictor class"""
    
    def test_init(self, mock_database):
        """Test LogisticRegressionPredictor initialization"""
        predictor = LogisticRegressionPredictor(mock_database)
        assert predictor.database == mock_database
        assert not predictor.is_trained
        assert predictor.model is not None
        assert predictor.regression_model is not None
    
    @patch('visa.predictor.LogisticRegressionPredictor.prepare_training_data')
    @patch('visa.predictor.LogisticRegressionPredictor.prepare_classification_data')
    def test_train_success(self, mock_prepare_class, mock_prepare_reg, mock_database):
        """Test successful model training"""
        # Mock classification data with balanced classes
        X_class = pd.DataFrame({
            'category_encoded': [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3],
            'country_encoded': [1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2],
            'fiscal_year': [2023, 2023, 2024, 2023, 2023, 2024, 2023, 2023, 2024, 2023, 2023, 2024],
            'month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'days_since_epoch': [19000, 19030, 19060, 19090, 19120, 19150, 19180, 19210, 19240, 19270, 19300, 19330],
            'days_advancement': [15, 20, 25, 5, 8, 30, 12, 18, 22, 3, 6, 28],
            'volatility_score': [2.0, 3.0, 1.5, 2.5, 3.5, 1.0, 2.2, 3.2, 1.8, 2.1, 3.1, 1.2],
            'trend_slope': [1.0, 2.0, 0.5, 1.5, 2.5, 0.8, 1.2, 2.2, 0.7, 1.1, 2.1, 0.9],
            'seasonal_factor': [1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 1.0, 1.1, 0.9],
            'country_specific_factor': [0.3, 0.3, 0.5, 0.3, 0.3, 0.5, 0.3, 0.3, 0.5, 0.3, 0.3, 0.5]
        })
        # Balanced classes: 4 advancing, 4 stable, 4 retrogressing
        y_class = pd.Series(['advancing', 'advancing', 'advancing', 'stable', 'stable', 'advancing', 
                           'advancing', 'advancing', 'advancing', 'stable', 'stable', 'advancing'])
        
        # Mock regression data
        y_reg = pd.Series([17, 22, 27, 7, 10, 32, 14, 20, 24, 5, 8, 30])
        
        mock_prepare_class.return_value = (X_class, y_class)
        mock_prepare_reg.return_value = (X_class, y_reg)
        
        predictor = LogisticRegressionPredictor(mock_database)
        metrics = predictor.train()
        
        assert predictor.is_trained
        assert isinstance(metrics, dict)
        assert 'model_type' in metrics
        assert metrics['model_type'] == 'LogisticRegression'
        assert 'classification_accuracy' in metrics
        assert 'regression_mae' in metrics


class TestModelEvaluator:
    """Test the ModelEvaluator class"""
    
    def test_init(self, mock_database):
        """Test ModelEvaluator initialization"""
        evaluator = ModelEvaluator(mock_database)
        assert evaluator.database == mock_database
    
    @patch('visa.predictor.RandomForestPredictor.train')
    @patch('visa.predictor.LogisticRegressionPredictor.train')
    def test_compare_models(self, mock_lr_train, mock_rf_train, mock_database):
        """Test model comparison"""
        mock_rf_train.return_value = {'model_type': 'RandomForest', 'test_mae': 5.0}
        mock_lr_train.return_value = {'model_type': 'LogisticRegression', 'classification_accuracy': 0.85}
        
        evaluator = ModelEvaluator(mock_database)
        rf_model = RandomForestPredictor(mock_database)
        lr_model = LogisticRegressionPredictor(mock_database)
        
        results = evaluator.compare_models([rf_model, lr_model])
        
        assert isinstance(results, dict)
        assert 'RandomForest' in results
        assert 'LogisticRegression' in results
    
    def test_get_model_recommendations(self, mock_database):
        """Test getting model recommendations"""
        evaluator = ModelEvaluator(mock_database)
        recommendations = evaluator.get_model_recommendations()
        
        assert isinstance(recommendations, dict)
        assert 'RandomForest' in recommendations
        assert 'LogisticRegression' in recommendations
        assert 'general' in recommendations


class TestCreatePredictor:
    """Test the create_predictor factory function"""
    
    def test_create_random_forest(self, mock_database):
        """Test creating RandomForest predictor"""
        predictor = create_predictor('randomforest', mock_database)
        assert isinstance(predictor, RandomForestPredictor)
    
    def test_create_logistic_regression(self, mock_database):
        """Test creating LogisticRegression predictor"""
        predictor = create_predictor('logisticregression', mock_database)
        assert isinstance(predictor, LogisticRegressionPredictor)
    
    def test_create_unknown_model(self, mock_database):
        """Test creating unknown model type raises error"""
        with pytest.raises(ValueError, match="Unknown model type"):
            create_predictor('unknown_model', mock_database)
    
    def test_case_insensitive_creation(self, mock_database):
        """Test case-insensitive model creation"""
        predictor1 = create_predictor('RandomForest', mock_database)
        predictor2 = create_predictor('RANDOMFOREST', mock_database)
        predictor3 = create_predictor('LogisticRegression', mock_database)
        
        assert isinstance(predictor1, RandomForestPredictor)
        assert isinstance(predictor2, RandomForestPredictor)
        assert isinstance(predictor3, LogisticRegressionPredictor)


@pytest.mark.integration
class TestPredictorIntegration:
    """Integration tests for the prediction system"""
    
    def test_end_to_end_prediction_flow(self, sample_history):
        """Test complete prediction workflow"""
        # This would require a real database with data
        # For now, it's a placeholder for future integration tests
        pass
    
    def test_real_database_integration(self):
        """Test with real database (requires test data)"""
        # This would test with actual SQLite database
        # Placeholder for future implementation
        pass


# Additional fixtures for complex testing scenarios
@pytest.fixture
def complex_history():
    """Create complex historical data with various patterns"""
    history = []
    base_date = date(2020, 1, 1)
    
    # Create data with different patterns
    patterns = [
        10,   # steady advancement
        15,   # acceleration
        5,    # deceleration
        -2,   # slight retrogression
        20,   # big jump
        8,    # return to normal
        12,   # steady
        0,    # no movement
        25,   # big advancement
        10    # normal
    ]
    
    cumulative_days = 0
    for i, advancement in enumerate(patterns):
        cumulative_days += advancement
        cat_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=base_date + timedelta(days=cumulative_days),
            filing_date=base_date + timedelta(days=cumulative_days + 60),
            status=BulletinStatus.DATE_SPECIFIED,
            notes=f"Month {i+1}"
        )
        history.append(cat_data)
    
    return history


@pytest.fixture
def mixed_status_history():
    """Create history with mixed statuses (current, unavailable, dates)"""
    history = []
    base_date = date(2023, 1, 1)
    statuses = [
        BulletinStatus.DATE_SPECIFIED,
        BulletinStatus.DATE_SPECIFIED,
        BulletinStatus.CURRENT,
        BulletinStatus.UNAVAILABLE,
        BulletinStatus.DATE_SPECIFIED,
        BulletinStatus.DATE_SPECIFIED
    ]
    
    for i, status in enumerate(statuses):
        cat_data = CategoryData(
            category=VisaCategory.EB3,
            country=CountryCode.CHINA,
            final_action_date=base_date + timedelta(days=i*30) if status == BulletinStatus.DATE_SPECIFIED else None,
            filing_date=base_date + timedelta(days=i*30 + 60) if status == BulletinStatus.DATE_SPECIFIED else None,
            status=status,
            notes=f"Month {i+1} - {status.value}"
        )
        history.append(cat_data)
    
    return history