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
from api.utils.cache import cache_response, CACHE_PRESETS, cache_manager, CacheStats
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
        
        # The repository method only takes years_back parameter
        if start_year:
            from datetime import datetime
            current_year = datetime.now().year
            years_back = current_year - start_year
        else:
            years_back = 5  # default
            
        history = repository.get_category_history(
            category=visa_category,
            country=country_code,
            years_back=years_back
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
@cache_response(ttl=CACHE_PRESETS["very_long"], prefix="categories")
async def get_supported_categories():
    """Get list of supported visa categories"""
    return {
        "employment_based": [cat.value for cat in [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, VisaCategory.EB4, VisaCategory.EB5]],
        "family_based": [cat.value for cat in [VisaCategory.F1, VisaCategory.F2A, VisaCategory.F2B, VisaCategory.F3, VisaCategory.F4]]
    }

@router.get("/countries")
@cache_response(ttl=CACHE_PRESETS["very_long"], prefix="countries")
async def get_supported_countries():
    """Get list of supported countries"""
    return {
        "countries": [country.value for country in CountryCode]
    }

@router.get("/bulletins")
@cache_response(ttl=CACHE_PRESETS["long"], prefix="bulletins")
async def get_all_bulletins(start_year: int = Query(2020), end_year: int = Query(None)):
    """Get all visa bulletins within year range"""
    try:
        if end_year is None:
            from datetime import datetime
            end_year = datetime.now().year
        
        bulletins = repository.get_bulletins_by_year_range(start_year, end_year)
        
        # Convert to simple dict format for JSON response
        bulletin_list = []
        for bulletin in bulletins:
            bulletin_list.append({
                "fiscal_year": bulletin.fiscal_year,
                "month": bulletin.month,
                "year": bulletin.year,
                "bulletin_date": bulletin.bulletin_date.isoformat() if bulletin.bulletin_date else None,
                "source_url": bulletin.source_url,
                "categories_count": len(bulletin.categories)
            })
        
        return {
            "bulletins": bulletin_list,
            "count": len(bulletin_list),
            "year_range": f"{start_year}-{end_year}"
        }
    except Exception as e:
        logger.error(f"Get bulletins error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bulletins: {str(e)}")

@router.get("/bulletins/{year}/{month}")
@cache_response(ttl=CACHE_PRESETS["very_long"], prefix="bulletin_detail")
async def get_bulletin_by_date(year: int, month: int):
    """Get specific visa bulletin by year and month"""
    try:
        # The repository method expects (fiscal_year, month, year) but we'll use year as both fiscal_year and year
        bulletin = repository.get_bulletin_by_date(year, month, year)
        if not bulletin:
            raise HTTPException(status_code=404, detail=f"No bulletin found for {year}/{month}")
        
        # Convert to dict format for JSON response
        bulletin_data = {
            "fiscal_year": bulletin.fiscal_year,
            "month": bulletin.month,
            "year": bulletin.year,
            "bulletin_date": bulletin.bulletin_date.isoformat() if bulletin.bulletin_date else None,
            "source_url": bulletin.source_url,
            "categories": []
        }
        
        for cat in bulletin.categories:
            bulletin_data["categories"].append({
                "category": cat.category.value,
                "country": cat.country.value,
                "final_action_date": cat.final_action_date.isoformat() if cat.final_action_date else None,
                "filing_date": cat.filing_date.isoformat() if cat.filing_date else None,
                "status": cat.status,
                "notes": cat.notes
            })
        
        return bulletin_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get bulletin error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bulletin: {str(e)}")

# Cache management endpoints
@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics and information"""
    return CacheStats.get_cache_info()

@router.delete("/cache/clear")
async def clear_cache():
    """Clear all API cache entries"""
    if cache_manager.clear_all():
        logger.info("Cache cleared successfully")
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.delete("/cache/invalidate/{pattern}")
async def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    from api.utils.cache import invalidate_cache_pattern
    deleted_count = invalidate_cache_pattern(pattern)
    return {
        "message": f"Invalidated {deleted_count} cache entries",
        "pattern": pattern,
        "deleted_count": deleted_count
    }