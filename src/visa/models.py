"""
Data models for visa bulletin prediction system
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from enum import Enum
import json


class VisaCategory(Enum):
    """Enumeration of visa categories"""
    # Employment-based categories
    EB1 = "EB-1"
    EB2 = "EB-2" 
    EB3 = "EB-3"
    EB4 = "EB-4"
    EB5 = "EB-5"
    
    # Family-based categories
    F1 = "F1"
    F2A = "F2A"
    F2B = "F2B"
    F3 = "F3"
    F4 = "F4"


class CountryCode(Enum):
    """Enumeration of country codes with special processing"""
    WORLDWIDE = "Worldwide"
    CHINA = "China"
    INDIA = "India"
    MEXICO = "Mexico"
    PHILIPPINES = "Philippines"


class BulletinStatus(Enum):
    """Status of visa bulletin entries"""
    CURRENT = "C"
    UNAVAILABLE = "U"
    DATE_SPECIFIED = "DATE"


@dataclass
class CategoryData:
    """Data model for individual category information in a visa bulletin"""
    category: VisaCategory
    country: CountryCode
    final_action_date: Optional[date] = None
    filing_date: Optional[date] = None
    status: BulletinStatus = BulletinStatus.DATE_SPECIFIED
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate data after initialization"""
        if isinstance(self.category, str):
            self.category = VisaCategory(self.category)
        if isinstance(self.country, str):
            self.country = CountryCode(self.country)
        if isinstance(self.status, str):
            self.status = BulletinStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "country": self.country.value,
            "final_action_date": self.final_action_date.isoformat() if self.final_action_date else None,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "status": self.status.value,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryData':
        """Create instance from dictionary"""
        return cls(
            category=VisaCategory(data["category"]),
            country=CountryCode(data["country"]),
            final_action_date=datetime.fromisoformat(data["final_action_date"]).date() if data.get("final_action_date") else None,
            filing_date=datetime.fromisoformat(data["filing_date"]).date() if data.get("filing_date") else None,
            status=BulletinStatus(data["status"]),
            notes=data.get("notes")
        )


@dataclass
class VisaBulletin:
    """Data model for a complete visa bulletin"""
    bulletin_date: date
    fiscal_year: int
    month: int
    year: int
    categories: List[CategoryData] = field(default_factory=list)
    source_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate bulletin data after initialization"""
        if self.fiscal_year < 2020 or self.fiscal_year > 2030:
            raise ValueError(f"Invalid fiscal year: {self.fiscal_year}")
        if self.month < 1 or self.month > 12:
            raise ValueError(f"Invalid month: {self.month}")
    
    def add_category_data(self, category_data: CategoryData):
        """Add category data to the bulletin"""
        self.categories.append(category_data)
        self.updated_at = datetime.now()
    
    def get_category_data(self, category: VisaCategory, country: CountryCode) -> Optional[CategoryData]:
        """Get specific category data"""
        for cat_data in self.categories:
            if cat_data.category == category and cat_data.country == country:
                return cat_data
        return None
    
    def get_employment_categories(self) -> List[CategoryData]:
        """Get all employment-based categories"""
        employment_cats = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, VisaCategory.EB4, VisaCategory.EB5]
        return [cat for cat in self.categories if cat.category in employment_cats]
    
    def get_family_categories(self) -> List[CategoryData]:
        """Get all family-based categories"""
        family_cats = [VisaCategory.F1, VisaCategory.F2A, VisaCategory.F2B, VisaCategory.F3, VisaCategory.F4]
        return [cat for cat in self.categories if cat.category in family_cats]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "bulletin_date": self.bulletin_date.isoformat(),
            "fiscal_year": self.fiscal_year,
            "month": self.month,
            "year": self.year,
            "categories": [cat.to_dict() for cat in self.categories],
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisaBulletin':
        """Create instance from dictionary"""
        bulletin = cls(
            bulletin_date=datetime.fromisoformat(data["bulletin_date"]).date(),
            fiscal_year=data["fiscal_year"],
            month=data["month"],
            year=data["year"],
            source_url=data.get("source_url"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        
        for cat_data in data.get("categories", []):
            bulletin.add_category_data(CategoryData.from_dict(cat_data))
        
        return bulletin


@dataclass
class PredictionResult:
    """Data model for prediction results"""
    category: VisaCategory
    country: CountryCode
    predicted_date: Optional[date]
    confidence_score: float
    prediction_type: str  # "advancement", "retrogression", "current", "unavailable"
    target_month: int
    target_year: int
    created_at: datetime = field(default_factory=datetime.now)
    model_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "country": self.country.value,
            "predicted_date": self.predicted_date.isoformat() if self.predicted_date else None,
            "confidence_score": self.confidence_score,
            "prediction_type": self.prediction_type,
            "target_month": self.target_month,
            "target_year": self.target_year,
            "created_at": self.created_at.isoformat(),
            "model_version": self.model_version
        }


@dataclass  
class TrendAnalysis:
    """Data model for trend analysis results"""
    category: VisaCategory
    country: CountryCode
    start_date: date
    end_date: date
    total_advancement_days: int
    average_monthly_advancement: float
    volatility_score: float
    trend_direction: str  # "advancing", "retrogressing", "stable"
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "country": self.country.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_advancement_days": self.total_advancement_days,
            "average_monthly_advancement": self.average_monthly_advancement,
            "volatility_score": self.volatility_score,
            "trend_direction": self.trend_direction,
            "analysis_date": self.analysis_date.isoformat()
        }