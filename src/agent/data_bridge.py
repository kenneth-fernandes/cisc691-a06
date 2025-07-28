"""
Data Bridge Layer for Agent-to-Analytics Integration

This module provides the bridge between the AI agent and visa analytics system,
handling data access, context injection, and fallback mechanisms.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date

from visa.analytics import TrendAnalyzer
from visa.models import VisaCategory, CountryCode
from visa.repository import VisaBulletinRepository

logger = logging.getLogger(__name__)


class VisaDataBridge:
    """Bridge class that provides data access layer for agent queries"""
    
    def __init__(self):
        """Initialize the data bridge with analytics components"""
        try:
            # VisaBulletinRepository will automatically detect Docker environment
            # and use PostgreSQL when DATABASE_URL is set
            self.repository = VisaBulletinRepository()
            self.analyzer = TrendAnalyzer(self.repository)
            self.database = self.repository.db  # Access the underlying database
            self.is_available = True
            logger.info("Visa data bridge initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize visa data bridge: {e}")
            self.is_available = False
    
    def check_data_availability(self) -> Dict[str, Any]:
        """Check if visa data is available and get basic statistics"""
        if not self.is_available:
            return {
                'status': 'unavailable',
                'message': 'Visa data system is not available'
            }
        
        try:
            # Get basic database statistics
            stats = self.database.get_database_stats()
            
            return {
                'status': 'available',
                'total_bulletins': stats.get('bulletin_count', 0),
                'date_range': stats.get('year_range', 'Unknown'),
                'categories_available': ['EB-1', 'EB-2', 'EB-3', 'EB-4', 'EB-5', 'F1', 'F2A', 'F2B', 'F3', 'F4'],
                'countries_available': ['INDIA', 'CHINA', 'MEXICO', 'PHILIPPINES', 'WORLDWIDE']
            }
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return {
                'status': 'error',
                'message': f'Error accessing data: {str(e)}'
            }
    
    def extract_visa_context(self, user_query: str) -> Dict[str, Any]:
        """Extract visa-related context from user query"""
        query_lower = user_query.lower()
        context = {
            'is_visa_related': False,
            'categories': [],
            'countries': [],
            'query_type': 'general',
            'keywords': []
        }
        
        # Check if query is visa-related
        visa_keywords = [
            'visa', 'bulletin', 'priority date', 'advancement', 'retrogression',
            'eb-1', 'eb-2', 'eb-3', 'eb-4', 'eb-5', 'eb1', 'eb2', 'eb3', 'eb4', 'eb5',
            'f1', 'f2a', 'f2b', 'f3', 'f4', 'family', 'employment',
            'india', 'china', 'mexico', 'philippines', 'worldwide',
            'trend', 'prediction', 'forecast', 'movement', 'advance'
        ]
        
        found_keywords = [kw for kw in visa_keywords if kw in query_lower]
        if found_keywords:
            context['is_visa_related'] = True
            context['keywords'] = found_keywords
        
        # Extract categories
        category_patterns = {
            'eb-1': VisaCategory.EB1, 'eb1': VisaCategory.EB1,
            'eb-2': VisaCategory.EB2, 'eb2': VisaCategory.EB2,
            'eb-3': VisaCategory.EB3, 'eb3': VisaCategory.EB3,
            'eb-4': VisaCategory.EB4, 'eb4': VisaCategory.EB4,
            'eb-5': VisaCategory.EB5, 'eb5': VisaCategory.EB5,
            'f1': VisaCategory.F1, 'f2a': VisaCategory.F2A,
            'f2b': VisaCategory.F2B, 'f3': VisaCategory.F3, 'f4': VisaCategory.F4
        }
        
        for pattern, category in category_patterns.items():
            if pattern in query_lower:
                context['categories'].append(category.value)
        
        # Extract countries
        country_patterns = {
            'india': CountryCode.INDIA, 'indian': CountryCode.INDIA,
            'china': CountryCode.CHINA, 'chinese': CountryCode.CHINA,
            'mexico': CountryCode.MEXICO, 'mexican': CountryCode.MEXICO,
            'philippines': CountryCode.PHILIPPINES, 'filipino': CountryCode.PHILIPPINES,
            'worldwide': CountryCode.WORLDWIDE, 'row': CountryCode.WORLDWIDE,
            'others': CountryCode.WORLDWIDE
        }
        
        for pattern, country in country_patterns.items():
            if pattern in query_lower:
                context['countries'].append(country.value)
        
        # Determine query type
        if any(word in query_lower for word in ['trend', 'trending', 'analysis', 'pattern']):
            context['query_type'] = 'trend_analysis'
        elif any(word in query_lower for word in ['predict', 'forecast', 'future', 'next', 'when']):
            context['query_type'] = 'prediction'
        elif any(word in query_lower for word in ['compare', 'comparison', 'versus', 'vs', 'rank']):
            context['query_type'] = 'comparison'
        elif any(word in query_lower for word in ['summary', 'overview', 'report', 'all']):
            context['query_type'] = 'summary'
        elif any(word in query_lower for word in ['explain', 'status', 'current', 'what']):
            context['query_type'] = 'explanation'
        
        return context
    
    def get_relevant_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant data based on extracted context"""
        if not self.is_available or not context['is_visa_related']:
            return {'status': 'not_applicable'}
        
        try:
            data = {'status': 'success', 'context_data': {}}
            
            # Get data based on query type and context
            if context['query_type'] == 'trend_analysis' and context['categories'] and context['countries']:
                # Get trend data for specific category-country combination
                category = context['categories'][0]
                country = context['countries'][0]
                
                try:
                    category_enum = VisaCategory(category.replace('-', ''))
                    country_enum = CountryCode(country.upper())
                    
                    trend_data = self.analyzer.calculate_advancement_trends(
                        category_enum, country_enum, years_back=3
                    )
                    data['context_data']['trend_analysis'] = trend_data
                except ValueError as e:
                    logger.warning(f"Invalid category/country combination: {e}")
            
            elif context['query_type'] == 'comparison' and context['countries']:
                # Get comparison data for country
                country = context['countries'][0]
                try:
                    country_enum = CountryCode(country.upper())
                    comparison_data = self.analyzer.compare_categories(country_enum)
                    data['context_data']['category_comparison'] = comparison_data
                except ValueError as e:
                    logger.warning(f"Invalid country for comparison: {e}")
            
            elif context['query_type'] == 'summary':
                # Get summary report
                summary_data = self.analyzer.generate_summary_report()
                data['context_data']['summary_report'] = summary_data
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting relevant data: {e}")
            return {
                'status': 'error',
                'message': f'Error retrieving data: {str(e)}'
            }
    
    def inject_data_context(self, user_query: str, base_prompt: str) -> str:
        """Inject relevant data context into the agent prompt"""
        if not self.is_available:
            return base_prompt
        
        try:
            # Extract context from user query
            context = self.extract_visa_context(user_query)
            
            if not context['is_visa_related']:
                return base_prompt
            
            # Get relevant data
            data_result = self.get_relevant_data(context)
            
            if data_result['status'] != 'success':
                return base_prompt
            
            # Build data context injection
            data_context = "\n\n=== RELEVANT VISA DATA ===\n"
            
            context_data = data_result['context_data']
            
            if 'trend_analysis' in context_data:
                trend = context_data['trend_analysis']
                if trend['status'] == 'success':
                    data_context += f"**Current Trend Data for {trend['category']}-{trend['country']}:**\n"
                    data_context += f"- Average advancement: {trend['average_advancement_days']:.1f} days/month\n"
                    data_context += f"- Trend direction: {trend['trend_direction']}\n"
                    data_context += f"- Volatility: {trend['volatility']}\n"
                    data_context += f"- Data points: {trend['data_points']} bulletins\n"
                    data_context += f"- Interpretation: {trend['interpretation']}\n"
            
            if 'category_comparison' in context_data:
                comparison = context_data['category_comparison']
                data_context += f"**Category Comparison for {comparison['country']}:**\n"
                for cat, data in comparison['categories'].items():
                    data_context += f"- {cat}: {data['average_advancement']:.1f} days/month, {data['trend_direction']}\n"
            
            if 'summary_report' in context_data:
                summary = context_data['summary_report']
                data_context += f"**Market Summary:**\n"
                for obs in summary['overall_trends']['general_observations']:
                    data_context += f"- {obs}\n"
            
            data_context += "=== END VISA DATA ===\n\n"
            
            # Inject before the user query
            enhanced_prompt = base_prompt + data_context
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error injecting data context: {e}")
            return base_prompt
    
    def handle_data_unavailable_scenario(self, user_query: str) -> Optional[str]:
        """Handle scenarios where data is unavailable"""
        context = self.extract_visa_context(user_query)
        
        if not context['is_visa_related']:
            return None
        
        if not self.is_available:
            return """I apologize, but I'm currently unable to access the historical visa bulletin data system. 
            I can still provide general guidance about visa categories and processes based on my knowledge, 
            but I cannot provide current trend analysis or data-driven predictions. 
            
            Please try again later or contact support if this issue persists."""
        
        availability = self.check_data_availability()
        
        if availability['status'] != 'available':
            return f"""I'm having trouble accessing the visa data at the moment: {availability.get('message', 'Unknown error')}
            
            I can still help with general visa information and guidance. Would you like me to provide 
            general information about visa categories or processes instead?"""
        
        return None
    
    def get_data_summary_for_context(self) -> str:
        """Get a brief summary of available data for context setting"""
        if not self.is_available:
            return "Visa data system is currently unavailable."
        
        try:
            availability = self.check_data_availability()
            
            if availability['status'] == 'available':
                total_bulletins = availability.get('total_bulletins', 0)
                date_range = availability.get('date_range', 'unknown')
                
                summary = f"I have access to {total_bulletins} visa bulletins"
                if date_range and date_range != 'unknown':
                    summary += f" spanning from {date_range}"
                
                summary += ". I can provide trend analysis, predictions, and comparisons for all visa categories and countries."
                return summary
            else:
                return "Visa data system is temporarily unavailable."
                
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return "Unable to access visa data summary."


# Global instance for easy access
_visa_data_bridge = None


def get_visa_data_bridge() -> VisaDataBridge:
    """Get the global visa data bridge instance"""
    global _visa_data_bridge
    if _visa_data_bridge is None:
        _visa_data_bridge = VisaDataBridge()
    return _visa_data_bridge