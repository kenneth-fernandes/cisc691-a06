"""
LangChain Tools for Visa Analytics Data Access

This module provides LangChain Tool objects that bridge the AI agent with the analytics system,
allowing the agent to access real historical visa data and analytics in responses.
"""

import json
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from visa.analytics import TrendAnalyzer
from visa.models import VisaCategory, CountryCode
from visa.repository import VisaBulletinRepository


class TrendAnalysisInput(BaseModel):
    """Input schema for trend analysis tool"""
    category: str = Field(description="Visa category (e.g., 'EB-1', 'EB-2', 'EB-3', 'F1', 'F2A')")
    country: str = Field(description="Country code (e.g., 'INDIA', 'CHINA', 'WORLDWIDE', 'MEXICO', 'PHILIPPINES')")
    years_back: int = Field(default=3, description="Number of years to analyze (default: 3)")


class CategoryComparisonInput(BaseModel):
    """Input schema for category comparison tool"""
    country: str = Field(description="Country code to compare categories for")
    categories: Optional[List[str]] = Field(
        default=None, 
        description="List of categories to compare (default: ['EB-1', 'EB-2', 'EB-3'])"
    )
    years_back: int = Field(default=2, description="Number of years to analyze (default: 2)")


class MovementPredictionInput(BaseModel):
    """Input schema for movement prediction tool"""
    category: str = Field(description="Visa category (e.g., 'EB-1', 'EB-2', 'EB-3', 'F1', 'F2A')")
    country: str = Field(description="Country code (e.g., 'INDIA', 'CHINA', 'WORLDWIDE', 'MEXICO', 'PHILIPPINES')")
    months_ahead: int = Field(default=3, description="Number of months to predict (default: 3)")


class SummaryReportInput(BaseModel):
    """Input schema for summary report tool"""
    categories: Optional[List[str]] = Field(
        default=None,
        description="Categories to include in report (default: ['EB-1', 'EB-2', 'EB-3', 'F1'])"
    )
    countries: Optional[List[str]] = Field(
        default=None,
        description="Countries to include in report (default: ['INDIA', 'CHINA', 'WORLDWIDE'])"
    )


class VisaTrendAnalysisTool(BaseTool):
    """Tool for analyzing visa bulletin trends for a specific category and country"""
    
    name: str = "visa_trend_analysis"
    description: str = """
    Analyzes historical visa bulletin trends for a specific category and country combination.
    Provides detailed statistics including average advancement, trend direction, volatility,
    and momentum analysis. Use this when users ask about how a category is trending or
    performing historically.
    
    Examples of when to use:
    - "How is EB-2 India trending?"
    - "What's the advancement pattern for EB-1 China?"
    - "Show me the volatility of F1 category"
    """
    args_schema: Type[BaseModel] = TrendAnalysisInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        category: str,
        country: str,
        years_back: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the trend analysis"""
        try:
            # Initialize components
            repository = VisaBulletinRepository()
            analyzer = TrendAnalyzer(repository)
            
            # Normalize inputs
            category_enum = self._normalize_category(category)
            country_enum = self._normalize_country(country)
            
            # Perform analysis
            result = analyzer.calculate_advancement_trends(
                category_enum, country_enum, years_back
            )
            
            # Format result for agent consumption
            return self._format_trend_result(result)
            
        except Exception as e:
            return f"Error analyzing trends for {category}-{country}: {str(e)}"
    
    def _normalize_category(self, category: str) -> VisaCategory:
        """Normalize category string to VisaCategory enum"""
        category_upper = category.upper().replace('-', '').replace('_', '')
        
        # Handle common variations
        category_map = {
            'EB1': VisaCategory.EB1,
            'EB2': VisaCategory.EB2,
            'EB3': VisaCategory.EB3,
            'EB4': VisaCategory.EB4,
            'EB5': VisaCategory.EB5,
            'F1': VisaCategory.F1,
            'F2A': VisaCategory.F2A,
            'F2B': VisaCategory.F2B,
            'F3': VisaCategory.F3,
            'F4': VisaCategory.F4,
        }
        
        if category_upper in category_map:
            return category_map[category_upper]
        else:
            raise ValueError(f"Unknown category: {category}")
    
    def _normalize_country(self, country: str) -> CountryCode:
        """Normalize country string to CountryCode enum"""
        country_upper = country.upper()
        
        # Handle common variations
        country_map = {
            'INDIA': CountryCode.INDIA,
            'IN': CountryCode.INDIA,
            'CHINA': CountryCode.CHINA,
            'CN': CountryCode.CHINA,
            'MEXICO': CountryCode.MEXICO,
            'MX': CountryCode.MEXICO,
            'PHILIPPINES': CountryCode.PHILIPPINES,
            'PH': CountryCode.PHILIPPINES,
            'WORLDWIDE': CountryCode.WORLDWIDE,
            'ROW': CountryCode.WORLDWIDE,
            'OTHERS': CountryCode.WORLDWIDE,
        }
        
        if country_upper in country_map:
            return country_map[country_upper]
        else:
            raise ValueError(f"Unknown country: {country}")
    
    def _format_trend_result(self, result: Dict[str, Any]) -> str:
        """Format trend analysis result for agent consumption"""
        if result['status'] != 'success':
            return f"Analysis failed: {result.get('message', 'Unknown error')}"
        
        # Extract key information
        category = result['category']
        country = result['country']
        avg_advancement = result['average_advancement_days']
        trend_direction = result['trend_direction']
        volatility = result['volatility']
        data_points = result['data_points']
        interpretation = result['interpretation']
        
        # Get additional insights
        momentum = result.get('momentum', {})
        confidence = result.get('prediction_confidence', {})
        seasonal = result.get('seasonal_pattern', {})
        
        # Create comprehensive response
        response = f"""**Trend Analysis for {category} - {country}**

