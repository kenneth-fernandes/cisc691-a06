"""
Visa bulletin expertise and prompts for the AI agent
"""
from typing import Dict
from ..visa.models import VisaCategory, CountryCode, BulletinStatus

# Knowledge base for visa bulletin understanding
VISA_CATEGORIES_INFO = {
    VisaCategory.EB1: {
        "name": "Employment-Based First Preference",
        "description": "Priority workers including persons of extraordinary ability, outstanding professors/researchers, and multinational executives",
        "typical_processing": "Generally moves faster than other employment categories"
    },
    VisaCategory.EB2: {
        "name": "Employment-Based Second Preference",
        "description": "Advanced degree professionals or persons of exceptional ability",
        "typical_processing": "Subject to significant retrogression for certain countries"
    },
    VisaCategory.EB3: {
        "name": "Employment-Based Third Preference",
        "description": "Skilled workers, professionals, and other workers",
        "typical_processing": "Often experiences longer wait times than EB1 and EB2"
    },
    VisaCategory.F1: {
        "name": "Family First Preference",
        "description": "Unmarried sons and daughters of U.S. citizens",
        "typical_processing": "Processing times vary by country"
    },
    VisaCategory.F2A: {
        "name": "Family Second Preference A",
        "description": "Spouses and children of permanent residents",
        "typical_processing": "Generally moves faster than other family categories"
    }
}

COUNTRY_SPECIFIC_INFO = {
    CountryCode.INDIA: {
        "key_factors": ["High demand for EB2/EB3", "Significant backlog", "Regular retrogression"],
        "typical_patterns": "EB2 and EB3 categories often face multi-year waiting periods"
    },
    CountryCode.CHINA: {
        "key_factors": ["High EB5 usage", "EB2/EB3 backlog", "Regular updates"],
        "typical_patterns": "EB5 category closely watched due to high investor interest"
    }
}

# System prompt template for visa bulletin expertise
VISA_EXPERT_PROMPT = """You are an AI assistant specialized in U.S. visa bulletin analysis and interpretation. Your capabilities include:

1. Understanding visa bulletin data and trends:
   - Interpret dates and status changes for all visa categories
   - Analyze historical patterns and movement
   - Explain category-specific characteristics

2. Category expertise:
   - Detailed knowledge of employment-based categories (EB1-EB5)
   - Family-based categories (F1-F4)
   - Country-specific processing patterns

3. Date calculations and predictions:
   - Calculate priority date movements
   - Understand fiscal year implications
   - Interpret visa bulletin tables and charts

4. Technical understanding:
   - Final Action Dates vs. Filing Dates
   - Priority date cutoffs
   - Visa number availability
   - Retrogression and advancement patterns

Use clear, accurate language and reference specific visa bulletin data when available.
Always consider country-specific factors and historical patterns in your analysis."""

# Domain-specific prompt templates
PROMPT_TEMPLATES = {
    "analyze_movement": """Analyze the movement pattern for {category} category for {country} between {start_date} and {end_date}.
Consider:
1. Total advancement/retrogression
2. Monthly rate of change
3. Any unusual patterns
4. Comparison to historical trends""",

    "predict_movement": """Based on historical data, predict the likely movement for {category} category for {country} in the next {months} months.
Consider:
1. Recent movement patterns
2. Seasonal factors
3. Known policy changes
4. Country-specific factors""",

    "explain_status": """Explain the current status of {category} category for {country}:
1. Current priority date
2. Recent movement pattern
3. Factors affecting movement
4. Comparison to similar categories"""
}

def get_category_insight(category: VisaCategory) -> Dict:
    """Get detailed insight for a visa category"""
    DEFAULT_INSIGHT = {
        "name": "",
        "description": "Category information not available",
        "typical_processing": "Processing patterns vary"
    }
    insight = VISA_CATEGORIES_INFO.get(category, DEFAULT_INSIGHT)
    if insight is DEFAULT_INSIGHT:
        insight["name"] = category.value
    return insight

def get_country_insight(country: CountryCode) -> Dict:
    """Get country-specific processing insights"""
    return COUNTRY_SPECIFIC_INFO.get(country, {
        "key_factors": ["Standard processing patterns apply"],
        "typical_patterns": "Follows general visa bulletin patterns"
    })