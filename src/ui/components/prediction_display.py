"""
Prediction results display component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import pandas as pd

from visa.models import VisaCategory, CountryCode, PredictionResult, TrendAnalysis, CategoryData
from visa.predictor import create_predictor, TrendAnalyzer
from visa.database import VisaDatabase


def render_prediction_results(prediction: PredictionResult) -> None:
    """
    Render prediction results with visual indicators
    
    Args:
        prediction: PredictionResult object containing prediction data
    """
    if not prediction:
        st.warning("⚠️ No prediction data available")
        return
    
    st.markdown(
        "<h3 style='margin-bottom: 1rem;'>🔮 Prediction Results</h3>",
        unsafe_allow_html=True,
    )
    
    # Main prediction card
    prediction_icon = {
        "advancement": "📈",
        "retrogression": "📉", 
        "stable": "➡️",
        "current": "✅",
        "unavailable": "❌",
        "insufficient_data": "⚠️",
        "no_features": "❓"
    }.get(prediction.prediction_type, "🔮")
    
    prediction_color = {
        "advancement": "#28a745",
        "retrogression": "#dc3545",
        "stable": "#ffc107", 
        "current": "#17a2b8",
        "unavailable": "#6c757d",
        "insufficient_data": "#fd7e14",
        "no_features": "#6f42c1"
    }.get(prediction.prediction_type, "#007bff")
    
    st.markdown(
        f"""
        <div style='background-color: {prediction_color}15; 
                    border: 2px solid {prediction_color}; 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin: 15px 0;
                    text-align: center;'>
            <h2 style='margin: 0; color: {prediction_color};'>
                {prediction_icon} {prediction.prediction_type.replace('_', ' ').title()}
            </h2>
            <hr style='margin: 10px 0; border-color: {prediction_color}50;'>
            <p style='font-size: 1.1em; margin: 10px 0;'>
                <strong>Category:</strong> {prediction.category.value} | 
                <strong>Country:</strong> {prediction.country.value}
            </p>
            <p style='font-size: 1.1em; margin: 10px 0;'>
                <strong>Target:</strong> {prediction.target_month:02d}/{prediction.target_year}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Prediction details in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📅 Predicted Date", 
            value=prediction.predicted_date.strftime("%m/%d/%Y") if prediction.predicted_date else "N/A"
        )
    
    with col2:
        confidence_percentage = int(prediction.confidence_score * 100)
        confidence_color = "🟢" if confidence_percentage >= 70 else "🟡" if confidence_percentage >= 40 else "🔴"
        st.metric(
            label=f"{confidence_color} Confidence",
            value=f"{confidence_percentage}%"
        )
    
    with col3:
        st.metric(
            label="🤖 Model Version",
            value=prediction.model_version
        )
    
    # Additional details in expander
    with st.expander("📊 Detailed Information"):
        st.write(f"**Prediction Type:** {prediction.prediction_type}")
        st.write(f"**Generated:** {prediction.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if prediction.predicted_date:
            days_from_now = (prediction.predicted_date - date.today()).days
            if days_from_now > 0:
                st.write(f"**Days from today:** {days_from_now} days")
            elif days_from_now < 0:
                st.write(f"**Date was:** {abs(days_from_now)} days ago")
            else:
                st.write("**Date is:** Today")


def render_trend_analysis(trend: TrendAnalysis) -> None:
    """
    Render trend analysis with visualizations
    
    Args:
        trend: TrendAnalysis object containing trend data
    """
    if not trend:
        st.warning("⚠️ No trend analysis available")
        return
        
    st.markdown(
        "<h3 style='margin-bottom: 1rem;'>📈 Trend Analysis</h3>",
        unsafe_allow_html=True,
    )
    
    # Trend direction indicator
    trend_icon = {
        "advancing": "📈",
        "retrogressing": "📉",
        "stable": "➡️"
    }.get(trend.trend_direction, "📊")
    
    trend_color = {
        "advancing": "#28a745",
        "retrogressing": "#dc3545", 
        "stable": "#ffc107"
    }.get(trend.trend_direction, "#007bff")
    
    st.markdown(
        f"""
        <div style='background-color: {trend_color}15; 
                    border: 1px solid {trend_color}; 
                    border-radius: 8px; 
                    padding: 15px; 
                    margin: 10px 0;'>
            <h4 style='margin: 0 0 10px 0; color: {trend_color};'>
                {trend_icon} {trend.trend_direction.title()} Trend
            </h4>
            <p style='margin: 5px 0;'>
                <strong>Category:</strong> {trend.category.value} | 
                <strong>Country:</strong> {trend.country.value}
            </p>
            <p style='margin: 5px 0;'>
                <strong>Analysis Period:</strong> {trend.start_date} to {trend.end_date}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Movement",
            value=f"{trend.total_advancement_days} days"
        )
    
    with col2:
        st.metric(
            label="📅 Monthly Average", 
            value=f"{trend.average_monthly_advancement:.1f} days",
            delta=f"{trend.average_monthly_advancement:.1f}"
        )
    
    with col3:
        volatility_level = "High" if trend.volatility_score > 20 else "Medium" if trend.volatility_score > 10 else "Low"
        st.metric(
            label="🌊 Volatility",
            value=volatility_level,
            help=f"Score: {trend.volatility_score:.2f}"
        )
    
    with col4:
        period_days = (trend.end_date - trend.start_date).days
        st.metric(
            label="⏰ Period",
            value=f"{period_days} days"
        )


def render_historical_chart(history: List[CategoryData], category: VisaCategory, country: CountryCode) -> None:
    """
    Render historical progression chart
    
    Args:
        history: List of CategoryData objects
        category: Visa category
        country: Country code
    """
    if not history:
        st.warning("⚠️ No historical data available")
        return
    
    st.markdown(
        "<h3 style='margin-bottom: 1rem;'>📊 Historical Progression</h3>",
        unsafe_allow_html=True,
    )
    
    # Filter valid dates
    valid_data = [
        {
            "index": i,
            "date": cat.final_action_date,
            "status": cat.status.value if cat.status else "Unknown"
        }
        for i, cat in enumerate(history)
        if cat.final_action_date
    ]
    
    if not valid_data:
        st.info("📝 No date progression data available for visualization")
        return
    
    # Create DataFrame for plotting
    df = pd.DataFrame(valid_data)
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['date'],
        mode='lines+markers',
        name=f"{category.value} - {country.value}",
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4')
    ))
    
    fig.update_layout(
        title=f"Date Progression: {category.value} - {country.value}",
        xaxis_title="Bulletin Sequence",
        yaxis_title="Priority Date",
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary stats
    if len(valid_data) >= 2:
        first_date = valid_data[0]['date']
        last_date = valid_data[-1]['date']
        total_advancement = (last_date - first_date).days
        periods = len(valid_data) - 1
        avg_advancement = total_advancement / periods if periods > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🗓️ First Date", first_date.strftime("%m/%d/%Y"))
        with col2:
            st.metric("🗓️ Latest Date", last_date.strftime("%m/%d/%Y"))  
        with col3:
            st.metric("📈 Avg per Period", f"{avg_advancement:.1f} days")


def render_comparison_chart(predictions: List[PredictionResult]) -> None:
    """
    Render comparison chart for multiple predictions
    
    Args:
        predictions: List of prediction results to compare
    """
    if not predictions or len(predictions) < 2:
        st.info("📊 Need at least 2 predictions for comparison")
        return
    
    st.markdown(
        "<h3 style='margin-bottom: 1rem;'>🔍 Prediction Comparison</h3>",
        unsafe_allow_html=True,
    )
    
    # Create comparison DataFrame
    comparison_data = []
    for pred in predictions:
        comparison_data.append({
            "Category": pred.category.value,
            "Country": pred.country.value,
            "Label": f"{pred.category.value}-{pred.country.value}",
            "Predicted Date": pred.predicted_date.strftime("%Y-%m-%d") if pred.predicted_date else "N/A",
            "Confidence": pred.confidence_score * 100,
            "Type": pred.prediction_type.replace("_", " ").title()
        })
    
    df = pd.DataFrame(comparison_data)
    
    # Confidence comparison bar chart
    fig = px.bar(
        df, 
        x="Label", 
        y="Confidence",
        color="Type",
        title="Prediction Confidence Comparison",
        labels={"Confidence": "Confidence (%)", "Label": "Category-Country"}
    )
    
    fig.update_layout(height=400, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("**📋 Detailed Comparison**")
    st.dataframe(df, use_container_width=True)