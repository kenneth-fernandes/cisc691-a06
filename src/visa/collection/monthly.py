"""
Monthly visa bulletin data fetcher

Core functionality for automatically fetching the latest visa bulletin data 
and managing monthly updates with status tracking.
"""

import logging
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any

from ..parser import VisaBulletinParser
from ..repository import VisaBulletinRepository
from ..config import VisaConfig


class MonthlyDataFetcher:
    """Automated monthly visa bulletin data fetcher"""
    
    def __init__(self, config: Optional[VisaConfig] = None):
        self.config = config or VisaConfig()
        self.parser = VisaBulletinParser(self.config)
        self.repository = VisaBulletinRepository()
        self.logger = self._setup_logging()
        self.status_file = Path("data/monthly_fetch_status.json")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_file = Path("data/monthly_fetch.log")
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
    
    def _load_status(self) -> Dict[str, Any]:
        """Load previous fetch status"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load status file: {e}")
        
        return {
            'last_check': None,
            'last_successful_fetch': None,
            'last_bulletin_date': None,
            'consecutive_failures': 0,
            'total_fetches': 0,
            'total_successes': 0
        }
    
    def _save_status(self, status: Dict[str, Any]):
        """Save current fetch status"""
        try:
            self.status_file.parent.mkdir(exist_ok=True)
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save status file: {e}")
    
    def fetch_current_bulletin(self, force: bool = False) -> Dict[str, Any]:
        """
        Fetch the current visa bulletin
        
        Args:
            force: Force fetch even if already collected
            
        Returns:
            Dict containing fetch results
        """
        status = self._load_status()
        status['last_check'] = datetime.now().isoformat()
        status['total_fetches'] += 1
        
        self.logger.info("🔍 Fetching current visa bulletin...")
        
        try:
            # Parse current bulletin using existing infrastructure
            bulletin = self.parser.parse_current_bulletin()
            
            if not bulletin:
                self.logger.warning("❌ No current bulletin found")
                status['consecutive_failures'] += 1
                self._save_status(status)
                return {
                    'status': 'no_bulletin_found',
                    'message': 'No current bulletin could be fetched'
                }
            
            bulletin_date_str = bulletin.bulletin_date.isoformat()
            self.logger.info(f"📋 Found bulletin for: {bulletin_date_str}")
            
            # Check if we already have this bulletin
            existing_bulletin = self.repository.get_bulletin_by_date(
                bulletin.fiscal_year, bulletin.month, bulletin.year
            )
            
            if existing_bulletin and not force:
                self.logger.info("ℹ️  Bulletin already exists in database")
                status['consecutive_failures'] = 0  # Reset failure count
                self._save_status(status)
                return {
                    'status': 'already_exists',
                    'bulletin_date': bulletin_date_str,
                    'message': f'Bulletin for {bulletin_date_str} already in database'
                }
            
            # Store the bulletin
            self.logger.info("💾 Storing bulletin in database...")
            
            bulletin_dict = bulletin.to_dict()
            created_bulletin, validation_result = self.repository.create_bulletin(
                bulletin_dict, validate=True
            )
            
            if created_bulletin:
                self.logger.info("✅ Successfully stored current bulletin")
                status['last_successful_fetch'] = datetime.now().isoformat()
                status['last_bulletin_date'] = bulletin_date_str
                status['consecutive_failures'] = 0
                status['total_successes'] += 1
                
                # Log bulletin details
                self.logger.info(f"📊 Bulletin Details:")
                self.logger.info(f"   📅 Date: {bulletin.bulletin_date}")
                self.logger.info(f"   🏛️  Fiscal Year: {bulletin.fiscal_year}")
                self.logger.info(f"   📋 Categories: {len(bulletin.categories)}")
                self.logger.info(f"   🌐 Source: {bulletin.source_url}")
                
                if validation_result.warnings:
                    self.logger.warning("⚠️  Validation warnings:")
                    for warning in validation_result.warnings:
                        self.logger.warning(f"   - {warning}")
                
                self._save_status(status)
                
                return {
                    'status': 'success',
                    'bulletin_date': bulletin_date_str,
                    'categories_count': len(bulletin.categories),
                    'source_url': bulletin.source_url,
                    'validation_warnings': validation_result.warnings
                }
            else:
                self.logger.error("❌ Failed to store bulletin")
                status['consecutive_failures'] += 1
                self._save_status(status)
                
                return {
                    'status': 'storage_failed',
                    'bulletin_date': bulletin_date_str,
                    'validation_errors': validation_result.errors
                }
                
        except Exception as e:
            self.logger.error(f"💥 Error fetching bulletin: {str(e)}")
            status['consecutive_failures'] += 1
            self._save_status(status)
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_for_updates(self) -> Dict[str, Any]:
        """Check if there are new bulletins available without fetching"""
        self.logger.info("🔍 Checking for bulletin updates...")
        
        try:
            # Get current bulletin URL
            current_url = self.parser.scraper.get_current_bulletin_url()
            
            if not current_url:
                return {
                    'status': 'no_url_found',
                    'message': 'Could not find current bulletin URL'
                }
            
            # Extract date from URL or content
            try:
                content = self.parser.scraper.fetch_bulletin_content(current_url)
                bulletin_date, month, year = self.parser.date_extractor.extract_bulletin_date(
                    content, current_url
                )
                
                # Check if we have this bulletin
                existing_bulletin = self.repository.get_bulletin_by_date(
                    self.parser.date_extractor.calculate_fiscal_year(month, year),
                    month, year
                )
                
                status = self._load_status()
                
                return {
                    'status': 'check_complete',
                    'current_bulletin_date': bulletin_date.isoformat(),
                    'current_bulletin_url': current_url,
                    'already_collected': existing_bulletin is not None,
                    'last_check': status.get('last_check'),
                    'last_successful_fetch': status.get('last_successful_fetch')
                }
                
            except Exception as e:
                self.logger.warning(f"Could not extract date from bulletin: {e}")
                return {
                    'status': 'date_extraction_failed',
                    'current_bulletin_url': current_url,
                    'error': str(e)
                }
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_fetch_status(self) -> Dict[str, Any]:
        """Get current fetch status and statistics"""
        status = self._load_status()
        
        # Get latest bulletin in database
        latest_bulletin = self.repository.get_latest_bulletin()
        
        # Calculate success rate
        success_rate = (status['total_successes'] / status['total_fetches'] * 100) if status['total_fetches'] > 0 else 0
        
        return {
            'fetch_statistics': {
                'total_fetches': status['total_fetches'],
                'total_successes': status['total_successes'],
                'success_rate': round(success_rate, 2),
                'consecutive_failures': status['consecutive_failures']
            },
            'last_activity': {
                'last_check': status['last_check'],
                'last_successful_fetch': status['last_successful_fetch'],
                'last_bulletin_date': status['last_bulletin_date']
            },
            'database_status': {
                'latest_bulletin': f"{latest_bulletin.bulletin_date}" if latest_bulletin else None,
                'total_bulletins': self.repository.get_statistics().get('bulletin_count', 0)
            }
        }
    
    def generate_cron_schedule(self) -> str:
        """Generate cron schedule for monthly fetching"""
        # Run on the 15th of each month at 2 AM (after most bulletins are published)
        return """
# Add this to your crontab (crontab -e) to automatically fetch monthly bulletins
# Runs on the 15th of each month at 2:00 AM
0 2 15 * * /usr/bin/python3 /path/to/scripts/monthly_fetcher.py >> /var/log/visa_bulletin_fetch.log 2>&1

# Alternative: Run daily at 6 AM to catch updates as soon as they're published
0 6 * * * /usr/bin/python3 /path/to/scripts/monthly_fetcher.py >> /var/log/visa_bulletin_fetch.log 2>&1

# For testing: Run every hour
0 * * * * /usr/bin/python3 /path/to/scripts/monthly_fetcher.py >> /var/log/visa_bulletin_fetch.log 2>&1
"""