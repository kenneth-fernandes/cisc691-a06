"""
Visa Analytics API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import date

from api.models.analytics import (
    TrendAnalysisRequest, TrendAnalysisResponse,
    PredictionRequest, PredictionResponse,
    CategoryComparisonRequest, CategoryComparisonResponse,
    HistoricalDataRequest, HistoricalDataResponse,
    DatabaseStatsResponse
)
from api.utils.validation import validate_input, normalize_visa_category, normalize_country_code
from visa.analytics import TrendAnalyzer
from visa.models import VisaCategory, CountryCode
from visa.repository import VisaBulletinRepository

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize analytics components
trend_analyzer = TrendAnalyzer()
repository = VisaBulletinRepository()

@router.post("/trends", response_model=TrendAnalysisResponse)
async def analyze_trends(request: TrendAnalysisRequest):
    """Analyze visa bulletin trends for a category and country"""
    try:
        # Validate and normalize inputs
        category, country = validate_input(request.category, request.country)
        
        # Perform trend analysis
        analysis = trend_analyzer.calculate_advancement_trends(
            category=category,
            country=country,
            years_back=request.years_back
        )
        
        return TrendAnalysisResponse(
            category=request.category,
            country=request.country,
            analysis=analysis
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or country: {str(e)}")
    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")

@router.post("/predictions", response_model=PredictionResponse)
async def predict_movement(request: PredictionRequest):
    """Predict visa bulletin movement for the next few months"""
    try:
        category, country = validate_input(request.category, request.country)
        
        prediction = trend_analyzer.predict_next_movement(
            category=category,
            country=country,
            months_ahead=request.months_ahead
        )
        
        return PredictionResponse(
            category=request.category,
            country=request.country,
            prediction=prediction
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or country: {str(e)}")
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/compare", response_model=CategoryComparisonResponse)
async def compare_categories(request: CategoryComparisonRequest):
    """Compare advancement trends across categories for a country"""
    try:
        country = normalize_country_code(request.country)
        categories = [normalize_visa_category(cat) for cat in request.categories]
        
        comparison = trend_analyzer.compare_categories(
            country=country,
            categories=categories,
            years_back=request.years_back
        )
        
        return CategoryComparisonResponse(
            country=request.country,
            comparison=comparison
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or country: {str(e)}")
    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/historical", response_model=HistoricalDataResponse)
async def get_historical_data(
    category: str = Query(..., description="Visa category (e.g., EB2)"),
    country: str = Query(..., description="Country code (e.g., INDIA)"),
    start_year: Optional[int] = Query(None, description="Start year for data"),
    end_year: Optional[int] = Query(None, description="End year for data")
):
    """Get historical visa bulletin data for a category and country"""
    try:
        visa_category, country_code = validate_input(category, country)
        
        history = repository.get_category_history(
            category=visa_category,
            country=country_code,
            start_year=start_year,
            end_year=end_year
        )
        
        # Convert to dictionary format
        historical_data = []
        for data in history:
            historical_data.append({
                "category": data.category.value,
                "country": data.country.value,
                "final_action_date": data.final_action_date.isoformat() if data.final_action_date else None,
                "filing_date": data.filing_date.isoformat() if data.filing_date else None,
                "status": data.status.value if hasattr(data.status, 'value') else data.status,
                "notes": data.notes
            })
        
        return HistoricalDataResponse(
            category=category,
            country=country,
            data_points=len(historical_data),
            historical_data=historical_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or country: {str(e)}")
    except Exception as e:
        logger.error(f"Historical data error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Historical data retrieval failed: {str(e)}")

@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats():
    """Get database statistics and coverage information"""
    try:
        stats = repository.get_statistics()
        
        return DatabaseStatsResponse(
            total_bulletins=stats.get('bulletin_count', 0),
            total_categories=stats.get('category_data_count', 0),
            year_range=stats.get('year_range', 'No data'),
            database_stats=stats
        )
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.get("/categories")
async def get_supported_categories():
    """Get list of supported visa categories"""
    return {
        "employment_based": [cat.value for cat in [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, VisaCategory.EB4, VisaCategory.EB5]],
        "family_based": [cat.value for cat in [VisaCategory.F1, VisaCategory.F2A, VisaCategory.F2B, VisaCategory.F3, VisaCategory.F4]]
    }

@router.get("/countries")
async def get_supported_countries():
    """Get list of supported countries"""
    return {
        "countries": [country.value for country in CountryCode]
    }