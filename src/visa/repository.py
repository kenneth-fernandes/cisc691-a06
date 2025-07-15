"""
Repository layer providing high-level CRUD operations for visa bulletin data
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
import logging

from .models import VisaBulletin, CategoryData, PredictionResult, TrendAnalysis, VisaCategory, CountryCode
from .database import VisaDatabase
from .validators import BulletinValidator, DataCleaner, ValidationResult
from .config import VisaConfig

logger = logging.getLogger(__name__)


class VisaBulletinRepository:
    """High-level repository for visa bulletin operations"""
    
    def __init__(self, db_path: str = None):
        """Initialize repository with database connection"""
        self.db = VisaDatabase(db_path)
        self.config = VisaConfig()
    
    def create_bulletin(self, bulletin_data: Dict[str, Any], validate: bool = True) -> Tuple[Optional[VisaBulletin], ValidationResult]:
        """Create a new visa bulletin with validation"""
        validation_result = ValidationResult(True, [], [])
        
        if validate:
            validation_result = BulletinValidator.validate_complete_bulletin(bulletin_data)
            if not validation_result.is_valid:
                logger.error(f"Bulletin validation failed: {validation_result.errors}")
                return None, validation_result
        
        try:
            # Clean the data
            cleaned_data = DataCleaner.clean_bulletin_data(bulletin_data)
            
            # Create bulletin object
            bulletin = VisaBulletin(
                bulletin_date=datetime.fromisoformat(cleaned_data['bulletin_date']).date(),
                fiscal_year=cleaned_data['fiscal_year'],
                month=cleaned_data['month'],
                year=cleaned_data['year'],
                source_url=cleaned_data.get('source_url')
            )
            
            # Add category data
            for cat_data in cleaned_data.get('categories', []):
                category_obj = CategoryData(
                    category=VisaCategory(cat_data['category']),
                    country=CountryCode(cat_data['country']),
                    final_action_date=datetime.fromisoformat(cat_data['final_action_date']).date() if cat_data.get('final_action_date') else None,
                    filing_date=datetime.fromisoformat(cat_data['filing_date']).date() if cat_data.get('filing_date') else None,
                    status=cat_data.get('status', 'DATE'),
                    notes=cat_data.get('notes')
                )
                bulletin.add_category_data(category_obj)
            
            # Save to database
            bulletin_id = self.db.save_bulletin(bulletin)
            logger.info(f"Created bulletin {bulletin_id} for {bulletin.fiscal_year}-{bulletin.month}-{bulletin.year}")
            
            return bulletin, validation_result
            
        except Exception as e:
            logger.error(f"Error creating bulletin: {str(e)}")
            validation_result.add_error(f"Failed to create bulletin: {str(e)}")
            return None, validation_result
    
    def get_bulletin_by_date(self, fiscal_year: int, month: int, year: int) -> Optional[VisaBulletin]:
        """Get a bulletin by its date"""
        try:
            return self.db.get_bulletin(fiscal_year, month, year)
        except Exception as e:
            logger.error(f"Error retrieving bulletin {fiscal_year}-{month}-{year}: {str(e)}")
            return None
    
    def get_bulletins_by_year_range(self, start_year: int, end_year: int = None) -> List[VisaBulletin]:
        """Get all bulletins within a year range"""
        if end_year is None:
            end_year = datetime.now().year
        
        try:
            return self.db.get_bulletins_range(start_year, end_year)
        except Exception as e:
            logger.error(f"Error retrieving bulletins for {start_year}-{end_year}: {str(e)}")
            return []
    
    def get_latest_bulletin(self) -> Optional[VisaBulletin]:
        """Get the most recent bulletin"""
        current_year = datetime.now().year
        bulletins = self.get_bulletins_by_year_range(current_year - 1, current_year)
        
        if not bulletins:
            return None
        
        # Sort by date and return the latest
        bulletins.sort(key=lambda b: (b.year, b.month), reverse=True)
        return bulletins[0]
    
    def update_bulletin(self, bulletin: VisaBulletin) -> bool:
        """Update an existing bulletin"""
        try:
            bulletin.updated_at = datetime.now()
            self.db.save_bulletin(bulletin)
            logger.info(f"Updated bulletin for {bulletin.fiscal_year}-{bulletin.month}-{bulletin.year}")
            return True
        except Exception as e:
            logger.error(f"Error updating bulletin: {str(e)}")
            return False
    
    def delete_bulletin(self, fiscal_year: int, month: int, year: int) -> bool:
        """Delete a bulletin"""
        try:
            success = self.db.delete_bulletin(fiscal_year, month, year)
            if success:
                logger.info(f"Deleted bulletin {fiscal_year}-{month}-{year}")
            return success
        except Exception as e:
            logger.error(f"Error deleting bulletin {fiscal_year}-{month}-{year}: {str(e)}")
            return False
    
    def get_category_history(self, category: VisaCategory, country: CountryCode, 
                           years_back: int = 5) -> List[CategoryData]:
        """Get historical data for a category/country combination"""
        end_year = datetime.now().year
        start_year = end_year - years_back
        
        try:
            return self.db.get_category_history(category, country, start_year, end_year)
        except Exception as e:
            logger.error(f"Error retrieving history for {category.value}-{country.value}: {str(e)}")
            return []
    
    def get_advancement_trends(self, category: VisaCategory, country: CountryCode, 
                             months_back: int = 12) -> Dict[str, Any]:
        """Calculate advancement trends for a category/country"""
        history = self.get_category_history(category, country, years_back=3)
        
        if len(history) < 2:
            return {
                'trend': 'insufficient_data',
                'average_advancement': 0,
                'total_advancement': 0,
                'data_points': len(history)
            }
        
        # Filter to recent months
        recent_history = history[-months_back:] if len(history) > months_back else history
        
        # Calculate advancements between consecutive months
        advancements = []
        for i in range(1, len(recent_history)):
            prev_data = recent_history[i-1]
            curr_data = recent_history[i]
            
            if (prev_data.final_action_date and curr_data.final_action_date and 
                prev_data.status == 'DATE' and curr_data.status == 'DATE'):
                
                days_advancement = (curr_data.final_action_date - prev_data.final_action_date).days
                advancements.append(days_advancement)
        
        if not advancements:
            return {
                'trend': 'no_movement_data',
                'average_advancement': 0,
                'total_advancement': 0,
                'data_points': len(history)
            }
        
        avg_advancement = sum(advancements) / len(advancements)
        total_advancement = sum(advancements)
        
        # Determine trend direction
        if avg_advancement > 10:
            trend = 'advancing'
        elif avg_advancement < -10:
            trend = 'retrogressing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'average_advancement': round(avg_advancement, 2),
            'total_advancement': total_advancement,
            'data_points': len(advancements),
            'advancement_list': advancements
        }
    
    def get_country_comparison(self, category: VisaCategory, target_month: int, target_year: int) -> Dict[str, Any]:
        """Compare a category across all countries for a specific month"""
        comparison = {}
        
        for country in CountryCode:
            bulletin = self.get_bulletin_by_date(target_year, target_month, target_year)
            if bulletin:
                cat_data = bulletin.get_category_data(category, country)
                if cat_data:
                    comparison[country.value] = {
                        'final_action_date': cat_data.final_action_date,
                        'filing_date': cat_data.filing_date,
                        'status': cat_data.status,
                        'formatted_date': cat_data.final_action_date.strftime('%B %d, %Y') if cat_data.final_action_date else cat_data.status
                    }
        
        return comparison
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        try:
            db_stats = self.db.get_database_stats()
            
            # Add additional stats
            latest_bulletin = self.get_latest_bulletin()
            oldest_bulletins = self.get_bulletins_by_year_range(2020, 2025)
            
            stats = {
                **db_stats,
                'latest_bulletin': f"{latest_bulletin.fiscal_year}-{latest_bulletin.month}-{latest_bulletin.year}" if latest_bulletin else "None",
                'oldest_bulletin': f"{oldest_bulletins[0].fiscal_year}-{oldest_bulletins[0].month}-{oldest_bulletins[0].year}" if oldest_bulletins else "None",
                'total_years_covered': len(set(b.year for b in oldest_bulletins)),
                'categories_tracked': len(VisaCategory),
                'countries_tracked': len(CountryCode)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {'error': str(e)}
    
    def bulk_import_bulletins(self, bulletins_data: List[Dict[str, Any]], 
                            validate_each: bool = True, 
                            stop_on_error: bool = False) -> Dict[str, Any]:
        """Import multiple bulletins at once"""
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
        
        for i, bulletin_data in enumerate(bulletins_data):
            try:
                bulletin, validation = self.create_bulletin(bulletin_data, validate_each)
                
                if bulletin:
                    results['successful'] += 1
                    if validation.warnings:
                        results['warnings'].extend([f"Bulletin {i+1}: {w}" for w in validation.warnings])
                else:
                    results['failed'] += 1
                    results['errors'].extend([f"Bulletin {i+1}: {e}" for e in validation.errors])
                    
                    if stop_on_error:
                        break
                        
            except Exception as e:
                results['failed'] += 1
                error_msg = f"Bulletin {i+1}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                
                if stop_on_error:
                    break
        
        logger.info(f"Bulk import completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def search_bulletins(self, **filters) -> List[VisaBulletin]:
        """Search bulletins with various filters"""
        # This is a simple implementation - could be enhanced with more sophisticated filtering
        all_bulletins = self.get_bulletins_by_year_range(
            filters.get('start_year', 2020),
            filters.get('end_year', datetime.now().year)
        )
        
        filtered_bulletins = []
        
        for bulletin in all_bulletins:
            include = True
            
            # Filter by fiscal year
            if 'fiscal_year' in filters and bulletin.fiscal_year != filters['fiscal_year']:
                include = False
            
            # Filter by month
            if 'month' in filters and bulletin.month != filters['month']:
                include = False
            
            # Filter by category (check if bulletin contains this category)
            if 'category' in filters:
                category = VisaCategory(filters['category'])
                has_category = any(cat.category == category for cat in bulletin.categories)
                if not has_category:
                    include = False
            
            # Filter by country
            if 'country' in filters:
                country = CountryCode(filters['country'])
                has_country = any(cat.country == country for cat in bulletin.categories)
                if not has_country:
                    include = False
            
            if include:
                filtered_bulletins.append(bulletin)
        
        return filtered_bulletins