**Overall Assessment**: {interpretation}

**Key Metrics**:
- Average monthly advancement: {avg_advancement:.1f} days
- Trend direction: {trend_direction.replace('_', ' ').title()}
- Volatility: {volatility.title()}
- Data points analyzed: {data_points} bulletins
- Analysis confidence: {confidence.get('confidence', 'Unknown').title()} ({confidence.get('score', 0):.0f}%)

**Detailed Insights**:
- Total advancement: {result['total_advancement_days']} days over analysis period
- Positive months: {result['positive_months']}, Negative: {result['negative_months']}, Stable: {result['stagnant_months']}
- Consistency score: {result['consistency_score']:.1f}/100"""

        # Add momentum information
        if momentum.get('status') != 'insufficient_data':
            direction = momentum.get('direction', 'stable')
            response += f"\n- Recent momentum: {direction.title()}"
        
        # Add seasonal insights
        if seasonal.get('status') == 'detected':
            best_month = seasonal.get('best_month')
            worst_month = seasonal.get('worst_month')
            response += f"\n- Best historical month: {best_month}, Worst: {worst_month}"
        
        # Add percentile information
        percentiles = result.get('percentiles', {})
        if percentiles:
            response += f"\n\n**Movement Range**:"
            response += f"\n- 25th percentile: {percentiles.get('25th', 0):.0f} days"
            response += f"\n- Median (50th): {percentiles.get('50th', 0):.0f} days"
            response += f"\n- 75th percentile: {percentiles.get('75th', 0):.0f} days"
        
        return response


class VisaCategoryComparisonTool(BaseTool):
    """Tool for comparing visa advancement trends across categories for a specific country"""
    
    name: str = "visa_category_comparison"
    description: str = """
    Compares advancement trends across multiple visa categories for a specific country.
    Shows which categories are advancing fastest, most stable, or most volatile.
    Use this when users want to compare different categories for a country.
    
    Examples of when to use:
    - "Compare EB categories for India"
    - "Which family-based category is moving fastest for China?"
    - "Rank the categories by advancement speed"
    """
    args_schema: Type[BaseModel] = CategoryComparisonInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        country: str,
        categories: Optional[List[str]] = None,
        years_back: int = 2,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the category comparison"""
        try:
            # Initialize components
            repository = VisaBulletinRepository()
            analyzer = TrendAnalyzer(repository)
            trend_tool = VisaTrendAnalysisTool()
            
            # Normalize inputs
            country_enum = trend_tool._normalize_country(country)
            
            if categories:
                category_enums = [trend_tool._normalize_category(cat) for cat in categories]
            else:
                category_enums = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3]
            
            # Perform comparison
            result = analyzer.compare_categories(country_enum, category_enums, years_back)
            
            # Format result
            return self._format_comparison_result(result)
            
        except Exception as e:
            return f"Error comparing categories for {country}: {str(e)}"
    
    def _format_comparison_result(self, result: Dict[str, Any]) -> str:
        """Format comparison result for agent consumption"""
        country = result['country']
        categories = result['categories']
        rankings = result['rankings']
        
        if not categories:
            return f"No data available for category comparison in {country}"
        
        response = f"**Category Comparison for {country}**\n\n"
        
        # Overall category performance
        response += "**Individual Category Performance**:\n"
        for cat_name, data in categories.items():
            avg_adv = data['average_advancement']
            trend = data['trend_direction'].replace('_', ' ').title()
            volatility = data['volatility'].title()
            response += f"- **{cat_name}**: {avg_adv:.1f} days/month, {trend}, {volatility} volatility\n"
        
        # Rankings
        if rankings['fastest_advancing']:
            response += "\n**🚀 Fastest Advancing Categories**:\n"
            for i, cat in enumerate(rankings['fastest_advancing'][:3], 1):
                response += f"{i}. {cat['category']}: {cat['advancement']:.1f} days/month\n"
        
        if rankings['most_stable']:
            response += "\n**📊 Most Consistent Categories**:\n"
            for i, cat in enumerate(rankings['most_stable'][:3], 1):
                response += f"{i}. {cat['category']}: {cat['consistency']:.1f}% consistency\n"
        
        if rankings['most_volatile']:
            response += "\n**⚡ Most Volatile Categories**:\n"
            for i, cat in enumerate(rankings['most_volatile'][:3], 1):
                response += f"{i}. {cat['category']}: {cat['volatility_numeric']:.1f} std deviation\n"
        
        return response


