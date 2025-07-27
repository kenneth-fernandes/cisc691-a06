"""
Pydantic models for analytics API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TrendAnalysisRequest(BaseModel):
    """Trend analysis request model"""
    category: str = Field(..., description="Visa category (e.g., EB2)")
    country: str = Field(..., description="Country code (e.g., INDIA)")
    years_back: int = Field(default=3, description="Number of years to analyze")

class TrendAnalysisResponse(BaseModel):
    """Trend analysis response model"""
    category: str = Field(..., description="Analyzed visa category")
    country: str = Field(..., description="Analyzed country")
    analysis: Dict[str, Any] = Field(..., description="Detailed trend analysis results")

class PredictionRequest(BaseModel):
    """Prediction request model"""
    category: str = Field(..., description="Visa category (e.g., EB2)")
    country: str = Field(..., description="Country code (e.g., INDIA)")
    months_ahead: int = Field(default=3, description="Number of months to predict")

class PredictionResponse(BaseModel):
    """Prediction response model"""
    category: str = Field(..., description="Predicted visa category")
    country: str = Field(..., description="Predicted country")
    prediction: Dict[str, Any] = Field(..., description="Prediction results")

class CategoryComparisonRequest(BaseModel):
    """Category comparison request model"""
    country: str = Field(..., description="Country code (e.g., INDIA)")
    categories: List[str] = Field(..., description="List of categories to compare")
    years_back: int = Field(default=2, description="Number of years to analyze")

class CategoryComparisonResponse(BaseModel):
    """Category comparison response model"""
    country: str = Field(..., description="Compared country")
    comparison: Dict[str, Any] = Field(..., description="Comparison results")

class HistoricalDataRequest(BaseModel):
    """Historical data request model"""
    category: str = Field(..., description="Visa category (e.g., EB2)")
    country: str = Field(..., description="Country code (e.g., INDIA)")
    start_year: Optional[int] = Field(None, description="Start year for data")
    end_year: Optional[int] = Field(None, description="End year for data")

class HistoricalDataResponse(BaseModel):
    """Historical data response model"""
    category: str = Field(..., description="Requested visa category")
    country: str = Field(..., description="Requested country")
    data_points: int = Field(..., description="Number of data points returned")
    historical_data: List[Dict[str, Any]] = Field(..., description="Historical bulletin data")

class DatabaseStatsResponse(BaseModel):
    """Database statistics response model"""
    total_bulletins: int = Field(..., description="Total number of bulletins")
    total_categories: int = Field(..., description="Total category data entries")
    year_range: str = Field(..., description="Year range of available data")
    database_stats: Dict[str, Any] = Field(..., description="Detailed database statistics")