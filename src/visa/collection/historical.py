"""
Historical visa bulletin data collection

Core functionality for collecting historical visa bulletin data from 2020-2025,
with support for resumable collection, progress tracking, and error handling.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from ..parser import VisaBulletinParser
from ..repository import VisaBulletinRepository
from ..config import VisaConfig


class HistoricalDataCollector:
    """Main collector class for historical visa bulletin data"""
    
    def __init__(self, config: Optional[VisaConfig] = None):
        self.config = config or VisaConfig()
        self.parser = VisaBulletinParser(self.config)
        self.repository = VisaBulletinRepository()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        # Create data directory if it doesn't exist
        Path("data").mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/collection.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
        
    def collect_historical_data(self, start_year: int, end_year: int, 
                              max_workers: int = 5, verify_urls: bool = True,
                              resume: bool = False) -> dict:
        """
        Collect historical visa bulletin data for specified year range
        
        Args:
            start_year: Starting year for collection
            end_year: Ending year for collection
            max_workers: Number of parallel workers for collection
            verify_urls: Whether to verify URL accessibility before parsing
            resume: Whether to resume from previous failed collection
            
        Returns:
            Dict containing collection results and statistics
        """
        session_id = f"historical_{start_year}_{end_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"🚀 Starting historical data collection: {start_year}-{end_year}")
        self.logger.info(f"📋 Session ID: {session_id}")
        
        try:
            # Check for existing data to avoid duplicates
            existing_bulletins = self.repository.get_bulletins_by_year_range(start_year, end_year)
            existing_count = len(existing_bulletins)
            
            if existing_count > 0 and not resume:
                self.logger.warning(f"⚠️  Found {existing_count} existing bulletins in date range")
                # Note: In a CLI context, this would prompt the user
                # For programmatic use, we'll continue with a warning
                self.logger.info("Continuing with collection - may create duplicates")
            
            # Parse historical bulletins using existing infrastructure
            self.logger.info("🔍 Discovering and parsing bulletins...")
            bulletins = self.parser.parse_historical_bulletins(
                start_year=start_year,
                end_year=end_year,
                verify_urls=verify_urls,
                max_workers=max_workers
            )
            
            if not bulletins:
                self.logger.warning("No bulletins were successfully parsed")
                return {
                    'status': 'completed',
                    'session_id': session_id,
                    'bulletins_collected': 0,
                    'bulletins_stored': 0,
                    'errors': ['No bulletins found or parsed successfully']
                }
            
            self.logger.info(f"✅ Successfully parsed {len(bulletins)} bulletins")
            
            # Convert bulletins to dictionary format for bulk import
            self.logger.info("💾 Storing bulletins in database...")
            bulletin_data = []
            for bulletin in bulletins:
                try:
                    bulletin_dict = bulletin.to_dict()
                    bulletin_data.append(bulletin_dict)
                except Exception as e:
                    self.logger.error(f"Failed to convert bulletin to dict: {e}")
            
            # Bulk import using existing repository method
            import_results = self.repository.bulk_import_bulletins(
                bulletin_data, 
                validate_each=True, 
                stop_on_error=False
            )
            
            # Log detailed results
            self.logger.info("📊 Collection Results:")
            self.logger.info(f"   🔍 Bulletins parsed: {len(bulletins)}")
            self.logger.info(f"   ✅ Successfully stored: {import_results['successful']}")
            self.logger.info(f"   ❌ Failed to store: {import_results['failed']}")
            
            if import_results['errors']:
                self.logger.warning("❌ Import Errors:")
                for error in import_results['errors'][:5]:  # Show first 5 errors
                    self.logger.warning(f"   - {error}")
                if len(import_results['errors']) > 5:
                    self.logger.warning(f"   ... and {len(import_results['errors']) - 5} more errors")
            
            if import_results['warnings']:
                self.logger.info("⚠️  Import Warnings:")
                for warning in import_results['warnings'][:5]:
                    self.logger.info(f"   - {warning}")
            
            # Get database statistics
            stats = self.repository.get_statistics()
            self.logger.info(f"📈 Database Stats: {stats.get('bulletin_count', 0)} total bulletins")
            
            return {
                'status': 'completed',
                'session_id': session_id,
                'bulletins_collected': len(bulletins),
                'bulletins_stored': import_results['successful'],
                'import_results': import_results,
                'database_stats': stats
            }
            
        except KeyboardInterrupt:
            self.logger.info("⏹️  Collection interrupted by user")
            return {'status': 'interrupted', 'session_id': session_id}
            
        except Exception as e:
            self.logger.error(f"💥 Collection failed: {str(e)}")
            return {
                'status': 'failed', 
                'session_id': session_id,
                'error': str(e)
            }
    
    def validate_existing_data(self, start_year: int = None, end_year: int = None) -> dict:
        """Validate existing data in the database"""
        self.logger.info("🔍 Validating existing data...")
        
        # Get bulletins to validate
        if start_year and end_year:
            bulletins = self.repository.get_bulletins_by_year_range(start_year, end_year)
        else:
            bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
        
        validation_results = {
            'total_bulletins': len(bulletins),
            'valid_bulletins': 0,
            'invalid_bulletins': 0,
            'validation_errors': [],
            'data_quality_issues': []
        }
        
        for bulletin in bulletins:
            try:
                # Convert to dict for validation
                bulletin_dict = bulletin.to_dict()
                
                # Use existing validator
                from ..validators import BulletinValidator
                validator = BulletinValidator()
                result = validator.validate_complete_bulletin(bulletin_dict)
                
                if result.is_valid:
                    validation_results['valid_bulletins'] += 1
                else:
                    validation_results['invalid_bulletins'] += 1
                    for error in result.errors:
                        validation_results['validation_errors'].append(
                            f"Bulletin {bulletin.year}-{bulletin.month}: {error}"
                        )
                
                # Check for data quality issues
                if len(bulletin.categories) == 0:
                    validation_results['data_quality_issues'].append(
                        f"Bulletin {bulletin.year}-{bulletin.month}: No category data"
                    )
                    
            except Exception as e:
                validation_results['invalid_bulletins'] += 1
                validation_results['validation_errors'].append(
                    f"Bulletin {bulletin.year}-{bulletin.month}: Validation error - {str(e)}"
                )
        
        # Log validation summary
        self.logger.info("📊 Validation Results:")
        self.logger.info(f"   📋 Total bulletins: {validation_results['total_bulletins']}")
        self.logger.info(f"   ✅ Valid bulletins: {validation_results['valid_bulletins']}")
        self.logger.info(f"   ❌ Invalid bulletins: {validation_results['invalid_bulletins']}")
        
        if validation_results['validation_errors']:
            self.logger.warning("❌ Validation Errors (first 5):")
            for error in validation_results['validation_errors'][:5]:
                self.logger.warning(f"   - {error}")
        
        return validation_results
    
    def get_collection_summary(self) -> dict:
        """Get summary of all collected data"""
        stats = self.repository.get_statistics()
        
        # Get data by year
        year_breakdown = {}
        for year in range(2020, 2026):
            bulletins = self.repository.get_bulletins_by_year_range(year, year)
            year_breakdown[year] = len(bulletins)
        
        return {
            'database_stats': stats,
            'year_breakdown': year_breakdown,
            'collection_coverage': {
                'years_covered': len([y for y, count in year_breakdown.items() if count > 0]),
                'total_months': sum(year_breakdown.values()),
                'expected_months': 12 * (2025 - 2020 + 1),  # 12 months * 6 years
                'coverage_percentage': (sum(year_breakdown.values()) / (12 * 6)) * 100
            }
        }