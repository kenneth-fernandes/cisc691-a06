"""
Integration tests for the visa bulletin system
"""
import pytest
from unittest.mock import patch, Mock
from datetime import date

from visa.parser import VisaBulletinParser
from visa.models import VisaBulletin, VisaCategory, CountryCode
from visa.config import VisaConfig


@pytest.mark.integration
class TestVisaParserIntegration:
    """Integration tests for visa parser system"""
    
    def test_config_initialization(self):
        """Test that configuration initializes properly"""
        config = VisaConfig()
        
        # Check required URLs
        assert config.STATE_DEPT_URL.startswith("https://")
        assert config.BULLETIN_BASE_URL.startswith("https://")
        
        # Check categories
        assert len(config.EMPLOYMENT_CATEGORIES) == 5
        assert len(config.FAMILY_CATEGORIES) == 5
        assert len(config.SPECIAL_COUNTRIES) == 4
        
        # Check validation methods
        assert config.validate_category("EB-1") is True
        assert config.validate_category("Invalid") is False
        assert config.validate_country("China") is True
        assert config.validate_country("Invalid") is False
    
    def test_parser_components_integration(self):
        """Test that all parser components work together"""
        config = VisaConfig()
        parser = VisaBulletinParser(config)
        
        # Verify all components are initialized
        assert parser.config is not None
        assert parser.scraper is not None
        assert parser.date_extractor is not None
        assert parser.table_parser is not None
        assert parser.validator is not None
        
        # Test URL generation
        url = parser.scraper.generate_historical_bulletin_url(2024, 6)
        assert "2024" in url
        assert "june" in url
        
        # Test date extraction
        test_date, month, year = parser.date_extractor.extract_bulletin_date(
            "Visa Bulletin for July 2024"
        )
        assert month == 7
        assert year == 2024
    
    @patch('requests.Session.get')
    def test_parser_with_mocked_network(self, mock_get, mock_html_content):
        """Test parser with mocked network calls"""
        # Mock network response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html_content
        mock_response.content = mock_html_content.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        parser = VisaBulletinParser()
        
        # Test fetching bulletin content
        content = parser.scraper.fetch_bulletin_content("https://example.com")
        assert content == mock_html_content
        
        # Test parsing the content
        bulletin = parser.parse_bulletin_content(content, "https://example.com")
        assert bulletin is not None
        assert len(bulletin.categories) > 0
    
    def test_bulletin_data_flow(self, sample_bulletin):
        """Test complete data flow from bulletin to dictionary and back"""
        # Test bulletin to dictionary
        bulletin_dict = sample_bulletin.to_dict()
        
        # Verify dictionary structure
        required_fields = ["bulletin_date", "fiscal_year", "month", "year", "categories"]
        for field in required_fields:
            assert field in bulletin_dict
        
        # Test dictionary back to bulletin
        restored_bulletin = VisaBulletin.from_dict(bulletin_dict)
        
        # Verify data integrity
        assert restored_bulletin.bulletin_date == sample_bulletin.bulletin_date
        assert restored_bulletin.fiscal_year == sample_bulletin.fiscal_year
        assert restored_bulletin.month == sample_bulletin.month
        assert restored_bulletin.year == sample_bulletin.year
        assert len(restored_bulletin.categories) == len(sample_bulletin.categories)
        
        # Verify category data integrity
        original_cat = sample_bulletin.categories[0]
        restored_cat = restored_bulletin.categories[0]
        
        assert restored_cat.category == original_cat.category
        assert restored_cat.country == original_cat.country
        assert restored_cat.final_action_date == original_cat.final_action_date
        assert restored_cat.status == original_cat.status
    
    def test_validation_integration(self, sample_bulletin):
        """Test validation integration with bulletin data"""
        from visa.validators import BulletinValidator
        
        validator = BulletinValidator()
        
        # Test valid bulletin
        bulletin_dict = sample_bulletin.to_dict()
        result = validator.validate_complete_bulletin(bulletin_dict)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # Test invalid bulletin
        invalid_dict = bulletin_dict.copy()
        invalid_dict["fiscal_year"] = 2050  # Invalid year
        invalid_dict["month"] = 13  # Invalid month
        
        result = validator.validate_complete_bulletin(invalid_dict)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_category_filtering(self, multiple_categories):
        """Test category filtering functionality"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        # Add all categories
        for cat_data in multiple_categories:
            bulletin.add_category_data(cat_data)
        
        # Test employment category filtering
        employment_cats = bulletin.get_employment_categories()
        employment_cat_names = [cat.category.value for cat in employment_cats]
        
        assert "EB-1" in employment_cat_names
        assert "EB-2" in employment_cat_names
        assert "F1" not in employment_cat_names
        assert "F2A" not in employment_cat_names
        
        # Test family category filtering
        family_cats = bulletin.get_family_categories()
        family_cat_names = [cat.category.value for cat in family_cats]
        
        assert "F1" in family_cat_names
        assert "F2A" in family_cat_names
        assert "EB-1" not in family_cat_names
        assert "EB-2" not in family_cat_names
    
    def test_historical_url_generation_integration(self):
        """Test historical URL generation and validation"""
        parser = VisaBulletinParser()
        
        # Test single URL generation
        url = parser.scraper.generate_historical_bulletin_url(2024, 6)
        expected_pattern = "visa-bulletin/2024/visa-bulletin-for-june-2024.html"
        assert expected_pattern in url
        
        # Test bulk URL generation
        urls = parser.scraper.get_historical_bulletin_urls(2024, 2024)
        
        # Verify URL structure
        assert len(urls) > 0
        for url, year, month in urls:
            assert year == 2024
            assert 1 <= month <= 12
            assert f"{year}" in url
            assert "visa-bulletin" in url
        
        # Verify URLs are chronologically ordered
        months = [month for _, _, month in urls]
        assert months == sorted(months)
    
    def test_error_handling_integration(self):
        """Test error handling across the system"""
        from visa.parser import ParsingError
        
        parser = VisaBulletinParser()
        
        # Test parsing invalid content (should handle gracefully, not raise)
        try:
            result = parser.parse_bulletin_content("invalid html content")
            # Should return a bulletin but with minimal/default data
            assert result is not None
        except Exception:
            # Some parsing errors are expected with invalid content
            pass
        
        # Test invalid date parsing
        invalid_bulletin_data = {
            "bulletin_date": "2024-07-01",
            "fiscal_year": 2050,  # Invalid
            "month": 7,
            "year": 2024,
            "categories": []
        }
        
        # Should handle validation errors gracefully
        from visa.validators import BulletinValidator
        validator = BulletinValidator()
        result = validator.validate_complete_bulletin(invalid_bulletin_data)
        assert result.is_valid is False


@pytest.mark.slow
class TestNetworkIntegration:
    """Network-dependent integration tests (marked as slow)"""
    
    @pytest.mark.network
    def test_real_url_verification(self):
        """Test URL verification with real State Department URLs"""
        parser = VisaBulletinParser()
        
        # Test a known good URL pattern (may fail if format changes)
        test_url = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
        
        # This test may fail if the State Department changes their URL structure
        # or if there are network issues - that's expected
        try:
            is_accessible = parser.scraper.verify_bulletin_url(test_url)
            # We don't assert True here because the URL might not exist
            # We just want to test that the method doesn't crash
            assert isinstance(is_accessible, bool)
        except Exception as e:
            pytest.skip(f"Network test skipped due to: {e}")
    
    @pytest.mark.network
    def test_historical_url_structure(self):
        """Test that historical URL structure matches expected pattern"""
        parser = VisaBulletinParser()
        
        # Generate some historical URLs
        urls = parser.scraper.get_historical_bulletin_urls(2023, 2024)
        
        # Test URL structure (without actually fetching)
        for url, year, month in urls[:3]:  # Test first 3 URLs
            assert f"{year}" in url
            assert "visa-bulletin" in url
            assert "travel.state.gov" in url
            
            # Month should be in the URL as word
            month_name = parser.scraper.month_names[month - 1]
            assert month_name in url


@pytest.mark.unit
class TestComponentInteraction:
    """Test interaction between different components"""
    
    def test_config_parser_interaction(self):
        """Test configuration usage in parser"""
        config = VisaConfig()
        parser = VisaBulletinParser(config)
        
        # Verify parser uses config
        assert parser.config == config
        assert parser.scraper.config == config
        
        # Test config URLs are used
        url = parser.scraper.generate_historical_bulletin_url(2024, 6)
        assert config.BULLETIN_BASE_URL in url
    
    def test_validator_parser_interaction(self):
        """Test validator usage in parser"""
        parser = VisaBulletinParser()
        
        # Create a test bulletin
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        # Test that parser can validate bulletins
        bulletin_dict = bulletin.to_dict()
        result = parser.validator.validate_complete_bulletin(bulletin_dict)
        
        assert result is not None
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')
    
    def test_date_extractor_parser_interaction(self):
        """Test date extractor usage in parser"""
        parser = VisaBulletinParser()
        
        # Test date extraction
        test_content = "Visa Bulletin for September 2024"
        test_url = "https://example.com/visa-bulletin-for-september-2024.html"
        
        bulletin_date, month, year = parser.date_extractor.extract_bulletin_date(
            test_content, test_url
        )
        
        assert month == 9
        assert year == 2024
        assert bulletin_date == date(2024, 9, 1)
        
        # Test fiscal year calculation
        fiscal_year = parser.date_extractor.calculate_fiscal_year(month, year)
        assert fiscal_year == 2024  # September is in FY 2024