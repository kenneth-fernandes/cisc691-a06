"""
Visa category and country selection component
"""

import streamlit as st
from typing import Optional, Tuple
from visa.models import VisaCategory, CountryCode


def render_visa_selector() -> Tuple[Optional[VisaCategory], Optional[CountryCode]]:
    """
    Render visa category and country selection components
    
    Returns:
        Tuple of (selected_category, selected_country) or (None, None) if nothing selected
    """
    st.markdown(
        "<h3 style='margin-bottom: 1rem;'>🎯 Visa Category Selection</h3>",
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            "<p style='margin-bottom: 0.5rem; font-weight: 600;'>📋 Category</p>",
            unsafe_allow_html=True,
        )
        
        # Group categories by type for better UX
        employment_categories = [
            ("EB-1 (Priority Workers)", VisaCategory.EB1),
            ("EB-2 (Advanced Degree)", VisaCategory.EB2),
            ("EB-3 (Skilled Workers)", VisaCategory.EB3),
            ("EB-4 (Special Immigrants)", VisaCategory.EB4),
            ("EB-5 (Investors)", VisaCategory.EB5),
        ]
        
        family_categories = [
            ("F1 (Unmarried Adult Children)", VisaCategory.F1),
            ("F2A (Spouses/Children of LPR)", VisaCategory.F2A),
            ("F2B (Unmarried Adult Children of LPR)", VisaCategory.F2B),
            ("F3 (Married Adult Children)", VisaCategory.F3),
            ("F4 (Siblings)", VisaCategory.F4),
        ]
        
        category_type = st.selectbox(
            "Category Type",
            ["Select Category Type...", "Employment-Based", "Family-Based"],
            label_visibility="collapsed"
        )
        
        selected_category = None
        if category_type == "Employment-Based":
            category_display = st.selectbox(
                "Employment Category",
                ["Select EB Category..."] + [cat[0] for cat in employment_categories],
                label_visibility="collapsed"
            )
            if category_display != "Select EB Category...":
                selected_category = next(cat[1] for cat in employment_categories if cat[0] == category_display)
                
        elif category_type == "Family-Based":
            category_display = st.selectbox(
                "Family Category", 
                ["Select F Category..."] + [cat[0] for cat in family_categories],
                label_visibility="collapsed"
            )
            if category_display != "Select F Category...":
                selected_category = next(cat[1] for cat in family_categories if cat[0] == category_display)
    
    with col2:
        st.markdown(
            "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🌍 Country</p>",
            unsafe_allow_html=True,
        )
        
        country_options = [
            ("All Countries Except Listed", CountryCode.WORLDWIDE),
            ("China", CountryCode.CHINA),
            ("India", CountryCode.INDIA), 
            ("Mexico", CountryCode.MEXICO),
            ("Philippines", CountryCode.PHILIPPINES),
        ]
        
        country_display = st.selectbox(
            "Country",
            ["Select Country..."] + [country[0] for country in country_options],
            label_visibility="collapsed"
        )
        
        selected_country = None
        if country_display != "Select Country...":
            selected_country = next(country[1] for country in country_options if country[0] == country_display)
    
    # Display current selection with visual feedback
    if selected_category and selected_country:
        st.markdown(
            f"""
            <div style='background-color: #1f77b415; 
                        border: 1px solid #1f77b4; 
                        border-radius: 5px; 
                        padding: 10px; 
                        margin: 15px 0;
                        text-align: center;'>
                <strong>🎯 Selected:</strong> {selected_category.value} - {selected_country.value}
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        return selected_category, selected_country
    
    return None, None


def render_country_filter() -> Optional[CountryCode]:
    """
    Render standalone country filter component
    
    Returns:
        Selected country or None if nothing selected
    """
    st.markdown(
        "<p style='margin-bottom: 0.5rem; font-weight: 600;'>🌍 Filter by Country</p>",
        unsafe_allow_html=True,
    )
    
    country_options = [
        ("All Countries", CountryCode.WORLDWIDE),
        ("China", CountryCode.CHINA),
        ("India", CountryCode.INDIA),
        ("Mexico", CountryCode.MEXICO), 
        ("Philippines", CountryCode.PHILIPPINES),
    ]
    
    country_display = st.selectbox(
        "Country Filter",
        [country[0] for country in country_options],
        label_visibility="collapsed"
    )
    
    return next(country[1] for country in country_options if country[0] == country_display)


def render_category_filter() -> Optional[VisaCategory]:
    """
    Render standalone category filter component
    
    Returns:
        Selected category or None if nothing selected  
    """
    st.markdown(
        "<p style='margin-bottom: 0.5rem; font-weight: 600;'>📋 Filter by Category</p>",
        unsafe_allow_html=True,
    )
    
    all_categories = [
        ("EB-1", VisaCategory.EB1),
        ("EB-2", VisaCategory.EB2), 
        ("EB-3", VisaCategory.EB3),
        ("EB-4", VisaCategory.EB4),
        ("EB-5", VisaCategory.EB5),
        ("F1", VisaCategory.F1),
        ("F2A", VisaCategory.F2A),
        ("F2B", VisaCategory.F2B),
        ("F3", VisaCategory.F3),
        ("F4", VisaCategory.F4),
    ]
    
    category_display = st.selectbox(
        "Category Filter",
        ["All Categories"] + [cat[0] for cat in all_categories],
        label_visibility="collapsed"
    )
    
    if category_display == "All Categories":
        return None
    
    return next(cat[1] for cat in all_categories if cat[0] == category_display)