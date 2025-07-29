"""
UI Components for Visa Prediction System
"""

from .sidebar import render_sidebar
from .visa_selector import render_visa_selector, render_country_filter, render_category_filter
from .prediction_display import (
    render_prediction_results, 
    render_trend_analysis, 
    render_historical_chart,
    render_comparison_chart
)
from .styles import load_custom_css, get_prediction_color, get_confidence_class

__all__ = [
    'render_sidebar',
    'render_visa_selector', 
    'render_country_filter',
    'render_category_filter',
    'render_prediction_results',
    'render_trend_analysis', 
    'render_historical_chart',
    'render_comparison_chart',
    'load_custom_css',
    'get_prediction_color',
    'get_confidence_class'
]