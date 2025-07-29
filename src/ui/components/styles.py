"""
Styling utilities and CSS for visa prediction UI components
"""

import streamlit as st


def load_custom_css():
    """Load custom CSS styles for visa prediction components"""
    st.markdown("""
    <style>
    /* Visa Prediction UI Styles */
    
    /* Main container styling */
    .visa-prediction-container {
        padding: 1rem;
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.2em;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b415;
    }
    
    /* Prediction result cards */
    .prediction-card {
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: transform 0.2s ease-in-out;
    }
    
    .prediction-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .prediction-advancement {
        background: linear-gradient(135deg, #28a74515, #28a74525);
        border-left: 4px solid #28a745;
    }
    
    .prediction-retrogression {
        background: linear-gradient(135deg, #dc354515, #dc354525);
        border-left: 4px solid #dc3545;
    }
    
    .prediction-stable {
        background: linear-gradient(135deg, #ffc10715, #ffc10725);
        border-left: 4px solid #ffc107;
    }
    
    /* Category selector styling */
    .category-selector {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .category-badge {
        display: inline-block;
        background-color: #1f77b4;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .country-badge {
        display: inline-block;
        background-color: #17a2b8;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    /* Confidence indicators */
    .confidence-high {
        color: #28a745;
        font-weight: 600;
    }
    
    .confidence-medium {
        color: #ffc107;
        font-weight: 600;
    }
    
    .confidence-low {
        color: #dc3545;
        font-weight: 600;
    }
    
    /* Trend indicators */
    .trend-advancing {
        color: #28a745;
        font-size: 1.2em;
    }
    
    .trend-retrogressing {
        color: #dc3545;
        font-size: 1.2em;
    }
    
    .trend-stable {
        color: #ffc107;
        font-size: 1.2em;
    }
    
    /* Historical chart container */
    .chart-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Comparison table styling */
    .comparison-table {
        background-color: #f8f9fa;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .comparison-table th {
        background-color: #1f77b4;
        color: white;
        font-weight: 600;
        padding: 0.75rem;
    }
    
    .comparison-table td {
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid #dee2e6;
    }
    
    /* Status indicators */
    .status-current {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 500;
    }
    
    .status-unavailable {
        background-color: #6c757d;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 500;
    }
    
    .status-date {
        background-color: #17a2b8;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 500;
    }
    
    /* Loading indicators */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #1f77b4;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Alert styling */
    .alert-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 0.75rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .prediction-card {
            margin: 0.25rem 0;
            padding: 0.75rem;
        }
        
        .category-selector {
            padding: 0.75rem;
        }
        
        .section-header {
            font-size: 1.1em;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .visa-prediction-container {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        .category-selector {
            background-color: #3b3b3b;
        }
        
        .chart-container {
            background-color: #2b2b2b;
        }
        
        .comparison-table {
            background-color: #3b3b3b;
        }
        
        .comparison-table td {
            border-bottom-color: #555555;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def get_prediction_color(prediction_type: str) -> str:
    """Get color for prediction type"""
    colors = {
        "advancement": "#28a745",
        "retrogression": "#dc3545", 
        "stable": "#ffc107",
        "current": "#17a2b8",
        "unavailable": "#6c757d",
        "insufficient_data": "#fd7e14",
        "no_features": "#6f42c1"
    }
    return colors.get(prediction_type, "#007bff")


def get_confidence_class(confidence_score: float) -> str:
    """Get CSS class for confidence level"""
    if confidence_score >= 0.7:
        return "confidence-high"
    elif confidence_score >= 0.4:
        return "confidence-medium"
    else:
        return "confidence-low"


def get_trend_class(trend_direction: str) -> str:
    """Get CSS class for trend direction"""
    classes = {
        "advancing": "trend-advancing",
        "retrogressing": "trend-retrogressing", 
        "stable": "trend-stable"
    }
    return classes.get(trend_direction, "")


def render_styled_metric(label: str, value: str, delta: str = None, 
                        help_text: str = None, icon: str = "📊") -> None:
    """Render a styled metric with custom formatting"""
    delta_html = f"<small style='color: #666;'>{delta}</small>" if delta else ""
    help_html = f"<span title='{help_text}'>ℹ️</span>" if help_text else ""
    
    st.markdown(f"""
    <div style='background-color: #f8f9fa; 
                border-radius: 8px; 
                padding: 1rem; 
                text-align: center; 
                margin: 0.5rem 0;'>
        <div style='font-size: 1.5em; margin-bottom: 0.5rem;'>{icon}</div>
        <div style='font-size: 0.9em; color: #666; margin-bottom: 0.25rem;'>
            {label} {help_html}
        </div>
        <div style='font-size: 1.4em; font-weight: 600; color: #1f77b4;'>
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Render a status badge with appropriate styling"""
    status_lower = status.lower()
    if status_lower == 'current' or status_lower == 'c':
        return "<span class='status-current'>CURRENT</span>"
    elif status_lower == 'unavailable' or status_lower == 'u':
        return "<span class='status-unavailable'>UNAVAILABLE</span>"
    else:
        return "<span class='status-date'>DATE</span>"