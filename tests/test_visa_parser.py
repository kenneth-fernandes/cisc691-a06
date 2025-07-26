"""
Unit tests for visa parser components
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from bs4 import BeautifulSoup

from visa.parser import (
    VisaBulletinScraper, BulletinDateExtractor, BulletinTableParser,
    VisaBulletinParser, ParsingError
)
from visa.models import VisaCategory, CountryCode, BulletinStatus
from visa.config import VisaConfig


class TestParsingError:
    """Test ParsingError exception"""
    
    def test_basic_creation(self):
        """Test creating parsing error"""
        error = ParsingError("Test error")
        assert str(error) == "parsing_error: Test error"
        assert error.message == "Test error"
        assert error.source_url is None
        assert error.error_type == "parsing_error"
    
    def test_with_source_url(self):
        """Test creating parsing error with source URL"""
        error = ParsingError("Test error", "https://example.com", "network_error")
        assert str(error) == "network_error: Test error"
        assert error.source_url == "https://example.com"
        assert error.error_type == "network_error"


class TestVisaBulletinScraper:
    """Test VisaBulletinScraper class"""
    
    def test_initialization(self):
        """Test scraper initialization"""
        scraper = VisaBulletinScraper()
        assert scraper.config is not None
        assert scraper.session is not None
        assert len(scraper.month_names) == 12
    
    def test_generate_historical_bulletin_url(self):
        """Test generating historical bulletin URLs"""
        scraper = VisaBulletinScraper()
        
        url = scraper.generate_historical_bulletin_url(2024, 6)
        expected = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2024/visa-bulletin-for-june-2024.html"
        assert url == expected
        
        url = scraper.generate_historical_bulletin_url(2023, 12)
        expected = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2023/visa-bulletin-for-december-2023.html"
        assert url == expected
    
    def test_generate_historical_bulletin_url_invalid_month(self):
        """Test generating URL with invalid month"""
        scraper = VisaBulletinScraper()
        
        with pytest.raises(ValueError, match="Invalid month"):
            scraper.generate_historical_bulletin_url(2024, 13)
        
        with pytest.raises(ValueError, match="Invalid month"):
            scraper.generate_historical_bulletin_url(2024, 0)
    
    def test_get_historical_bulletin_urls(self):
        """Test getting historical bulletin URLs"""
        scraper = VisaBulletinScraper()
        
        urls = scraper.get_historical_bulletin_urls(2024, 2024)
        
        # Should have up to 12 URLs for 2024 (minus future months)
        assert len(urls) <= 12
        assert all(isinstance(url_data, tuple) and len(url_data) == 3 for url_data in urls)
        
        # Check first URL structure
        url, year, month = urls[0]
        assert year == 2024
        assert month == 1
        assert "2024" in url
        assert "january" in url
    
    def test_get_historical_bulletin_urls_range(self):
        """Test getting URLs for date range"""
        scraper = VisaBulletinScraper()
        
        urls = scraper.get_historical_bulletin_urls(2023, 2024)
        
        # Should have 24 URLs minus future months
        assert len(urls) >= 12  # At least one full year
        
        # Check that URLs are in order
        years = [url_data[1] for url_data in urls]
        months = [url_data[2] for url_data in urls]
        
        assert years[0] == 2023
        assert months[0] == 1
    
    @patch('requests.Session.head')
    def test_verify_bulletin_url_success(self, mock_head):
        """Test URL verification success"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        scraper = VisaBulletinScraper()
        result = scraper.verify_bulletin_url("https://example.com")
        
        assert result is True
        mock_head.assert_called_once()
    
    @patch('requests.Session.head')
    def test_verify_bulletin_url_failure(self, mock_head):
        """Test URL verification failure"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        scraper = VisaBulletinScraper()
        result = scraper.verify_bulletin_url("https://example.com")
        
        assert result is False
    
    @patch('requests.Session.head')
    def test_verify_bulletin_url_exception(self, mock_head):
        """Test URL verification with exception"""
        mock_head.side_effect = Exception("Network error")
        
        scraper = VisaBulletinScraper()
        with pytest.raises(Exception, match="Network error"):
            scraper.verify_bulletin_url("https://example.com")


class TestBulletinDateExtractor:
    """Test BulletinDateExtractor class"""
    
    def test_extract_bulletin_date_from_url(self):
        """Test extracting date from URL"""
        url = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2025/visa-bulletin-for-july-2025.html"
        
        bulletin_date, month, year = BulletinDateExtractor.extract_bulletin_date("", url)
        
        assert bulletin_date == date(2025, 7, 1)  # First day of the bulletin month
        assert month == 7
        assert year == 2025
    
    def test_extract_bulletin_date_from_content(self):
        """Test extracting date from content"""
        content = "Visa Bulletin for July 2024"
        
        bulletin_date, month, year = BulletinDateExtractor.extract_bulletin_date(content)
        
        assert bulletin_date == date(2024, 7, 1)
        assert month == 7
        assert year == 2024
    
    def test_extract_bulletin_date_various_patterns(self):
        """Test extracting dates from various content patterns"""
        test_cases = [
            ("Bulletin for September 2023", (2023, 9)),
            ("December 2024 visa bulletin", (2024, 12)),
            ("bulletin for March 2025", (2025, 3)),
        ]
        
        for content, (expected_year, expected_month) in test_cases:
            bulletin_date, month, year = BulletinDateExtractor.extract_bulletin_date(content)
            
            assert year == expected_year
            assert month == expected_month
            assert bulletin_date == date(expected_year, expected_month, 1)
    
    def test_extract_bulletin_date_fallback(self):
        """Test fallback to current date when extraction fails"""
        bulletin_date, month, year = BulletinDateExtractor.extract_bulletin_date("no date here")
        
        current_date = date.today()
        assert bulletin_date == current_date
        assert month == current_date.month
        assert year == current_date.year
    
    def test_calculate_fiscal_year(self):
        """Test fiscal year calculation"""
        # Fiscal year starts in October
        assert BulletinDateExtractor.calculate_fiscal_year(10, 2023) == 2024
        assert BulletinDateExtractor.calculate_fiscal_year(11, 2023) == 2024
        assert BulletinDateExtractor.calculate_fiscal_year(12, 2023) == 2024
        assert BulletinDateExtractor.calculate_fiscal_year(1, 2024) == 2024
        assert BulletinDateExtractor.calculate_fiscal_year(9, 2024) == 2024


class TestBulletinTableParser:
    """Test BulletinTableParser class"""
    
    def test_parse_html_tables(self, mock_html_content):
        """Test parsing HTML tables"""
        soup = BeautifulSoup(mock_html_content, 'html.parser')
        parser = BulletinTableParser()
        
        categories = parser.parse_html_tables(soup)
        
        assert len(categories) > 0
        
        # Check that we got expected categories
        category_types = [cat.category for cat in categories]
        assert VisaCategory.EB1 in category_types
        assert VisaCategory.EB2 in category_types
        assert VisaCategory.F1 in category_types
    
    def test_find_country_indices(self):
        """Test finding country column indices"""
        headers = ["Category", "Worldwide", "China", "India", "Mexico", "Philippines"]
        
        parser = BulletinTableParser()
        country_indices = parser._find_country_indices(headers)
        
        assert CountryCode.WORLDWIDE in country_indices
        assert CountryCode.CHINA in country_indices
        assert CountryCode.INDIA in country_indices
        assert CountryCode.MEXICO in country_indices
        assert CountryCode.PHILIPPINES in country_indices
        
        assert country_indices[CountryCode.WORLDWIDE] == 1
        assert country_indices[CountryCode.CHINA] == 2
    
    def test_parse_category(self):
        """Test parsing category from text"""
        parser = BulletinTableParser()
        
        test_cases = [
            ("EB-1", VisaCategory.EB1),
            ("EB-2", VisaCategory.EB2),
            ("Employment First Preference", VisaCategory.EB1),
            ("Second Preference", VisaCategory.EB2),
            ("F1", VisaCategory.F1),
            ("F2A", VisaCategory.F2A),
            # Test new Employment-Based category parsing (State Department format)
            ("1ST", VisaCategory.EB1),
            ("2ND", VisaCategory.EB2),
            ("3RD", VisaCategory.EB3),
            ("4TH", VisaCategory.EB4),
            ("5TH", VisaCategory.EB5),
            ("FIRST", VisaCategory.EB1),
            ("SECOND", VisaCategory.EB2),
            ("THIRD", VisaCategory.EB3),
            ("FOURTH", VisaCategory.EB4),
            ("FIFTH", VisaCategory.EB5),
            ("OTHER WORKERS", VisaCategory.EB3),
            ("CERTAIN RELIGIOUS WORKERS", VisaCategory.EB4),
            ("RELIGIOUS WORKERS", VisaCategory.EB4),
            ("UNRESERVED", VisaCategory.EB5),
        ]
        
        for category_text, expected in test_cases:
            result = parser._parse_category(category_text)
            assert result == expected, f"Failed to parse '{category_text}' as {expected}"
        
        # Test invalid category
        result = parser._parse_category("Invalid Category")
        assert result is None
    
    def test_parse_date_cell(self):
        """Test parsing date cells"""
        parser = BulletinTableParser()
        
        # Test Current status
        result = parser._parse_date_cell("C")
        assert result["status"] == BulletinStatus.CURRENT
        
        result = parser._parse_date_cell("CURRENT")
        assert result["status"] == BulletinStatus.CURRENT
        
        # Test Unavailable status
        result = parser._parse_date_cell("U")
        assert result["status"] == BulletinStatus.UNAVAILABLE
        
        # Test State Department date formats (enhanced parsing)
        result = parser._parse_date_cell("15JAN23")
        assert result["final_action_date"] == date(2023, 1, 15)
        assert result["status"] == BulletinStatus.DATE_SPECIFIED
        
        result = parser._parse_date_cell("22APR24")
        assert result["final_action_date"] == date(2024, 4, 22)
        assert result["status"] == BulletinStatus.DATE_SPECIFIED
        
        result = parser._parse_date_cell("01DEC22")
        assert result is not None, "Expected result for 01DEC22 but got None"
        assert "final_action_date" in result, f"Missing final_action_date in result: {result}"
        assert result["final_action_date"] == date(2022, 12, 1)
        assert result["status"] == BulletinStatus.DATE_SPECIFIED
        
        # Test 4-digit year format
        result = parser._parse_date_cell("15JAN2023")
        assert result["final_action_date"] == date(2023, 1, 15)
        assert result["status"] == BulletinStatus.DATE_SPECIFIED
        
        # Test standard date formats
        result = parser._parse_date_cell("01/15/2023")
        assert result["final_action_date"] == date(2023, 1, 15)
        assert result["status"] == BulletinStatus.DATE_SPECIFIED
        
        result = parser._parse_date_cell("2023-06-15")
        assert result["final_action_date"] == date(2023, 6, 15)
        
        # Test edge cases for 2-digit year conversion
        result = parser._parse_date_cell("15JAN49")  # Should be 2049
        assert result["final_action_date"] == date(2049, 1, 15)
        
        result = parser._parse_date_cell("15JAN50")  # Should be 1950
        assert result["final_action_date"] == date(1950, 1, 15)
        
        # Test invalid date
        result = parser._parse_date_cell("invalid date")
        assert result is None
        
        result = parser._parse_date_cell("32JAN23")  # Invalid day
        assert result is None
        
        result = parser._parse_date_cell("15XXX23")  # Invalid month
        assert result is None


class TestVisaBulletinParser:
    """Test VisaBulletinParser class"""
    
    def test_initialization(self):
        """Test parser initialization"""
        parser = VisaBulletinParser()
        
        assert parser.config is not None
        assert parser.scraper is not None
        assert parser.date_extractor is not None
        assert parser.table_parser is not None
        assert parser.validator is not None
    
    def test_parse_bulletin_content(self, mock_html_content):
        """Test parsing bulletin content"""
        parser = VisaBulletinParser()
        
        bulletin = parser.parse_bulletin_content(
            mock_html_content, 
            "https://example.com/visa-bulletin-for-july-2024.html"
        )
        
        assert bulletin is not None
        assert bulletin.bulletin_date == date(2024, 7, 1)
        assert bulletin.fiscal_year == 2024
        assert bulletin.month == 7
        assert bulletin.year == 2024
        assert bulletin.source_url == "https://example.com/visa-bulletin-for-july-2024.html"
        assert len(bulletin.categories) > 0
    
    @patch('visa.parser.VisaBulletinScraper.fetch_bulletin_content')
    @patch('visa.parser.VisaBulletinScraper.verify_bulletin_url')
    def test_parse_bulletin_by_date(self, mock_verify, mock_fetch, mock_html_content):
        """Test parsing bulletin by specific date"""
        mock_verify.return_value = True
        mock_fetch.return_value = mock_html_content
        
        parser = VisaBulletinParser()
        bulletin = parser.parse_bulletin_by_date(2024, 7)
        
        assert bulletin is not None
        assert bulletin.month == 7
        assert bulletin.year == 2024
        
        mock_verify.assert_called_once()
        mock_fetch.assert_called_once()
    
    @patch('visa.parser.VisaBulletinScraper.verify_bulletin_url')
    def test_parse_bulletin_by_date_not_found(self, mock_verify):
        """Test parsing bulletin when URL not found"""
        mock_verify.return_value = False
        
        parser = VisaBulletinParser()
        bulletin = parser.parse_bulletin_by_date(2024, 7)
        
        assert bulletin is None
    
    @pytest.mark.mock
    @patch('visa.parser.VisaBulletinScraper.get_historical_bulletin_urls')
    @patch('visa.parser.VisaBulletinScraper.verify_bulletin_url')
    @patch('visa.parser.VisaBulletinScraper.fetch_bulletin_content')
    def test_parse_historical_bulletins(self, mock_fetch, mock_verify, mock_get_urls, 
                                       mock_html_content, historical_bulletin_urls):
        """Test parsing historical bulletins"""
        mock_get_urls.return_value = historical_bulletin_urls
        mock_verify.return_value = True
        mock_fetch.return_value = mock_html_content
        
        parser = VisaBulletinParser()
        bulletins = parser.parse_historical_bulletins(2024, 2024, max_workers=1)
        
        assert len(bulletins) == 3  # Number of URLs in fixture
        assert all(bulletin.year == 2024 for bulletin in bulletins)
        
        # Check that bulletins are sorted by date
        dates = [bulletin.bulletin_date for bulletin in bulletins]
        assert dates == sorted(dates)
    
    @patch('visa.parser.PyPDF2.PdfReader')
    def test_parse_pdf_bulletin(self, mock_pdf_reader, mock_html_content):
        """Test parsing PDF bulletin"""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Visa Bulletin for July 2024\nEB-1 Current\nEB-2 01/15/2023"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        parser = VisaBulletinParser()
        pdf_content = b"fake pdf content"
        
        bulletin = parser.parse_pdf_bulletin(pdf_content)
        
        assert bulletin is not None
        assert bulletin.month == 7
        assert bulletin.year == 2024
        
        mock_pdf_reader.assert_called_once()


@pytest.mark.integration
class TestParserIntegration:
    """Integration tests for parser components"""
    
    def test_end_to_end_parsing_flow(self, mock_html_content):
        """Test complete parsing flow without network calls"""
        parser = VisaBulletinParser()
        
        # Parse content directly (skip network calls)
        bulletin = parser.parse_bulletin_content(
            mock_html_content,
            "https://example.com/visa-bulletin-for-july-2024.html"
        )
        
        # Verify complete bulletin structure
        assert bulletin is not None
        assert bulletin.bulletin_date is not None
        assert bulletin.fiscal_year > 0
        assert bulletin.source_url is not None
        assert len(bulletin.categories) > 0
        
        # Verify category data structure
        for category in bulletin.categories:
            assert category.category is not None
            assert category.country is not None
            assert category.status is not None
        
        # Test bulletin methods
        employment_cats = bulletin.get_employment_categories()
        family_cats = bulletin.get_family_categories()
        
        assert isinstance(employment_cats, list)
        assert isinstance(family_cats, list)
        
        # Test serialization
        bulletin_dict = bulletin.to_dict()
        assert isinstance(bulletin_dict, dict)
        assert "bulletin_date" in bulletin_dict
        assert "categories" in bulletin_dict
        
        # Test deserialization
        from visa.models import VisaBulletin
        restored_bulletin = VisaBulletin.from_dict(bulletin_dict)
        assert restored_bulletin.bulletin_date == bulletin.bulletin_date
        assert len(restored_bulletin.categories) == len(bulletin.categories)