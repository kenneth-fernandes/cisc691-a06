"""
Visa Prediction Page with Real Database Integration
"""

import streamlit as st
from datetime import datetime, date
from typing import Optional
import traceback

from ui.components.visa_selector import render_visa_selector
from ui.components.prediction_display import (
    render_prediction_results, 
    render_historical_chart, 
    render_trend_analysis
)
from ui.components.styles import load_custom_css
from visa.models import VisaCategory, CountryCode, PredictionResult
from visa.database import VisaDatabase
from visa.predictor import create_predictor, TrendAnalyzer


def get_database_connection():
    """Get database connection with caching"""
    try:
        return VisaDatabase()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def get_historical_data(category: str, country: str, db: VisaDatabase):
    """Get historical data with caching"""
    try:
        cat_enum = VisaCategory(category)
        country_enum = CountryCode(country)
        return db.get_category_history(cat_enum, country_enum)
    except Exception as e:
        st.error(f"Failed to load historical data: {e}")
        return []


def generate_prediction(category: str, country: str, target_month: int, target_year: int, db: VisaDatabase):
    """Generate prediction with caching"""
    try:
        # Create predictor (RandomForest by default)
        predictor = create_predictor('randomforest', db)
        
        # Check if we have enough data to train
        cat_enum = VisaCategory(category)
        country_enum = CountryCode(country)
        history = db.get_category_history(cat_enum, country_enum)
        
        if len(history) < 3:
            return None, "Insufficient historical data for prediction"
        
        # Train the model (this would ideally be pre-trained and saved)
        with st.spinner("Training prediction model..."):
            try:
                metrics = predictor.train()
                st.success(f"Model trained with MAE: {metrics.get('test_mae', 'N/A'):.2f}")
            except Exception as e:
                return None, f"Model training failed: {str(e)}"
        
        # Make prediction
        prediction = predictor.predict(cat_enum, country_enum, target_month, target_year)
        return prediction, None
        
    except Exception as e:
        return None, f"Prediction failed: {str(e)}"


def render_visa_prediction_page():
    """Render the visa prediction page with real database integration"""
    
    # Load custom styles
    load_custom_css()
    
    st.title("🔮 Visa Bulletin Prediction")
    st.markdown("Real-time predictions using historical visa bulletin data from PostgreSQL/SQLite")
    
    # Database connection status
    db = get_database_connection()
    if not db:
        st.error("❌ Cannot connect to database. Please check your database configuration.")
        return
    
    # Show database info
    try:
        stats = db.get_database_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Bulletins", stats.get('bulletin_count', 0))
        with col2:
            st.metric("📋 Category Data", stats.get('category_data_count', 0))
        with col3:
            st.metric("🔮 Predictions", stats.get('prediction_count', 0))
        with col4:
            st.metric("📅 Year Range", stats.get('year_range', 'N/A'))
        
        # Show database type
        db_type = "PostgreSQL" if db.use_postgres else "SQLite"
        st.info(f"🗄️ Connected to {db_type} database")
    except Exception as e:
        st.warning(f"Could not load database stats: {e}")
    
    st.markdown("---")
    
    # Visa selector
    selected_category, selected_country = render_visa_selector()
    
    if selected_category and selected_country:
        st.markdown("---")
        
        # Show historical data
        with st.expander("📊 Historical Data", expanded=True):
            with st.spinner("Loading historical data..."):
                history = get_historical_data(
                    selected_category.value, 
                    selected_country.value, 
                    db
                )
            
            if history:
                st.success(f"Found {len(history)} historical records")
                render_historical_chart(history, selected_category, selected_country)
                
                # Show trend analysis
                try:
                    analyzer = TrendAnalyzer(db)
                    trend = analyzer.analyze_category_trend(selected_category, selected_country)
                    render_trend_analysis(trend)
                except Exception as e:
                    st.warning(f"Trend analysis failed: {e}")
            else:
                st.warning("No historical data found for this category and country combination")
        
        # Prediction section
        st.markdown("---")
        st.markdown("### 🔮 Generate Prediction")
        
        col1, col2 = st.columns(2)
        with col1:
            target_month = st.selectbox(
                "Target Month",
                range(1, 13),
                index=datetime.now().month - 1,
                format_func=lambda x: datetime(2024, x, 1).strftime("%B")
            )
        with col2:
            target_year = st.selectbox(
                "Target Year", 
                range(2024, 2027),
                index=0
            )
        
        if st.button("🚀 Generate Prediction", type="primary"):
            with st.spinner("Generating prediction..."):
                prediction, error = generate_prediction(
                    selected_category.value,
                    selected_country.value, 
                    target_month,
                    target_year,
                    db
                )
            
            if prediction:
                render_prediction_results(prediction)
                
                # Save prediction to database
                try:
                    db.save_prediction(prediction)
                    st.success("✅ Prediction saved to database")
                except Exception as e:
                    st.warning(f"Could not save prediction: {e}")
            else:
                st.error(f"❌ {error}")
        
        # Show recent predictions
        st.markdown("---")
        with st.expander("📝 Recent Predictions"):
            try:
                recent_predictions = db.get_latest_predictions(
                    selected_category, 
                    selected_country
                )
                if recent_predictions:
                    for i, pred in enumerate(recent_predictions[:5]):  # Show last 5
                        st.markdown(f"**{i+1}.** {pred.prediction_type.title()} - "
                                  f"Confidence: {pred.confidence_score*100:.0f}% - "
                                  f"Created: {pred.created_at.strftime('%Y-%m-%d %H:%M')}")
                else:
                    st.info("No recent predictions found")
            except Exception as e:
                st.warning(f"Could not load recent predictions: {e}")
    
    else:
        st.info("👆 Select a visa category and country to see predictions and historical data")
        
        # Show some general statistics
        if db:
            st.markdown("---")
            st.markdown("### 📈 Available Data Overview")
            try:
                # Get some sample data to show what's available
                all_bulletins = db.get_bulletins_range(2020, 2024)
                if all_bulletins:
                    st.success(f"Database contains {len(all_bulletins)} bulletins from 2020-2024")
                    
                    # Show categories with data
                    categories_with_data = set()
                    countries_with_data = set()
                    for bulletin in all_bulletins[:10]:  # Sample first 10
                        for cat_data in bulletin.categories:
                            categories_with_data.add(cat_data.category.value)
                            countries_with_data.add(cat_data.country.value)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Available Categories:**")
                        for cat in sorted(categories_with_data):
                            st.markdown(f"• {cat}")
                    
                    with col2:
                        st.markdown("**Available Countries:**")
                        for country in sorted(countries_with_data):
                            st.markdown(f"• {country}")
                else:
                    st.warning("No bulletin data found in database")
            except Exception as e:
                st.error(f"Could not load data overview: {e}")
                st.error(traceback.format_exc())