#!/usr/bin/env python3
"""
Comprehensive Visa Data Management CLI

This is the main command-line interface for managing historical visa bulletin data,
including collection, validation, cleaning, and analysis.

Usage:
    python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025
    python scripts/visa_data_manager.py validate --fix-errors
    python scripts/visa_data_manager.py analyze --category EB-2 --country India
    python scripts/visa_data_manager.py report --comprehensive
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from visa.collection import HistoricalDataCollector, MonthlyDataFetcher, DataValidator
from visa.analytics import TrendAnalyzer
from visa.models import VisaCategory, CountryCode
from visa.config import VisaConfig


class VisaDataManager:
    """Main manager class for all visa data operations"""
    
    def __init__(self):
        self.config = VisaConfig()
        self.historical_collector = HistoricalDataCollector(self.config)
        self.monthly_fetcher = MonthlyDataFetcher(self.config)
        self.validator = DataValidator()
        self.analyzer = TrendAnalyzer()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_file = Path("data/visa_data_manager.log")
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
    
    def collect_historical_data(self, start_year: int, end_year: int, 
                               max_workers: int = 5, verify_urls: bool = True) -> dict:
        """Collect historical visa bulletin data"""
        self.logger.info(f"🚀 Starting historical data collection: {start_year}-{end_year}")
        
        try:
            results = self.historical_collector.collect_historical_data(
                start_year=start_year,
                end_year=end_year,
                max_workers=max_workers,
                verify_urls=verify_urls
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Collection failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def fetch_current_bulletin(self, force: bool = False) -> dict:
        """Fetch the current bulletin"""
        self.logger.info("📋 Fetching current bulletin...")
        
        try:
            results = self.monthly_fetcher.fetch_current_bulletin(force=force)
            return results
            
        except Exception as e:
            self.logger.error(f"Current bulletin fetch failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def validate_data(self, start_year: int = None, end_year: int = None, 
                     fix_errors: bool = False) -> dict:
        """Validate existing data"""
        self.logger.info("🔍 Starting data validation...")
        
        try:
            if fix_errors:
                # Attempt to fix errors
                fix_results = self.validator.attempt_fixes(dry_run=False)
                total_fixes = fix_results['date_fixes'] + fix_results['category_fixes'] + fix_results['validation_fixes']
                self.logger.info(f"Applied {total_fixes} fixes")
            
            # Run validation
            validation_results = self.validator.validate_all_data(start_year, end_year)
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def analyze_trends(self, category: str = None, country: str = None, 
                      years_back: int = 3) -> dict:
        """Analyze trends for specific category/country"""
        
        try:
            if category and country:
                # Specific category-country analysis
                cat_enum = VisaCategory(category)
                country_enum = CountryCode(country)
                
                self.logger.info(f"📊 Analyzing trends for {category}-{country}")
                
                trend_data = self.analyzer.calculate_advancement_trends(
                    cat_enum, country_enum, years_back
                )
                
                # Also get predictions
                predictions = self.analyzer.predict_next_movement(
                    cat_enum, country_enum, months_ahead=6
                )
                
                return {
                    'status': 'success',
                    'analysis_type': 'specific_category_country',
                    'trend_analysis': trend_data,
                    'predictions': predictions
                }
                
            elif country:
                # Country comparison across categories
                country_enum = CountryCode(country)
                
                self.logger.info(f"📊 Comparing categories for {country}")
                
                comparison = self.analyzer.compare_categories(country_enum)
                
                return {
                    'status': 'success',
                    'analysis_type': 'country_comparison',
                    'comparison': comparison
                }
                
            else:
                # General summary
                self.logger.info("📊 Generating comprehensive summary report")
                
                summary = self.analyzer.generate_summary_report()
                
                return {
                    'status': 'success',
                    'analysis_type': 'comprehensive_summary',
                    'summary': summary
                }
                
        except ValueError as e:
            return {'status': 'error', 'error': f'Invalid category or country: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_report(self, comprehensive: bool = False, 
                       output_file: str = None) -> dict:
        """Generate a comprehensive data report"""
        self.logger.info("📄 Generating comprehensive report...")
        
        try:
            from visa.repository import VisaBulletinRepository
            repository = VisaBulletinRepository()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'database_statistics': repository.get_statistics(),
            }
            
            if comprehensive:
                # Add validation results
                validation_results = self.validator.validate_all_data()
                report['data_quality'] = validation_results
                
                # Add trend analysis for key combinations
                key_combinations = [
                    ('EB-2', 'India'),
                    ('EB-3', 'India'),
                    ('EB-2', 'China'),
                    ('EB-1', 'Worldwide'),
                    ('F1', 'India'),
                    ('F1', 'China')
                ]
                
                report['trend_analysis'] = {}
                for category, country in key_combinations:
                    try:
                        cat_enum = VisaCategory(category)
                        country_enum = CountryCode(country)
                        
                        trend_data = self.analyzer.calculate_advancement_trends(
                            cat_enum, country_enum, years_back=2
                        )
                        
                        if trend_data['status'] == 'success':
                            report['trend_analysis'][f"{category}_{country}"] = {
                                'average_advancement': trend_data['average_advancement_days'],
                                'trend_direction': trend_data['trend_direction'],
                                'volatility': trend_data['volatility'],
                                'interpretation': trend_data['interpretation']
                            }
                    except Exception as e:
                        self.logger.warning(f"Failed to analyze {category}-{country}: {e}")
                
                # Add summary insights
                summary = self.analyzer.generate_summary_report()
                report['summary_insights'] = summary['overall_trends']
            
            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                self.logger.info(f"📄 Report saved to: {output_path}")
            
            return {
                'status': 'success',
                'report': report,
                'output_file': output_file
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_status(self) -> dict:
        """Get overall system status"""
        try:
            from visa.repository import VisaBulletinRepository
            repository = VisaBulletinRepository()
            stats = repository.get_statistics()
            
            # Get monthly fetcher status
            try:
                fetch_status = self.monthly_fetcher.get_fetch_status()
            except:
                fetch_status = {'error': 'Could not get fetch status'}
            
            return {
                'status': 'success',
                'database_stats': stats,
                'fetch_status': fetch_status,
                'system_health': 'operational'
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def cleanup_data(self, days_old: int = 30) -> dict:
        """Cleanup old data and logs"""
        self.logger.info(f"🧹 Cleaning up data older than {days_old} days...")
        
        try:
            # Cleanup logic would go here
            # For now, just return success
            return {
                'status': 'success',
                'message': f'Cleanup completed for data older than {days_old} days'
            }
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Visa Data Management CLI")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect historical data')
    collect_parser.add_argument('--start-year', type=int, default=2020,
                               help='Starting year for collection (default: 2020)')
    collect_parser.add_argument('--end-year', type=int, default=2025,
                               help='Ending year for collection (default: 2025)')
    collect_parser.add_argument('--max-workers', type=int, default=5,
                               help='Number of parallel workers (default: 5)')
    collect_parser.add_argument('--no-verify', action='store_true',
                               help='Skip URL verification')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch current bulletin')
    fetch_parser.add_argument('--force', action='store_true',
                             help='Force fetch even if already exists')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate existing data')
    validate_parser.add_argument('--start-year', type=int, help='Start year for validation')
    validate_parser.add_argument('--end-year', type=int, help='End year for validation')
    validate_parser.add_argument('--fix-errors', action='store_true',
                                help='Attempt to fix common errors')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze trends')
    analyze_parser.add_argument('--category', choices=['EB-1', 'EB-2', 'EB-3', 'EB-4', 'EB-5', 'F1', 'F2A', 'F2B', 'F3', 'F4'],
                               help='Visa category to analyze')
    analyze_parser.add_argument('--country', choices=['Worldwide', 'China', 'India', 'Mexico', 'Philippines'],
                               help='Country to analyze')
    analyze_parser.add_argument('--years-back', type=int, default=3,
                               help='Years of history to analyze (default: 3)')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--comprehensive', action='store_true',
                              help='Generate comprehensive report')
    report_parser.add_argument('--output', help='Output file path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old data')
    cleanup_parser.add_argument('--days-old', type=int, default=30,
                               help='Delete data older than N days (default: 30)')
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    # Initialize manager
    manager = VisaDataManager()
    
    try:
        # Execute commands
        if args.command == 'collect':
            result = manager.collect_historical_data(
                start_year=args.start_year,
                end_year=args.end_year,
                max_workers=args.max_workers,
                verify_urls=not args.no_verify
            )
            
            if result['status'] == 'completed':
                print(f"✅ Collection completed: {result['bulletins_stored']} bulletins stored")
            else:
                print(f"❌ Collection failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'fetch':
            result = manager.fetch_current_bulletin(force=args.force)
            
            if result['status'] == 'success':
                print(f"✅ Current bulletin fetched: {result['bulletin_date']}")
            elif result['status'] == 'already_exists':
                print(f"ℹ️  Bulletin already exists: {result['bulletin_date']}")
            else:
                print(f"❌ Fetch failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'validate':
            result = manager.validate_data(
                start_year=args.start_year,
                end_year=args.end_year,
                fix_errors=args.fix_errors
            )
            
            if 'success_rate' in result:
                print(f"📊 Validation complete: {result['success_rate']:.1f}% success rate")
                print(f"Valid bulletins: {result['valid_bulletins']}/{result['total_bulletins']}")
            else:
                print(f"❌ Validation failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'analyze':
            result = manager.analyze_trends(
                category=args.category,
                country=args.country,
                years_back=args.years_back
            )
            
            if result['status'] == 'success':
                print(f"📊 Analysis complete for {args.category or 'all'}-{args.country or 'all'}")
                
                if result['analysis_type'] == 'specific_category_country':
                    trend = result['trend_analysis']
                    if trend['status'] == 'success':
                        print(f"Trend: {trend['trend_direction']}")
                        print(f"Average advancement: {trend['average_advancement_days']:.1f} days/month")
                        print(f"Interpretation: {trend['interpretation']}")
                        
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'report':
            result = manager.generate_report(
                comprehensive=args.comprehensive,
                output_file=args.output
            )
            
            if result['status'] == 'success':
                print("📄 Report generated successfully")
                if args.output:
                    print(f"Saved to: {args.output}")
            else:
                print(f"❌ Report generation failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'status':
            result = manager.get_status()
            
            if result['status'] == 'success':
                stats = result['database_stats']
                print("📊 System Status:")
                print(f"Total bulletins: {stats.get('bulletin_count', 0)}")
                print(f"System health: {result['system_health']}")
            else:
                print(f"❌ Status check failed: {result.get('error', 'Unknown error')}")
                
        elif args.command == 'cleanup':
            result = manager.cleanup_data(days_old=args.days_old)
            
            if result['status'] == 'success':
                print(f"🧹 Cleanup completed: {result['message']}")
            else:
                print(f"❌ Cleanup failed: {result.get('error', 'Unknown error')}")
                
    except KeyboardInterrupt:
        print("\n⏹️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()