"""
Visa Analytics page implementation
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.utils.api_client import get_api_client

def init_analytics_state():
    """Initialize analytics session state"""
    if "api_client" not in st.session_state:
        st.session_state.api_client = get_api_client()

def render_analytics_page():
    """Render the visa analytics interface"""
    st.title("📊 Visa Analytics Dashboard")
    
    # Initialize state
    init_analytics_state()
    api_client = st.session_state.api_client
    
    # Check API connection
    health_check = api_client.health_check()
    if "error" in health_check:
        st.error("🚫 Cannot connect to API server. Please start the API server first.")
        st.code("python scripts/start_api.py")
        return
    
    # Create tabs for different analytics
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🔮 Predictions", "📋 Historical Data", "📊 Database Stats"])
    
    with tab1:
        render_trends_analysis(api_client)
    
    with tab2:
        render_predictions(api_client)
    
    with tab3:
        render_historical_data(api_client)
    
    with tab4:
        render_database_stats(api_client)

def render_trends_analysis(api_client):
    """Render trends analysis section"""
    st.header("📈 Visa Bulletin Trend Analysis")
    
    # Get categories and countries
    categories_response = api_client.get_visa_categories()
    countries_response = api_client.get_visa_countries()
    
    if "error" in categories_response or "error" in countries_response:
        st.error("Failed to load categories or countries from API")
        return
    
    # Create input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get employment categories
        eb_categories = categories_response.get("employment_based", ["EB-1", "EB-2", "EB-3"])
        fb_categories = categories_response.get("family_based", ["F1", "F2A", "F2B"])
        all_categories = eb_categories + fb_categories
        
        selected_category = st.selectbox(
            "Visa Category",
            all_categories,
            index=1  # Default to EB-2
        )
    
    with col2:
        countries = countries_response.get("countries", ["India", "China", "Worldwide"])
        selected_country = st.selectbox(
            "Country",
            countries,
            index=0  # Default to India
        )
    
    with col3:
        years_back = st.slider(
            "Years to Analyze",
            min_value=1,
            max_value=5,
            value=2
        )
    
    # Analyze button
    if st.button("📊 Analyze Trends", type="primary"):
        with st.spinner("Analyzing trends..."):
            trends_response = api_client.analyze_visa_trends(
                category=selected_category,
                country=selected_country,
                years_back=years_back
            )
        
        if "error" in trends_response:
            st.error(f"Analysis failed: {trends_response['error']}")
        else:
            display_trends_results(trends_response)

def display_trends_results(trends_response):
    """Display trends analysis results"""
    analysis = trends_response.get("analysis", {})
    
    if not analysis:
        st.warning("No analysis data received")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Advancement",
            f"{analysis.get('total_advancement_days', 0)} days"
        )
    
    with col2:
        st.metric(
            "Avg Monthly Advancement",
            f"{analysis.get('average_monthly_advancement', 0):.1f} days"
        )
    
    with col3:
        st.metric(
            "Volatility Score",
            f"{analysis.get('volatility_score', 0):.2f}"
        )
    
    with col4:
        trend_direction = analysis.get('trend_direction', 'unknown')
        if trend_direction == 'advancing':
            st.metric("Trend", "📈 Advancing", delta="Positive")
        elif trend_direction == 'retrogressing':
            st.metric("Trend", "📉 Retrogressing", delta="Negative")
        else:
            st.metric("Trend", "➡️ Stable", delta="Neutral")

def render_predictions(api_client):
    """Render predictions section"""
    st.header("🔮 Visa Movement Predictions")
    
    # Get categories and countries (same as trends)
    categories_response = api_client.get_visa_categories()
    countries_response = api_client.get_visa_countries()
    
    if "error" in categories_response or "error" in countries_response:
        st.error("Failed to load categories or countries from API")
        return
    
    # Input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        eb_categories = categories_response.get("employment_based", ["EB-1", "EB-2", "EB-3"])
        fb_categories = categories_response.get("family_based", ["F1", "F2A", "F2B"])
        all_categories = eb_categories + fb_categories
        
        pred_category = st.selectbox(
            "Visa Category",
            all_categories,
            key="pred_category"
        )
    
    with col2:
        countries = countries_response.get("countries", ["India", "China", "Worldwide"])
        pred_country = st.selectbox(
            "Country",
            countries,
            key="pred_country"
        )
    
    with col3:
        months_ahead = st.slider(
            "Months to Predict",
            min_value=1,
            max_value=12,
            value=3
        )
    
    if st.button("🔮 Generate Prediction", type="primary"):
        with st.spinner("Generating prediction..."):
            pred_response = api_client.predict_visa_movement(
                category=pred_category,
                country=pred_country,
                months_ahead=months_ahead
            )
        
        if "error" in pred_response:
            st.error(f"Prediction failed: {pred_response['error']}")
        else:
            prediction = pred_response.get("prediction", {})
            if prediction:
                st.success("Prediction generated successfully!")
                st.json(prediction)
            else:
                st.warning("No prediction data received")

def render_historical_data(api_client):
    """Render historical data section"""
    st.header("📋 Historical Visa Bulletin Data")
    
    # Get categories and countries
    categories_response = api_client.get_visa_categories()
    countries_response = api_client.get_visa_countries()
    
    if "error" in categories_response or "error" in countries_response:
        st.error("Failed to load categories or countries from API")
        return
    
    # Input form
    col1, col2 = st.columns(2)
    
    with col1:
        eb_categories = categories_response.get("employment_based", ["EB-1", "EB-2", "EB-3"])
        fb_categories = categories_response.get("family_based", ["F1", "F2A", "F2B"])
        all_categories = eb_categories + fb_categories
        
        hist_category = st.selectbox(
            "Visa Category",
            all_categories,
            key="hist_category"
        )
    
    with col2:
        countries = countries_response.get("countries", ["India", "China", "Worldwide"])
        hist_country = st.selectbox(
            "Country",
            countries,
            key="hist_country"
        )
    
    if st.button("📋 Load Historical Data", type="primary"):
        with st.spinner("Loading historical data..."):
            hist_response = api_client.get_historical_data(
                category=hist_category,
                country=hist_country
            )
        
        if "error" in hist_response:
            st.error(f"Failed to load data: {hist_response['error']}")
        else:
            historical_data = hist_response.get("historical_data", [])
            data_points = hist_response.get("data_points", 0)
            
            st.success(f"Loaded {data_points} data points")
            
            if historical_data:
                # Convert to DataFrame for better display
                df = pd.DataFrame(historical_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No historical data found for the selected category and country")

def render_database_stats(api_client):
    """Render database statistics section"""
    st.header("📊 Database Statistics")
    
    with st.spinner("Loading database statistics..."):
        stats_response = api_client.get_database_stats()
    
    if "error" in stats_response:
        st.error(f"Failed to load statistics: {stats_response['error']}")
        return
    
    # Display key statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Bulletins",
            stats_response.get("total_bulletins", 0)
        )
    
    with col2:
        st.metric(
            "Total Categories",
            stats_response.get("total_categories", 0)
        )
    
    with col3:
        st.metric(
            "Year Range",
            stats_response.get("year_range", "No data")
        )
    
    # Display detailed stats
    st.subheader("Detailed Statistics")
    database_stats = stats_response.get("database_stats", {})
    if database_stats:
        st.json(database_stats)
    else:
        st.warning("No detailed statistics available")