class VisaMovementPredictionTool(BaseTool):
    """Tool for predicting future visa bulletin movements"""
    
    name: str = "visa_movement_prediction"
    description: str = """
    Predicts likely visa bulletin movements for the next few months based on historical trends.
    Provides prediction ranges and confidence levels. Use this when users ask about
    future movements or predictions.
    
    Examples of when to use:
    - "When will EB-2 India move next?"
    - "Predict EB-1 China movement for next 3 months"
    - "What's the forecast for F1 category?"
    """
    args_schema: Type[BaseModel] = MovementPredictionInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        category: str,
        country: str,
        months_ahead: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the movement prediction"""
        try:
            # Initialize components
            repository = VisaBulletinRepository()
            analyzer = TrendAnalyzer(repository)
            trend_tool = VisaTrendAnalysisTool()
            
            # Normalize inputs
            category_enum = trend_tool._normalize_category(category)
            country_enum = trend_tool._normalize_country(country)
            
            # Perform prediction
            result = analyzer.predict_next_movement(
                category_enum, country_enum, months_ahead
            )
            
            # Format result
            return self._format_prediction_result(result)
            
        except Exception as e:
            return f"Error predicting movement for {category}-{country}: {str(e)}"
    
    def _format_prediction_result(self, result: Dict[str, Any]) -> str:
        """Format prediction result for agent consumption"""
        if result['status'] != 'success':
            return f"Prediction failed: {result.get('reason', 'Unknown error')}"
        
        category = result['category']
        country = result['country']
        predictions = result['predictions']
        confidence = result['confidence']
        
        response = f"**Movement Prediction for {category} - {country}**\n\n"
        response += f"**Prediction Confidence**: {confidence['confidence'].title()} ({confidence['score']:.0f}%)\n\n"
        
        response += "**Monthly Predictions**:\n"
        for pred in predictions:
            month = pred['month']
            predicted = pred['predicted_advancement']
            range_low = pred['range_low']
            range_high = pred['range_high']
            
            if predicted > 0:
                direction = "advance"
            elif predicted < 0:
                direction = "retrogress"
            else:
                direction = "remain stable"
            
            response += f"Month {month}: Expected to {direction} by {abs(predicted)} days "
            response += f"(Range: {range_low} to {range_high} days)\n"
        
        response += f"\n**Methodology**: {result['methodology'].replace('_', ' ').title()}"
        response += f"\n\n**Disclaimer**: {result['disclaimer']}"
        
        return response


class VisaSummaryReportTool(BaseTool):
    """Tool for generating comprehensive visa trend summary reports"""
    
    name: str = "visa_summary_report"
    description: str = """
    Generates a comprehensive summary report of visa trends across multiple categories
    and countries. Provides overall market insights and comparative analysis.
    Use this for broad overviews and market summaries.
    
    Examples of when to use:
    - "Give me an overview of all visa categories"
    - "What's the overall market summary?"
    - "Compare all categories and countries"
    """
    args_schema: Type[BaseModel] = SummaryReportInput
    
    def __init__(self):
        super().__init__()
    
    def _run(
        self,
        categories: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the summary report generation"""
        try:
            # Initialize components
            repository = VisaBulletinRepository()
            analyzer = TrendAnalyzer(repository)
            trend_tool = VisaTrendAnalysisTool()
            
            # Normalize inputs
            if categories:
                category_enums = [trend_tool._normalize_category(cat) for cat in categories]
            else:
                category_enums = None
            
            if countries:
                country_enums = [trend_tool._normalize_country(country) for country in countries]
            else:
                country_enums = None
            
            # Generate report
            result = analyzer.generate_summary_report(category_enums, country_enums)
            
            # Format result
            return self._format_summary_result(result)
            
        except Exception as e:
            return f"Error generating summary report: {str(e)}"
    
    def _format_summary_result(self, result: Dict[str, Any]) -> str:
        """Format summary report for agent consumption"""
        response = "**Comprehensive Visa Bulletin Summary Report**\n\n"
        
        # Report metadata
        categories_count = result['categories_analyzed']
        countries_count = result['countries_analyzed']
        generated_at = result['generated_at'][:19]  # Remove microseconds
        
        response += f"**Report Details**:\n"
        response += f"- Generated: {generated_at}\n"
        response += f"- Categories analyzed: {categories_count}\n"
        response += f"- Countries analyzed: {countries_count}\n\n"
        
        # Overall trends
        overall = result['overall_trends']
        observations = overall.get('general_observations', [])
        
        if observations:
            response += "**Market Overview**:\n"
            for obs in observations:
                response += f"- {obs}\n"
            response += "\n"
        
        # Most active categories
        active_categories = overall.get('most_active_categories', [])
        if active_categories:
            response += "**Most Active Categories** (by average advancement):\n"
            for i, (cat, activity) in enumerate(active_categories, 1):
                response += f"{i}. {cat}: {activity:.1f} days average movement\n"
            response += "\n"
        
        # Category-country combinations
        combinations = result['category_country_combinations']
        if combinations:
            response += "**Category-Country Performance Summary**:\n"
            
            # Group by trend direction
            advancing = []
            stable = []
            retrogressing = []
            
            for combo_key, data in combinations.items():
                category = data['category']
                country = data['country']
                trend = data['trend_direction']
                avg_adv = data['average_advancement']
                
                combo_str = f"{category}-{country}: {avg_adv:.1f} days/month"
                
                if 'advancing' in trend:
                    advancing.append(combo_str)
                elif 'retrogressing' in trend:
                    retrogressing.append(combo_str)
                else:
                    stable.append(combo_str)
            
            if advancing:
                response += "\n**🚀 Advancing Categories**:\n"
                for combo in advancing[:5]:  # Top 5
                    response += f"- {combo}\n"
            
            if stable:
                response += "\n**📊 Stable Categories**:\n"
                for combo in stable[:3]:  # Top 3
                    response += f"- {combo}\n"
            
            if retrogressing:
                response += "\n**📉 Retrogressing Categories**:\n"
                for combo in retrogressing[:3]:  # Top 3
                    response += f"- {combo}\n"
        
        return response


def get_visa_analytics_tools() -> List[BaseTool]:
    """Get all visa analytics tools for LangChain agent integration"""
    return [
        VisaTrendAnalysisTool(),
        VisaCategoryComparisonTool(),
        VisaMovementPredictionTool(),
        VisaSummaryReportTool()
    ]