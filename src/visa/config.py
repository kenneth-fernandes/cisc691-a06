"""
Configuration settings for visa bulletin prediction system
"""
import os
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class VisaConfig:
    """Configuration class for visa bulletin prediction features"""
    
    # Data sources
    STATE_DEPT_URL: str = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
    BULLETIN_BASE_URL: str = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin"
    
    # Visa categories
    EMPLOYMENT_CATEGORIES: List[str] = field(default_factory=lambda: ["EB-1", "EB-2", "EB-3", "EB-4", "EB-5"])
    FAMILY_CATEGORIES: List[str] = field(default_factory=lambda: ["F1", "F2A", "F2B", "F3", "F4"])
    
    # Countries with special processing
    SPECIAL_COUNTRIES: List[str] = field(default_factory=lambda: ["China", "India", "Mexico", "Philippines"])
    
    # Database settings
    DATABASE_PATH: str = os.getenv("VISA_DB_PATH", "data/visa_bulletins.db")
    
    # ML model settings
    MODEL_UPDATE_FREQUENCY_DAYS: int = 30
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Data collection settings
    HISTORICAL_DATA_START_YEAR: int = 2020
    AUTO_UPDATE_ENABLED: bool = True
    
    # Cache settings
    CACHE_DURATION_HOURS: int = 24
    
    @classmethod
    def get_category_mapping(cls) -> Dict[str, str]:
        """Get mapping of category codes to full names"""
        return {
            "EB-1": "Employment-Based First Preference",
            "EB-2": "Employment-Based Second Preference", 
            "EB-3": "Employment-Based Third Preference",
            "EB-4": "Employment-Based Fourth Preference",
            "EB-5": "Employment-Based Fifth Preference",
            "F1": "Unmarried Sons and Daughters of U.S. Citizens",
            "F2A": "Spouses and Unmarried Children of Permanent Residents",
            "F2B": "Unmarried Sons and Daughters of Permanent Residents",
            "F3": "Married Sons and Daughters of U.S. Citizens",
            "F4": "Brothers and Sisters of U.S. Citizens"
        }
    
    @classmethod
    def validate_category(cls, category: str) -> bool:
        """Validate if a category is supported"""
        employment_cats = ["EB-1", "EB-2", "EB-3", "EB-4", "EB-5"]
        family_cats = ["F1", "F2A", "F2B", "F3", "F4"]
        return category in employment_cats + family_cats
    
    @classmethod
    def validate_country(cls, country: str) -> bool:
        """Validate if a country is in special processing list"""
        special_countries = ["China", "India", "Mexico", "Philippines"]
        return country in special_countries or country == "Worldwide"