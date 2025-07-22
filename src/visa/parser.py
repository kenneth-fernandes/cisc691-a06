"""
State Department visa bulletin parser for PDF/HTML content
"""
import re
import logging
import requests
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

import pandas as pd
from bs4 import BeautifulSoup, Tag
import PyPDF2
from io import BytesIO

from .models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus
from .config import VisaConfig
from .validators import BulletinValidator


logger = logging.getLogger(__name__)


@dataclass
class ParsingError(Exception):
    """Custom exception for parsing errors"""
    message: str
    source_url: Optional[str] = None
    error_type: str = "parsing_error"
    
    def __str__(self):
        return f"{self.error_type}: {self.message}"


class VisaBulletinScraper:
    """Web scraper for travel.state.gov visa bulletins"""
    
    def __init__(self, config: Optional[VisaConfig] = None):
        self.config = config or VisaConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.month_names = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
    def get_current_bulletin_url(self) -> Optional[str]:
        """Fetch the URL of the current visa bulletin"""
        try:
            response = self.session.get(self.config.STATE_DEPT_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for links to current bulletin
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'visa-bulletin' in href.lower() and any(
                    month in href.lower() for month in 
                    ['january', 'february', 'march', 'april', 'may', 'june',
                     'july', 'august', 'september', 'october', 'november', 'december']
                ):
                    return urljoin(self.config.STATE_DEPT_URL, href)
                    
            return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch bulletin URL: {e}")
            raise ParsingError(f"Network error fetching bulletin URL: {e}")
            
    def fetch_bulletin_content(self, url: str) -> str:
        """Fetch bulletin content from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch bulletin content from {url}: {e}")
            raise ParsingError(f"Network error fetching bulletin: {e}", url)
    
    def generate_historical_bulletin_url(self, year: int, month: int) -> str:
        """Generate historical bulletin URL for given year and month"""
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month: {month}. Must be 1-12.")
        
        month_name = self.month_names[month - 1]
        url = f"{self.config.BULLETIN_BASE_URL}/{year}/visa-bulletin-for-{month_name}-{year}.html"
        return url
    
    def get_historical_bulletin_urls(self, start_year: int, end_year: int) -> List[Tuple[str, int, int]]:
        """Get all historical bulletin URLs for a date range
        
        Returns:
            List of tuples: (url, year, month)
        """
        urls = []
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Don't generate URLs for future dates
                current_date = date.today()
                if year > current_date.year or (year == current_date.year and month > current_date.month):
                    continue
                    
                url = self.generate_historical_bulletin_url(year, month)
                urls.append((url, year, month))
        
        return urls
    
    def verify_bulletin_url(self, url: str) -> bool:
        """Verify if a bulletin URL exists and is accessible"""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False


class BulletinDateExtractor:
    """Extract dates and metadata from bulletin content"""
    
    @staticmethod
    def extract_bulletin_date(content: str, url: Optional[str] = None) -> Tuple[date, int, int]:
        """Extract bulletin date, month, and year from content"""
        # Try URL-based extraction first
        if url:
            date_match = re.search(r'(\d{4})-(\w+)', url)
            if date_match:
                year_str, month_str = date_match.groups()
                try:
                    year = int(year_str)
                    month_map = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_map.get(month_str.lower())
                    if month:
                        bulletin_date = date(year, month, 1)
                        return bulletin_date, month, year
                except ValueError:
                    pass
        
        # Content-based extraction
        patterns = [
            r'(?:for|bulletin)\s+(\w+)\s+(\d{4})',
            r'(\w+)\s+(\d{4})\s+visa\s+bulletin',
            r'bulletin\s+for\s+(\w+)\s+(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                month_str, year_str = match.groups()
                try:
                    year = int(year_str)
                    month_map = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_map.get(month_str.lower())
                    if month:
                        bulletin_date = date(year, month, 1)
                        return bulletin_date, month, year
                except ValueError:
                    continue
        
        # Default to current date if extraction fails
        current_date = date.today()
        logger.warning("Could not extract bulletin date, using current date")
        return current_date, current_date.month, current_date.year
    
    @staticmethod
    def calculate_fiscal_year(month: int, year: int) -> int:
        """Calculate fiscal year from month and year"""
        if month >= 10:  # Oct, Nov, Dec
            return year + 1
        else:  # Jan-Sep
            return year


class BulletinTableParser:
    """Parse visa category tables from bulletin content"""
    
    def __init__(self, validator: Optional[BulletinValidator] = None):
        self.validator = validator or BulletinValidator()
        
    def parse_html_tables(self, soup: BeautifulSoup) -> List[CategoryData]:
        """Parse HTML tables containing visa bulletin data"""
        categories = []
        
        # Find tables containing visa data
        tables = soup.find_all('table')
        
        for table in tables:
            if self._is_visa_table(table):
                categories.extend(self._parse_table(table))
                
        return categories
    
    def _is_visa_table(self, table: Tag) -> bool:
        """Check if table contains visa bulletin data"""
        table_text = table.get_text().lower()
        return any(cat.lower() in table_text for cat in 
                  ['eb-1', 'eb-2', 'eb-3', 'f1', 'f2a', 'f2b', 'f3', 'f4'])
    
    def _parse_table(self, table: Tag) -> List[CategoryData]:
        """Parse individual table for category data"""
        categories = []
        rows = table.find_all('tr')
        
        if len(rows) < 2:
            return categories
            
        # Get headers
        header_row = rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
        
        # Find country columns
        country_indices = self._find_country_indices(headers)
        
        # Parse data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
                
            category_text = cells[0].get_text().strip()
            category = self._parse_category(category_text)
            
            if category:
                for country, col_idx in country_indices.items():
                    if col_idx < len(cells):
                        date_text = cells[col_idx].get_text().strip()
                        parsed_data = self._parse_date_cell(date_text)
                        
                        if parsed_data:
                            cat_data = CategoryData(
                                category=category,
                                country=country,
                                final_action_date=parsed_data.get('final_action_date'),
                                filing_date=parsed_data.get('filing_date'),
                                status=parsed_data.get('status', BulletinStatus.DATE_SPECIFIED)
                            )
                            categories.append(cat_data)
        
        return categories
    
    def _find_country_indices(self, headers: List[str]) -> Dict[CountryCode, int]:
        """Find column indices for each country"""
        country_map = {}
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'worldwide' in header_lower or 'all' in header_lower:
                country_map[CountryCode.WORLDWIDE] = i
            elif 'china' in header_lower:
                country_map[CountryCode.CHINA] = i
            elif 'india' in header_lower:
                country_map[CountryCode.INDIA] = i
            elif 'mexico' in header_lower:
                country_map[CountryCode.MEXICO] = i
            elif 'philippines' in header_lower:
                country_map[CountryCode.PHILIPPINES] = i
                
        return country_map
    
    def _parse_category(self, category_text: str) -> Optional[VisaCategory]:
        """Parse category from text"""
        category_text = category_text.upper().strip()
        
        try:
            # Direct match
            for cat in VisaCategory:
                if cat.value.upper() in category_text:
                    return cat
                    
            # Pattern matching
            if 'EB-1' in category_text or 'FIRST' in category_text:
                return VisaCategory.EB1
            elif 'EB-2' in category_text or 'SECOND' in category_text:
                return VisaCategory.EB2
            elif 'EB-3' in category_text or 'THIRD' in category_text:
                return VisaCategory.EB3
            elif 'EB-4' in category_text or 'FOURTH' in category_text:
                return VisaCategory.EB4
            elif 'EB-5' in category_text or 'FIFTH' in category_text:
                return VisaCategory.EB5
                
        except Exception as e:
            logger.warning(f"Failed to parse category '{category_text}': {e}")
            
        return None
    
    def _parse_date_cell(self, date_text: str) -> Optional[Dict[str, Any]]:
        """Parse date from table cell"""
        date_text = date_text.strip().upper()
        
        if 'C' in date_text or 'CURRENT' in date_text:
            return {'status': BulletinStatus.CURRENT}
        elif 'U' in date_text or 'UNAVAILABLE' in date_text:
            return {'status': BulletinStatus.UNAVAILABLE}
        
        # Try to parse actual dates
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                        year, month, day = map(int, match.groups())
                    else:  # MM/DD/YYYY or MM-DD-YYYY
                        month, day, year = map(int, match.groups())
                    
                    parsed_date = date(year, month, day)
                    return {
                        'final_action_date': parsed_date,
                        'status': BulletinStatus.DATE_SPECIFIED
                    }
                except ValueError:
                    continue
        
        return None


class VisaBulletinParser:
    """Main parser class for State Department visa bulletins"""
    
    def __init__(self, config: Optional[VisaConfig] = None):
        self.config = config or VisaConfig()
        self.scraper = VisaBulletinScraper(self.config)
        self.date_extractor = BulletinDateExtractor()
        self.table_parser = BulletinTableParser()
        self.validator = BulletinValidator()
        
    def parse_current_bulletin(self) -> Optional[VisaBulletin]:
        """Parse the current visa bulletin from State Department website"""
        try:
            # Get current bulletin URL
            bulletin_url = self.scraper.get_current_bulletin_url()
            if not bulletin_url:
                raise ParsingError("Could not find current bulletin URL")
            
            # Fetch content
            content = self.scraper.fetch_bulletin_content(bulletin_url)
            
            # Parse content
            return self.parse_bulletin_content(content, bulletin_url)
            
        except Exception as e:
            logger.error(f"Failed to parse current bulletin: {e}")
            raise ParsingError(f"Failed to parse current bulletin: {e}")
    
    def parse_bulletin_content(self, content: str, source_url: Optional[str] = None) -> VisaBulletin:
        """Parse bulletin content (HTML or text)"""
        try:
            # Extract date information
            bulletin_date, month, year = self.date_extractor.extract_bulletin_date(
                content, source_url
            )
            fiscal_year = self.date_extractor.calculate_fiscal_year(month, year)
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            categories = self.table_parser.parse_html_tables(soup)
            
            # Create bulletin object
            bulletin = VisaBulletin(
                bulletin_date=bulletin_date,
                fiscal_year=fiscal_year,
                month=month,
                year=year,
                source_url=source_url
            )
            
            # Add categories
            for category_data in categories:
                bulletin.add_category_data(category_data)
            
            # Validate bulletin
            validation_result = self.validator.validate_complete_bulletin(bulletin.to_dict())
            if not validation_result.is_valid:
                logger.warning(f"Bulletin validation warnings: {validation_result.errors}")
            
            return bulletin
            
        except Exception as e:
            logger.error(f"Failed to parse bulletin content: {e}")
            raise ParsingError(f"Failed to parse bulletin content: {e}", source_url)
    
    def parse_pdf_bulletin(self, pdf_content: bytes, source_url: Optional[str] = None) -> VisaBulletin:
        """Parse PDF bulletin content"""
        try:
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Parse as text content
            return self.parse_bulletin_content(text_content, source_url)
            
        except Exception as e:
            logger.error(f"Failed to parse PDF bulletin: {e}")
            raise ParsingError(f"Failed to parse PDF bulletin: {e}", source_url)
    
    def parse_historical_bulletins(self, start_year: int, end_year: int, 
                                  verify_urls: bool = True, 
                                  max_workers: int = 5) -> List[VisaBulletin]:
        """Parse historical bulletins for a date range
        
        Args:
            start_year: Starting year for bulletin collection
            end_year: Ending year for bulletin collection  
            verify_urls: Whether to verify URL accessibility before parsing
            max_workers: Maximum concurrent workers for parallel processing
            
        Returns:
            List of successfully parsed VisaBulletin objects
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info(f"Starting historical bulletin collection: {start_year}-{end_year}")
        
        # Get all potential URLs
        bulletin_urls = self.scraper.get_historical_bulletin_urls(start_year, end_year)
        logger.info(f"Found {len(bulletin_urls)} potential bulletin URLs")
        
        # Verify URLs if requested
        if verify_urls:
            logger.info("Verifying URL accessibility...")
            verified_urls = []
            for url, year, month in bulletin_urls:
                if self.scraper.verify_bulletin_url(url):
                    verified_urls.append((url, year, month))
                else:
                    logger.debug(f"URL not accessible: {url}")
            
            bulletin_urls = verified_urls
            logger.info(f"Verified {len(bulletin_urls)} accessible URLs")
        
        # Parse bulletins in parallel
        bulletins = []
        failed_urls = []
        
        def parse_single_bulletin(url_data):
            url, year, month = url_data
            try:
                content = self.scraper.fetch_bulletin_content(url)
                bulletin = self.parse_bulletin_content(content, url)
                logger.info(f"✅ Parsed bulletin: {year}-{month:02d}")
                return bulletin
            except Exception as e:
                logger.warning(f"❌ Failed to parse {url}: {e}")
                failed_urls.append((url, str(e)))
                return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all parsing tasks
            future_to_url = {
                executor.submit(parse_single_bulletin, url_data): url_data 
                for url_data in bulletin_urls
            }
            
            # Collect results
            for future in as_completed(future_to_url):
                result = future.result()
                if result:
                    bulletins.append(result)
        
        # Log summary
        logger.info(f"📊 Historical bulletin parsing complete:")
        logger.info(f"   ✅ Successfully parsed: {len(bulletins)} bulletins")
        logger.info(f"   ❌ Failed to parse: {len(failed_urls)} bulletins")
        
        if failed_urls:
            logger.debug("Failed URLs:")
            for url, error in failed_urls[:5]:  # Show first 5 failures
                logger.debug(f"   {url}: {error}")
            if len(failed_urls) > 5:
                logger.debug(f"   ... and {len(failed_urls) - 5} more failures")
        
        # Sort bulletins by date
        bulletins.sort(key=lambda b: b.bulletin_date)
        
        return bulletins
    
    def parse_bulletin_by_date(self, year: int, month: int) -> Optional[VisaBulletin]:
        """Parse a specific historical bulletin by year and month"""
        try:
            url = self.scraper.generate_historical_bulletin_url(year, month)
            
            # Verify URL exists
            if not self.scraper.verify_bulletin_url(url):
                logger.warning(f"Bulletin not found for {year}-{month:02d}")
                return None
            
            # Fetch and parse content
            content = self.scraper.fetch_bulletin_content(url)
            bulletin = self.parse_bulletin_content(content, url)
            
            logger.info(f"✅ Successfully parsed bulletin for {year}-{month:02d}")
            return bulletin
            
        except Exception as e:
            logger.error(f"Failed to parse bulletin for {year}-{month:02d}: {e}")
            raise ParsingError(f"Failed to parse bulletin for {year}-{month:02d}: {e}")