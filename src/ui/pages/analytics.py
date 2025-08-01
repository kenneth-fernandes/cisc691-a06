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
    
    # Create advancement chart if data is available
    advancement_list = analysis.get('advancement_list', [])
    if advancement_list:
        st.subheader("📈 Advancement Pattern")
        
        # Create a line chart showing advancement over time
        fig_trend = px.line(
            x=range(1, len(advancement_list) + 1),
            y=advancement_list,
            title="Monthly Advancement Pattern",
            labels={'x': 'Month', 'y': 'Days Advanced'},
            markers=True
        )
        fig_trend.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="No Movement")
        fig_trend.update_layout(showlegend=False)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Show advancement statistics
        if advancement_list:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Best Month", f"{max(advancement_list)} days")
            with col2:
                st.metric("Worst Month", f"{min(advancement_list)} days")
            with col3:
                positive_months = len([x for x in advancement_list if x > 0])
                st.metric("Positive Months", f"{positive_months}/{len(advancement_list)}")
    
    # Show raw analysis data in expandable section
    with st.expander("📋 Raw Analysis Data"):
        st.json(analysis)

def display_prediction_results(prediction, category, country):
    """Display prediction results with visualizations"""
    st.subheader(f"🔮 Prediction for {category} - {country}")
    
    # Display key prediction metrics
    col1, col2, col3 = st.columns(3)
    
    # Extract data from the API response structure
    predictions_list = prediction.get('predictions', [])
    confidence_data = prediction.get('confidence', {})
    methodology = prediction.get('methodology', 'Unknown')
    
    with col1:
        # Show next month's prediction if available
        if predictions_list:
            pred_advancement = predictions_list[0].get('predicted_advancement', 0)
            predicted_date = f"{pred_advancement:+d} days" if pred_advancement != 0 else "No movement"
        else:
            predicted_date = 'Not available'
        st.metric("Predicted Movement", predicted_date)
    
    with col2:
        confidence_score = confidence_data.get('score', 0)
        st.metric("Confidence Score", f"{confidence_score:.1f}%")
    
    with col3:
        st.metric("Prediction Type", methodology.replace('_', ' ').title())
    
    # Display additional prediction details and visualizations
    if predictions_list and len(predictions_list) > 0:
        st.subheader("📊 Prediction Details")
        
        # Show all predictions if multiple months
        if len(predictions_list) > 1:
            st.subheader("📈 Multi-Month Predictions")
            pred_data = []
            for i, pred in enumerate(predictions_list):
                pred_data.append({
                    'Month': i + 1,
                    'Predicted Days': pred.get('predicted_advancement', 0),
                    'Range Low': pred.get('range_low', 0),
                    'Range High': pred.get('range_high', 0)
                })
            
            pred_df = pd.DataFrame(pred_data)
            st.dataframe(pred_df, use_container_width=True)
        
        # Create a gauge chart for confidence
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode = "gauge+number",
            value = confidence_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Confidence Level (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "yellow"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show confidence factors if available
        confidence_factors = confidence_data.get('factors', {})
        if confidence_factors:
            st.subheader("🎯 Confidence Factors")
            factors_col1, factors_col2 = st.columns(2)
            
            with factors_col1:
                st.metric("Data Points", confidence_factors.get('data_points', 'N/A'))
                st.metric("Consistency", f"{confidence_factors.get('consistency', 0):.1f}")
            
            with factors_col2:
                st.metric("Volatility", f"{confidence_factors.get('volatility', 0):.1f}")
                st.metric("Recent Stability", f"{confidence_factors.get('recent_stability', 0):.1f}")
    
    # Show disclaimer
    disclaimer = prediction.get('disclaimer', '')
    if disclaimer:
        st.info(f"ℹ️ {disclaimer}")
    
    # Show raw prediction data in expandable section
    with st.expander("📋 Raw Prediction Data"):
        st.json(prediction)

def display_database_charts(database_stats):
    """Display database statistics with charts and visualizations"""
    
    # Create overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Latest Bulletin", database_stats.get('latest_bulletin', 'None'))
    
    with col2:
        st.metric("Oldest Bulletin", database_stats.get('oldest_bulletin', 'None'))
    
    with col3:
        st.metric("Years Covered", database_stats.get('total_years_covered', 0))
    
    # Create data distribution charts
    st.subheader("📈 Data Distribution")
    
    # Create a pie chart showing data breakdown
    labels = ['Bulletins', 'Category Records', 'Predictions']
    values = [
        database_stats.get('bulletin_count', 0),
        database_stats.get('category_data_count', 0),
        database_stats.get('prediction_count', 0)
    ]
    
    fig_pie = px.pie(
        values=values, 
        names=labels,
        title="Database Content Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Create a bar chart showing categories and countries tracked
    st.subheader("📊 Coverage Statistics")
    
    coverage_data = {
        'Type': ['Categories Tracked', 'Countries Tracked'],
        'Count': [
            database_stats.get('categories_tracked', 0),
            database_stats.get('countries_tracked', 0)
        ]
    }
    
    fig_bar = px.bar(
        coverage_data,
        x='Type',
        y='Count',
        title="Categories and Countries Coverage",
        color='Type',
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    fig_bar.update_layout(showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Show detailed stats in expandable section
    with st.expander("📋 Detailed Database Statistics"):
        st.json(database_stats)

def display_historical_charts(df, category, country):
    """Display historical data with charts and visualizations"""
    st.subheader(f"📋 Historical Data for {category} - {country}")
    
    # Show data table first
    st.dataframe(df, use_container_width=True)
    
    # Try to create timeline charts if date columns exist
    if 'final_action_date' in df.columns and not df['final_action_date'].isna().all():
        # Filter out null dates and convert to datetime
        df_filtered = df[df['final_action_date'].notna()].copy()
        
        if not df_filtered.empty:
            try:
                df_filtered['final_action_date'] = pd.to_datetime(df_filtered['final_action_date'])
                df_filtered = df_filtered.sort_values('final_action_date')
                
                # Create timeline chart for final action dates
                fig_timeline = px.line(
                    df_filtered,
                    x='final_action_date',
                    y=range(len(df_filtered)),
                    title=f"Final Action Date Timeline - {category} {country}",
                    labels={'y': 'Data Point Index', 'final_action_date': 'Final Action Date'},
                    markers=True
                )
                fig_timeline.update_yaxis(title="Data Point Index")
                fig_timeline.update_layout(showlegend=False)
                st.plotly_chart(fig_timeline, use_container_width=True)
                
                # Show movement analysis if we have multiple points
                if len(df_filtered) > 1:
                    df_filtered['date_advancement'] = df_filtered['final_action_date'].diff().dt.days
                    advancement_data = df_filtered[df_filtered['date_advancement'].notna()]
                    
                    if not advancement_data.empty:
                        fig_advancement = px.bar(
                            advancement_data,
                            x='final_action_date',
                            y='date_advancement',
                            title=f"Date Advancement Analysis - {category} {country}",
                            labels={'date_advancement': 'Days Advanced', 'final_action_date': 'Bulletin Date'},
                            color='date_advancement',
                            color_continuous_scale='RdYlGn'
                        )
                        st.plotly_chart(fig_advancement, use_container_width=True)
            
            except Exception as e:
                st.warning(f"Could not create timeline chart: {str(e)}")
    
    # Show status distribution if available
    if 'status' in df.columns:
        status_counts = df['status'].value_counts()
        if not status_counts.empty:
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title=f"Status Distribution - {category} {country}"
            )
            st.plotly_chart(fig_status, use_container_width=True)

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
                display_prediction_results(prediction, pred_category, pred_country)
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
                display_historical_charts(df, hist_category, hist_country)
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
    
    # Display detailed stats with charts
    st.subheader("Detailed Statistics")
    database_stats = stats_response.get("database_stats", {})
    if database_stats:
        display_database_charts(database_stats)
    else:
        st.warning("No detailed statistics available")