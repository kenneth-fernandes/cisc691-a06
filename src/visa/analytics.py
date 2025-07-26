"""
Advanced analytics and trend calculation utilities for visa bulletin data
"""
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import logging

from .models import VisaBulletin, CategoryData, VisaCategory, CountryCode
from .repository import VisaBulletinRepository

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Advanced trend analysis for visa bulletin data"""
    
    def __init__(self, repository: Optional[VisaBulletinRepository] = None):
        self.repository = repository or VisaBulletinRepository()
    
    def calculate_advancement_trends(self, category: VisaCategory, country: CountryCode,
                                   years_back: int = 3) -> Dict[str, Any]:
        """Calculate detailed advancement trends with statistical analysis"""
        
        logger.info(f"Calculating trends for {category.value}-{country.value}")
        
        # Get historical data
        history = self.repository.get_category_history(category, country, years_back)
        
        if len(history) < 3:
            return {
                'status': 'insufficient_data',
                'data_points': len(history),
                'message': 'Need at least 3 data points for trend analysis'
            }
        
        # Sort by date (assuming history comes with bulletin metadata)
        # For now, we'll use the order as-is since the repository should return sorted data
        
        # Calculate monthly advancements
        advancements = []
        valid_dates = []
        
        for i in range(1, len(history)):
            prev_data = history[i-1]
            curr_data = history[i]
            
            if (prev_data.final_action_date and curr_data.final_action_date and 
                prev_data.status == 'DATE' and curr_data.status == 'DATE'):
                
                days_advancement = (curr_data.final_action_date - prev_data.final_action_date).days
                advancements.append(days_advancement)
                valid_dates.append(curr_data.final_action_date)
        
        if not advancements:
            return {
                'status': 'no_movement_data',
                'data_points': len(history),
                'message': 'No date-based movements found in historical data'
            }
        
        # Statistical analysis
        adv_array = np.array(advancements)
        
        analysis = {
            'status': 'success',
            'category': category.value,
            'country': country.value,
            'analysis_period': f'{len(history)} bulletins over {years_back} years',
            'data_points': len(advancements),
            
            # Basic statistics
            'total_advancement_days': int(np.sum(adv_array)),
            'average_advancement_days': float(np.mean(adv_array)),
            'median_advancement_days': float(np.median(adv_array)),
            'std_deviation': float(np.std(adv_array)),
            'min_advancement': int(np.min(adv_array)),
            'max_advancement': int(np.max(adv_array)),
            
            # Trend classification
            'trend_direction': self._classify_trend(adv_array),
            'volatility': self._calculate_volatility(adv_array),
            'consistency_score': self._calculate_consistency(adv_array),
            
            # Advanced metrics
            'momentum': self._calculate_momentum(adv_array),
            'seasonal_pattern': self._detect_seasonal_pattern(advancements, valid_dates),
            'prediction_confidence': self._calculate_prediction_confidence(adv_array),
            
            # Detailed breakdown
            'monthly_advancements': advancements,
            'positive_months': int(np.sum(adv_array > 0)),
            'negative_months': int(np.sum(adv_array < 0)),
            'stagnant_months': int(np.sum(adv_array == 0)),
            
            # Percentile analysis
            'percentiles': {
                '25th': float(np.percentile(adv_array, 25)),
                '50th': float(np.percentile(adv_array, 50)),
                '75th': float(np.percentile(adv_array, 75)),
                '90th': float(np.percentile(adv_array, 90))
            }
        }
        
        # Add interpretation
        analysis['interpretation'] = self._generate_trend_interpretation(analysis)
        
        return analysis
    
    def _classify_trend(self, advancements: np.ndarray) -> str:
        """Classify the overall trend direction"""
        avg_advancement = np.mean(advancements)
        recent_trend = np.mean(advancements[-6:]) if len(advancements) >= 6 else avg_advancement
        
        if avg_advancement > 15 and recent_trend > 10:
            return 'strongly_advancing'
        elif avg_advancement > 5 and recent_trend > 0:
            return 'advancing'
        elif avg_advancement < -15 and recent_trend < -10:
            return 'strongly_retrogressing'
        elif avg_advancement < -5 and recent_trend < 0:
            return 'retrogressing'
        elif abs(avg_advancement) <= 5:
            return 'stable'
        else:
            return 'mixed'
    
    def _calculate_volatility(self, advancements: np.ndarray) -> str:
        """Calculate volatility classification"""
        std_dev = np.std(advancements)
        
        if std_dev > 30:
            return 'high'
        elif std_dev > 15:
            return 'moderate'
        else:
            return 'low'
    
    def _calculate_consistency(self, advancements: np.ndarray) -> float:
        """Calculate consistency score (0-100)"""
        if len(advancements) < 2:
            return 0.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_val = np.mean(advancements)
        if mean_val == 0:
            return 50.0  # Neutral score for no movement
        
        cv = np.std(advancements) / abs(mean_val)
        
        # Convert to 0-100 scale (higher = more consistent)
        consistency = max(0, 100 - (cv * 20))
        return round(consistency, 2)
    
    def _calculate_momentum(self, advancements: np.ndarray) -> Dict[str, Any]:
        """Calculate trend momentum"""
        if len(advancements) < 6:
            return {'status': 'insufficient_data'}
        
        recent_period = advancements[-6:]  # Last 6 months
        earlier_period = advancements[-12:-6] if len(advancements) >= 12 else advancements[:-6]
        
        recent_avg = np.mean(recent_period)
        earlier_avg = np.mean(earlier_period)
        
        momentum_change = recent_avg - earlier_avg
        
        return {
            'recent_average': float(recent_avg),
            'earlier_average': float(earlier_avg),
            'momentum_change': float(momentum_change),
            'direction': 'accelerating' if momentum_change > 5 else 'decelerating' if momentum_change < -5 else 'stable'
        }
    
    def _detect_seasonal_pattern(self, advancements: List[int], dates: List[date]) -> Dict[str, Any]:
        """Detect seasonal patterns in advancement data"""
        if len(advancements) < 12:
            return {'status': 'insufficient_data'}
        
        # Group by month
        monthly_data = defaultdict(list)
        for adv, date_obj in zip(advancements, dates):
            monthly_data[date_obj.month].append(adv)
        
        # Calculate average advancement by month
        monthly_averages = {}
        for month, advs in monthly_data.items():
            if advs:
                monthly_averages[month] = sum(advs) / len(advs)
        
        if len(monthly_averages) < 6:
            return {'status': 'insufficient_monthly_data'}
        
        # Find best and worst months
        best_month = max(monthly_averages, key=monthly_averages.get)
        worst_month = min(monthly_averages, key=monthly_averages.get)
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return {
            'status': 'detected',
            'monthly_averages': {month_names[m-1]: round(avg, 1) for m, avg in monthly_averages.items()},
            'best_month': month_names[best_month-1],
            'worst_month': month_names[worst_month-1],
            'seasonal_variance': round(monthly_averages[best_month] - monthly_averages[worst_month], 1)
        }
    
    def _calculate_prediction_confidence(self, advancements: np.ndarray) -> Dict[str, Any]:
        """Calculate confidence level for predictions"""
        if len(advancements) < 6:
            return {'confidence': 'low', 'score': 25, 'reason': 'insufficient_data'}
        
        # Factors affecting confidence
        data_points = len(advancements)
        consistency = self._calculate_consistency(advancements)
        volatility = np.std(advancements)
        recent_stability = np.std(advancements[-6:]) if len(advancements) >= 6 else volatility
        
        # Calculate confidence score
        confidence_score = 0
        
        # More data points = higher confidence
        confidence_score += min(data_points * 2, 30)
        
        # Higher consistency = higher confidence
        confidence_score += consistency * 0.3
        
        # Lower volatility = higher confidence
        if volatility < 10:
            confidence_score += 20
        elif volatility < 20:
            confidence_score += 10
        
        # Recent stability adds confidence
        if recent_stability < volatility * 0.8:
            confidence_score += 15
        
        confidence_score = min(confidence_score, 100)
        
        if confidence_score >= 80:
            level = 'high'
        elif confidence_score >= 60:
            level = 'moderate'
        elif confidence_score >= 40:
            level = 'low'
        else:
            level = 'very_low'
        
        return {
            'confidence': level,
            'score': round(confidence_score, 1),
            'factors': {
                'data_points': data_points,
                'consistency': consistency,
                'volatility': round(volatility, 1),
                'recent_stability': round(recent_stability, 1)
            }
        }
    
    def _generate_trend_interpretation(self, analysis: Dict[str, Any]) -> str:
        """Generate human-readable interpretation of trends"""
        category = analysis['category']
        country = analysis['country']
        trend = analysis['trend_direction']
        avg_days = analysis['average_advancement_days']
        volatility = analysis['volatility']
        
        base_msg = f"{category} for {country} "
        
        if trend == 'strongly_advancing':
            base_msg += f"is advancing rapidly, with an average of {avg_days:.0f} days per month."
        elif trend == 'advancing':
            base_msg += f"is advancing steadily at {avg_days:.0f} days per month."
        elif trend == 'strongly_retrogressing':
            base_msg += f"is retrogressing significantly, moving backward {abs(avg_days):.0f} days per month."
        elif trend == 'retrogressing':
            base_msg += f"is retrogressing at {abs(avg_days):.0f} days per month."
        elif trend == 'stable':
            base_msg += "shows minimal movement with stable priority dates."
        else:
            base_msg += "shows mixed movement patterns with no clear trend."
        
        if volatility == 'high':
            base_msg += " Movement is highly unpredictable."
        elif volatility == 'moderate':
            base_msg += " Movement shows moderate variability."
        else:
            base_msg += " Movement is relatively consistent."
        
        return base_msg
    
    def compare_categories(self, country: CountryCode, categories: List[VisaCategory] = None,
                          years_back: int = 2) -> Dict[str, Any]:
        """Compare advancement trends across categories for a specific country"""
        
        if categories is None:
            categories = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3]
        
        comparison = {
            'country': country.value,
            'categories': {},
            'rankings': {
                'fastest_advancing': [],
                'most_stable': [],
                'most_volatile': []
            }
        }
        
        category_scores = []
        
        for category in categories:
            logger.info(f"Analyzing {category.value} for comparison")
            
            trend_data = self.calculate_advancement_trends(category, country, years_back)
            
            if trend_data['status'] == 'success':
                comparison['categories'][category.value] = {
                    'average_advancement': trend_data['average_advancement_days'],
                    'trend_direction': trend_data['trend_direction'],
                    'volatility': trend_data['volatility'],
                    'consistency_score': trend_data['consistency_score'],
                    'data_points': trend_data['data_points']
                }
                
                category_scores.append({
                    'category': category.value,
                    'advancement': trend_data['average_advancement_days'],
                    'consistency': trend_data['consistency_score'],
                    'volatility_numeric': trend_data['std_deviation']
                })
        
        if category_scores:
            # Rank categories
            comparison['rankings']['fastest_advancing'] = sorted(
                category_scores, key=lambda x: x['advancement'], reverse=True
            )[:3]
            
            comparison['rankings']['most_stable'] = sorted(
                category_scores, key=lambda x: x['consistency'], reverse=True
            )[:3]
            
            comparison['rankings']['most_volatile'] = sorted(
                category_scores, key=lambda x: x['volatility_numeric'], reverse=True
            )[:3]
        
        return comparison
    
    def predict_next_movement(self, category: VisaCategory, country: CountryCode,
                            months_ahead: int = 3) -> Dict[str, Any]:
        """Predict likely movement for next few months"""
        
        trend_data = self.calculate_advancement_trends(category, country, years_back=3)
        
        if trend_data['status'] != 'success':
            return {
                'status': 'prediction_failed',
                'reason': trend_data.get('message', 'Insufficient data for prediction')
            }
        
        # Get recent advancement data
        recent_advancements = trend_data['monthly_advancements'][-6:]  # Last 6 months
        avg_advancement = trend_data['average_advancement_days']
        std_dev = trend_data['std_deviation']
        momentum = trend_data['momentum']
        
        # Simple prediction based on recent trends
        base_prediction = avg_advancement
        
        # Adjust for momentum
        if momentum.get('direction') == 'accelerating':
            base_prediction *= 1.2
        elif momentum.get('direction') == 'decelerating':
            base_prediction *= 0.8
        
        # Calculate prediction range
        margin_of_error = std_dev * 1.5  # 1.5 standard deviations
        
        predictions = []
        for month in range(1, months_ahead + 1):
            # Add some randomness based on historical volatility
            month_prediction = base_prediction
            
            predictions.append({
                'month': month,
                'predicted_advancement': round(month_prediction),
                'range_low': round(month_prediction - margin_of_error),
                'range_high': round(month_prediction + margin_of_error),
                'confidence': trend_data['prediction_confidence']['confidence']
            })
        
        return {
            'status': 'success',
            'category': category.value,
            'country': country.value,
            'predictions': predictions,
            'methodology': 'trend_analysis',
            'confidence': trend_data['prediction_confidence'],
            'disclaimer': 'Predictions are based on historical trends and should not be considered guaranteed outcomes.'
        }
    
    def generate_summary_report(self, categories: List[VisaCategory] = None,
                              countries: List[CountryCode] = None) -> Dict[str, Any]:
        """Generate a comprehensive summary report of all trends"""
        
        if categories is None:
            categories = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, VisaCategory.F1]
        
        if countries is None:
            countries = [CountryCode.INDIA, CountryCode.CHINA, CountryCode.WORLDWIDE]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'categories_analyzed': len(categories),
            'countries_analyzed': len(countries),
            'category_country_combinations': {},
            'overall_trends': {
                'most_active_categories': [],
                'most_active_countries': [],
                'general_observations': []
            }
        }
        
        all_trends = []
        
        for category in categories:
            for country in countries:
                combo_key = f"{category.value}_{country.value}"
                logger.info(f"Generating summary for {combo_key}")
                
                trend_data = self.calculate_advancement_trends(category, country, years_back=2)
                
                if trend_data['status'] == 'success':
                    report['category_country_combinations'][combo_key] = {
                        'category': category.value,
                        'country': country.value,
                        'trend_direction': trend_data['trend_direction'],
                        'average_advancement': trend_data['average_advancement_days'],
                        'volatility': trend_data['volatility'],
                        'data_quality': 'good' if trend_data['data_points'] >= 12 else 'limited'
                    }
                    
                    all_trends.append({
                        'combo': combo_key,
                        'category': category.value,
                        'country': country.value,
                        'advancement': trend_data['average_advancement_days'],
                        'trend': trend_data['trend_direction']
                    })
        
        # Generate overall insights
        if all_trends:
            # Most active categories
            category_activity = defaultdict(list)
            for trend in all_trends:
                category_activity[trend['category']].append(abs(trend['advancement']))
            
            category_avg_activity = {
                cat: sum(advs) / len(advs) for cat, advs in category_activity.items()
            }
            
            report['overall_trends']['most_active_categories'] = sorted(
                category_avg_activity.items(), key=lambda x: x[1], reverse=True
            )[:3]
            
            # General observations
            advancing_count = len([t for t in all_trends if 'advancing' in t['trend']])
            stable_count = len([t for t in all_trends if t['trend'] == 'stable'])
            retrogressing_count = len([t for t in all_trends if 'retrogressing' in t['trend']])
            
            report['overall_trends']['general_observations'] = [
                f"{advancing_count} category-country combinations are advancing",
                f"{stable_count} combinations are stable",
                f"{retrogressing_count} combinations are retrogressing"
            ]
        
        return report