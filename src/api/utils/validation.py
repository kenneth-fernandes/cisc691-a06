"""
Input validation utilities for API endpoints
"""
from visa.models import VisaCategory, CountryCode
from typing import Union

def normalize_visa_category(category: str) -> VisaCategory:
    """
    Normalize and validate visa category input
    Handles case-insensitive matching and common variations
    """
    category = category.upper().strip()
    
    # Handle common variations
    category_mappings = {
        "EB1": "EB-1",
        "EB2": "EB-2", 
        "EB3": "EB-3",
        "EB4": "EB-4",
        "EB5": "EB-5",
        "EB-1": "EB-1",
        "EB-2": "EB-2",
        "EB-3": "EB-3", 
        "EB-4": "EB-4",
        "EB-5": "EB-5",
        "F1": "F1",
        "F2A": "F2A",
        "F2B": "F2B",
        "F3": "F3",
        "F4": "F4"
    }
    
    normalized = category_mappings.get(category)
    if not normalized:
        raise ValueError(f"Invalid visa category: {category}")
    
    try:
        return VisaCategory(normalized)
    except ValueError:
        raise ValueError(f"Invalid visa category: {category}")

def normalize_country_code(country: str) -> CountryCode:
    """
    Normalize and validate country code input
    Handles case-insensitive matching and common variations
    """
    country = country.strip()
    
    # Handle common variations
    country_mappings = {
        # Case variations
        "worldwide": "Worldwide",
        "WORLDWIDE": "Worldwide", 
        "china": "China",
        "CHINA": "China",
        "india": "India",
        "INDIA": "India",
        "mexico": "Mexico", 
        "MEXICO": "Mexico",
        "philippines": "Philippines",
        "PHILIPPINES": "Philippines",
        # Exact matches
        "Worldwide": "Worldwide",
        "China": "China", 
        "India": "India",
        "Mexico": "Mexico",
        "Philippines": "Philippines"
    }
    
    normalized = country_mappings.get(country)
    if not normalized:
        raise ValueError(f"Invalid country: {country}")
    
    try:
        return CountryCode(normalized)
    except ValueError:
        raise ValueError(f"Invalid country: {country}")

def validate_input(category: str, country: str) -> tuple[VisaCategory, CountryCode]:
    """
    Validate both category and country inputs
    Returns normalized enum values
    """
    try:
        visa_cat = normalize_visa_category(category)
        country_code = normalize_country_code(country)
        return visa_cat, country_code
    except ValueError as e:
        raise ValueError(f"Invalid category or country: {e}")