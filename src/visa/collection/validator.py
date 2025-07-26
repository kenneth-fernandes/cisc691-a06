"""
Data validation and quality management

Core functionality for validating existing visa bulletin data,
identifying inconsistencies, and providing data quality reports.
"""

import logging
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

from ..repository import VisaBulletinRepository
from ..validators import BulletinValidator, DateValidator, ValidationResult
from ..models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus


class DataValidator:
    """Comprehensive data validation and cleaning utility"""
    
    def __init__(self):
        self.repository = VisaBulletinRepository()
        self.bulletin_validator = BulletinValidator()
        self.date_validator = DateValidator()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_file = Path("data/validation.log")
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def validate_all_data(self, start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Validate all bulletins in the database"""
        self.logger.info("🔍 Starting comprehensive data validation...")
        
        # Get bulletins to validate
        if start_year and end_year:
            bulletins = self.repository.get_bulletins_by_year_range(start_year, end_year)
            scope = f"{start_year}-{end_year}"
        else:
            bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
            scope = "all data"
        
        self.logger.info(f"📊 Validating {scope}: {len(bulletins)} bulletins")
        
        validation_results = {
            'scope': scope,
            'total_bulletins': len(bulletins),
            'valid_bulletins': 0,
            'invalid_bulletins': 0,
            'bulletins_with_warnings': 0,
            'validation_errors': [],
            'validation_warnings': [],
            'data_quality_issues': [],
            'missing_data_issues': [],
            'date_inconsistencies': [],
            'category_coverage': defaultdict(int),
            'country_coverage': defaultdict(int),
            'monthly_coverage': defaultdict(int)
        }
        
        for i, bulletin in enumerate(bulletins):
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{len(bulletins)} bulletins validated")
            
            try:
                # Validate bulletin structure
                bulletin_dict = bulletin.to_dict()
                result = self.bulletin_validator.validate_complete_bulletin(bulletin_dict)
                
                bulletin_id = f"{bulletin.year}-{bulletin.month:02d}"
                
                if result.is_valid:
                    validation_results['valid_bulletins'] += 1
                else:
                    validation_results['invalid_bulletins'] += 1
                    for error in result.errors:
                        validation_results['validation_errors'].append(f"{bulletin_id}: {error}")
                
                if result.warnings:
                    validation_results['bulletins_with_warnings'] += 1
                    for warning in result.warnings:
                        validation_results['validation_warnings'].append(f"{bulletin_id}: {warning}")
                
                # Check data quality issues
                self._check_data_quality(bulletin, validation_results)
                
                # Check coverage
                self._update_coverage_stats(bulletin, validation_results)
                
            except Exception as e:
                bulletin_id = f"{bulletin.year}-{bulletin.month:02d}" if hasattr(bulletin, 'year') else f"bulletin-{i}"
                validation_results['invalid_bulletins'] += 1
                validation_results['validation_errors'].append(f"{bulletin_id}: Validation exception - {str(e)}")
        
        # Calculate summary statistics
        validation_results['success_rate'] = (
            validation_results['valid_bulletins'] / validation_results['total_bulletins'] * 100
        ) if validation_results['total_bulletins'] > 0 else 0
        
        # Log summary
        self._log_validation_summary(validation_results)
        
        return validation_results
    
    def _check_data_quality(self, bulletin: VisaBulletin, results: Dict[str, Any]):
        """Check for data quality issues in a bulletin"""
        bulletin_id = f"{bulletin.year}-{bulletin.month:02d}"
        
        # Check for missing category data
        if len(bulletin.categories) == 0:
            results['data_quality_issues'].append(f"{bulletin_id}: No category data")
        
        # Check for incomplete category data
        categories_with_dates = 0
        for cat_data in bulletin.categories:
            if cat_data.final_action_date:
                categories_with_dates += 1
            
            # Check for inconsistent date formats
            if cat_data.final_action_date and cat_data.filing_date:
                if cat_data.final_action_date > cat_data.filing_date:
                    results['date_inconsistencies'].append(
                        f"{bulletin_id}: Final action date after filing date for {cat_data.category.value}-{cat_data.country.value}"
                    )
        
        # Check if most categories are missing dates
        if categories_with_dates < len(bulletin.categories) * 0.5:
            results['missing_data_issues'].append(
                f"{bulletin_id}: {len(bulletin.categories) - categories_with_dates}/{len(bulletin.categories)} categories missing dates"
            )
        
        # Check bulletin date consistency
        if bulletin.bulletin_date.year != bulletin.year:
            results['date_inconsistencies'].append(
                f"{bulletin_id}: Bulletin date year ({bulletin.bulletin_date.year}) doesn't match year field ({bulletin.year})"
            )
        
        if bulletin.bulletin_date.month != bulletin.month:
            results['date_inconsistencies'].append(
                f"{bulletin_id}: Bulletin date month ({bulletin.bulletin_date.month}) doesn't match month field ({bulletin.month})"
            )
    
    def _update_coverage_stats(self, bulletin: VisaBulletin, results: Dict[str, Any]):
        """Update coverage statistics"""
        # Monthly coverage
        month_key = f"{bulletin.year}-{bulletin.month:02d}"
        results['monthly_coverage'][month_key] += 1
        
        # Category and country coverage
        for cat_data in bulletin.categories:
            results['category_coverage'][cat_data.category.value] += 1
            results['country_coverage'][cat_data.country.value] += 1
    
    def _log_validation_summary(self, results: Dict[str, Any]):
        """Log validation summary"""
        self.logger.info("\n📊 Validation Summary:")
        self.logger.info(f"   📋 Total bulletins: {results['total_bulletins']}")
        self.logger.info(f"   ✅ Valid bulletins: {results['valid_bulletins']}")
        self.logger.info(f"   ❌ Invalid bulletins: {results['invalid_bulletins']}")
        self.logger.info(f"   ⚠️  Bulletins with warnings: {results['bulletins_with_warnings']}")
        self.logger.info(f"   📈 Success rate: {results['success_rate']:.1f}%")
        
        if results['validation_errors']:
            self.logger.warning(f"\n❌ Top Validation Errors:")
            for error in results['validation_errors'][:5]:
                self.logger.warning(f"   - {error}")
            if len(results['validation_errors']) > 5:
                self.logger.warning(f"   ... and {len(results['validation_errors']) - 5} more errors")
        
        if results['data_quality_issues']:
            self.logger.info(f"\n⚠️  Data Quality Issues:")
            for issue in results['data_quality_issues'][:5]:
                self.logger.info(f"   - {issue}")
    
    def generate_detailed_report(self, start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Generate a detailed data quality report"""
        self.logger.info("📝 Generating detailed data quality report...")
        
        validation_results = self.validate_all_data(start_year, end_year)
        
        # Additional analysis
        report = {
            'validation_summary': validation_results,
            'coverage_analysis': self._analyze_coverage(validation_results),
            'data_completeness': self._analyze_completeness(),
            'temporal_analysis': self._analyze_temporal_patterns(),
            'recommendations': self._generate_recommendations(validation_results)
        }
        
        # Save report to file
        report_file = Path(f"data/data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📄 Report saved to: {report_file}")
        
        return report
    
    def _analyze_coverage(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data coverage"""
        return {
            'category_coverage': dict(validation_results['category_coverage']),
            'country_coverage': dict(validation_results['country_coverage']),
            'monthly_coverage': dict(validation_results['monthly_coverage']),
            'missing_months': self._find_missing_months(),
            'coverage_gaps': self._identify_coverage_gaps()
        }
    
    def _analyze_completeness(self) -> Dict[str, Any]:
        """Analyze data completeness"""
        all_bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
        
        completeness = {
            'total_bulletins': len(all_bulletins),
            'bulletins_with_categories': 0,
            'avg_categories_per_bulletin': 0,
            'bulletins_with_all_countries': 0,
            'completeness_by_year': defaultdict(dict)
        }
        
        total_categories = 0
        
        for bulletin in all_bulletins:
            year = bulletin.year
            
            if bulletin.categories:
                completeness['bulletins_with_categories'] += 1
                total_categories += len(bulletin.categories)
                
                # Check if all countries are represented
                countries_present = set(cat.country for cat in bulletin.categories)
                if len(countries_present) >= 4:  # Expecting at least 4 countries
                    completeness['bulletins_with_all_countries'] += 1
            
            # Year-specific analysis
            if year not in completeness['completeness_by_year']:
                completeness['completeness_by_year'][year] = {
                    'bulletins': 0,
                    'with_categories': 0,
                    'avg_categories': 0
                }
            
            completeness['completeness_by_year'][year]['bulletins'] += 1
            if bulletin.categories:
                completeness['completeness_by_year'][year]['with_categories'] += 1
        
        # Calculate averages
        if completeness['bulletins_with_categories'] > 0:
            completeness['avg_categories_per_bulletin'] = total_categories / completeness['bulletins_with_categories']
        
        return completeness
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in the data"""
        all_bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
        
        patterns = {
            'bulletins_by_month': defaultdict(int),
            'bulletins_by_year': defaultdict(int),
            'data_gaps': [],
            'publication_consistency': {}
        }
        
        for bulletin in all_bulletins:
            patterns['bulletins_by_month'][bulletin.month] += 1
            patterns['bulletins_by_year'][bulletin.year] += 1
        
        # Identify gaps (months with no bulletins)
        for year in range(2020, 2026):
            for month in range(1, 13):
                bulletins_for_month = [b for b in all_bulletins if b.year == year and b.month == month]
                if not bulletins_for_month:
                    patterns['data_gaps'].append(f"{year}-{month:02d}")
        
        return patterns
    
    def _find_missing_months(self) -> List[str]:
        """Find months with missing bulletin data"""
        all_bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
        existing_months = set(f"{b.year}-{b.month:02d}" for b in all_bulletins)
        
        missing_months = []
        for year in range(2020, 2026):
            for month in range(1, 13):
                # Don't flag future months as missing
                if year == 2025 and month > 12:
                    continue
                    
                month_key = f"{year}-{month:02d}"
                if month_key not in existing_months:
                    missing_months.append(month_key)
        
        return missing_months
    
    def _identify_coverage_gaps(self) -> List[str]:
        """Identify significant coverage gaps"""
        gaps = []
        missing_months = self._find_missing_months()
        
        if len(missing_months) > 10:
            gaps.append(f"Missing {len(missing_months)} months of data")
        
        # Check for consecutive missing months
        consecutive_missing = []
        for i, month in enumerate(missing_months):
            if i == 0 or month not in consecutive_missing:
                consecutive_missing = [month]
            else:
                consecutive_missing.append(month)
                
            if len(consecutive_missing) >= 3:
                gaps.append(f"Consecutive missing months: {consecutive_missing[0]} to {consecutive_missing[-1]}")
        
        return gaps
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if validation_results['success_rate'] < 90:
            recommendations.append("Overall data quality is below 90%. Consider re-parsing problematic bulletins.")
        
        if len(validation_results['date_inconsistencies']) > 0:
            recommendations.append("Fix date inconsistencies between bulletin dates and metadata.")
        
        if len(validation_results['missing_data_issues']) > 5:
            recommendations.append("Investigate bulletins with missing category data.")
        
        missing_months = self._find_missing_months()
        if len(missing_months) > 5:
            recommendations.append(f"Fill {len(missing_months)} missing months of data through re-collection.")
        
        if validation_results['invalid_bulletins'] > validation_results['total_bulletins'] * 0.1:
            recommendations.append("More than 10% of bulletins are invalid. Review parsing logic.")
        
        return recommendations
    
    def attempt_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """Attempt to fix common data issues"""
        self.logger.info(f"🔧 Attempting data fixes (dry_run={dry_run})...")
        
        fixes_applied = {
            'date_fixes': 0,
            'category_fixes': 0,
            'validation_fixes': 0,
            'errors': []
        }
        
        all_bulletins = self.repository.get_bulletins_by_year_range(2020, 2025)
        
        for bulletin in all_bulletins:
            try:
                modified = False
                
                # Fix date inconsistencies
                if bulletin.bulletin_date.year != bulletin.year or bulletin.bulletin_date.month != bulletin.month:
                    if not dry_run:
                        # Correct the bulletin date based on year/month fields
                        bulletin.bulletin_date = date(bulletin.year, bulletin.month, 1)
                        modified = True
                    fixes_applied['date_fixes'] += 1
                
                # Save changes if not dry run
                if modified and not dry_run:
                    self.repository.update_bulletin(bulletin)
                    
            except Exception as e:
                fixes_applied['errors'].append(f"Error fixing bulletin {bulletin.year}-{bulletin.month}: {str(e)}")
        
        total_fixes = fixes_applied['date_fixes'] + fixes_applied['category_fixes'] + fixes_applied['validation_fixes']
        self.logger.info(f"🔧 Fixes applied: {total_fixes}")
        
        return fixes_applied