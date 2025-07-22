"""
Unit tests for visa validators
"""
import pytest
from datetime import date
from visa.validators import (
    DateValidator, CategoryValidator, CountryValidator, BulletinValidator,
    DataCleaner, ValidationResult
)
from visa.models import VisaCategory, CountryCode


class TestValidationResult:
    """Test ValidationResult class"""
    
    def test_creation(self):
        """Test creating validation result"""
        result = ValidationResult(True, [], [])
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_add_error(self):
        """Test adding error makes result invalid"""
        result = ValidationResult(True, [], [])
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding warning keeps result valid"""
        result = ValidationResult(True, [], [])
        result.add_warning("Test warning")
        
        assert result.is_valid is True
        assert "Test warning" in result.warnings


class TestDateValidator:
    """Test DateValidator class"""
    
    def test_parse_valid_dates(self):
        """Test parsing various valid date formats"""
        test_cases = [
            ("01/15/2023", date(2023, 1, 15)),
            ("1/5/2023", date(2023, 1, 5)),
            ("12-25-2023", date(2023, 12, 25)),
            ("2023-06-15", date(2023, 6, 15)),
            ("01.15.2023", date(2023, 1, 15)),
        ]
        
        for date_str, expected_date in test_cases:
            parsed_date = DateValidator.parse_date(date_str)
            assert parsed_date == expected_date, f"Failed to parse {date_str}"
    
    def test_parse_special_statuses(self):
        """Test parsing special status codes"""
        special_statuses = ["C", "CURRENT", "U", "UNAVAILABLE", "c", "u"]
        
        for status in special_statuses:
            parsed_date = DateValidator.parse_date(status)
            assert parsed_date is None
    
    def test_parse_invalid_dates(self):
        """Test parsing invalid date strings"""
        invalid_dates = [
            "invalid",
            "13/01/2023",  # Invalid month
            "01/32/2023",  # Invalid day
            "2023-13-01",  # Invalid month
            "",
            None
        ]
        
        for invalid_date in invalid_dates:
            parsed_date = DateValidator.parse_date(invalid_date)
            assert parsed_date is None, f"Should not parse {invalid_date}"
    
    def test_validate_date_range(self):
        """Test date range validation"""
        # Valid dates
        assert DateValidator.validate_date_range(date(2023, 6, 15)) is True
        assert DateValidator.validate_date_range(date(2025, 1, 1)) is True
        assert DateValidator.validate_date_range(None) is True  # None is acceptable
        
        # Invalid dates
        assert DateValidator.validate_date_range(date(1999, 1, 1)) is False
        assert DateValidator.validate_date_range(date(2031, 1, 1)) is False
    
    def test_format_date_for_display(self):
        """Test date formatting for display"""
        test_date = date(2023, 6, 15)
        formatted = DateValidator.format_date_for_display(test_date)
        assert formatted == "June 15, 2023"
        
        # Test None date
        formatted_none = DateValidator.format_date_for_display(None)
        assert formatted_none == "Not Available"


class TestCategoryValidator:
    """Test CategoryValidator class"""
    
    def test_normalize_standard_categories(self):
        """Test normalizing standard category formats"""
        test_cases = [
            ("EB-1", "EB-1"),
            ("EB-2", "EB-2"),
            ("F1", "F1"),
            ("F2A", "F2A"),
        ]
        
        for input_cat, expected in test_cases:
            normalized = CategoryValidator.normalize_category(input_cat)
            assert normalized == expected
    
    def test_normalize_category_aliases(self):
        """Test normalizing category aliases"""
        test_cases = [
            ("EB1", "EB-1"),
            ("Employment First Preference", "EB-1"),
            ("Employment Second Preference", "EB-2"),
            ("Family First Preference", "F1"),
        ]
        
        for alias, expected in test_cases:
            normalized = CategoryValidator.normalize_category(alias)
            assert normalized == expected
    
    def test_normalize_case_insensitive(self):
        """Test case-insensitive normalization"""
        test_cases = [
            ("eb1", "EB-1"),
            ("EB1", "EB-1"),
            ("employment first preference", "EB-1"),
        ]
        
        for input_cat, expected in test_cases:
            normalized = CategoryValidator.normalize_category(input_cat)
            assert normalized == expected
    
    def test_normalize_invalid_category(self):
        """Test normalizing invalid categories"""
        invalid_categories = ["Invalid", "EB-10", "", None]
        
        for invalid_cat in invalid_categories:
            normalized = CategoryValidator.normalize_category(invalid_cat)
            assert normalized is None
    
    def test_validate_category(self):
        """Test category validation"""
        # Valid categories
        result = CategoryValidator.validate_category("EB-1")
        assert result.is_valid is True
        
        result = CategoryValidator.validate_category("F1")
        assert result.is_valid is True
        
        # Invalid category
        result = CategoryValidator.validate_category("Invalid")
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Empty category
        result = CategoryValidator.validate_category("")
        assert result.is_valid is False
        assert "Category cannot be empty" in result.errors[0]


class TestCountryValidator:
    """Test CountryValidator class"""
    
    def test_normalize_standard_countries(self):
        """Test normalizing standard country formats"""
        test_cases = [
            ("Worldwide", "Worldwide"),
            ("China", "China"),
            ("India", "India"),
            ("Mexico", "Mexico"),
            ("Philippines", "Philippines"),
        ]
        
        for input_country, expected in test_cases:
            normalized = CountryValidator.normalize_country(input_country)
            assert normalized == expected
    
    def test_normalize_country_aliases(self):
        """Test normalizing country aliases"""
        test_cases = [
            ("CHINA-mainland born", "China"),
            ("INDIA", "India"),
            ("All other countries", "Worldwide"),
            ("All Others", "Worldwide"),
            ("Rest of World", "Worldwide"),
            ("ROW", "Worldwide"),
        ]
        
        for alias, expected in test_cases:
            normalized = CountryValidator.normalize_country(alias)
            assert normalized == expected
    
    def test_normalize_case_insensitive(self):
        """Test case-insensitive normalization"""
        test_cases = [
            ("china", "China"),
            ("CHINA", "China"),
            ("all other countries", "Worldwide"),
        ]
        
        for input_country, expected in test_cases:
            normalized = CountryValidator.normalize_country(input_country)
            assert normalized == expected
    
    def test_normalize_invalid_country(self):
        """Test normalizing invalid countries"""
        invalid_countries = ["Invalid", "Germany", "", None]
        
        for invalid_country in invalid_countries:
            normalized = CountryValidator.normalize_country(invalid_country)
            assert normalized is None
    
    def test_validate_country(self):
        """Test country validation"""
        # Valid countries
        result = CountryValidator.validate_country("China")
        assert result.is_valid is True
        
        result = CountryValidator.validate_country("Worldwide")
        assert result.is_valid is True
        
        # Invalid country
        result = CountryValidator.validate_country("Invalid")
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Empty country
        result = CountryValidator.validate_country("")
        assert result.is_valid is False
        assert "Country cannot be empty" in result.errors[0]


class TestBulletinValidator:
    """Test BulletinValidator class"""
    
    def test_validate_bulletin_structure_valid(self):
        """Test validating valid bulletin structure"""
        valid_data = {
            "bulletin_date": "2024-07-01",
            "fiscal_year": 2024,
            "month": 7,
            "year": 2024,
            "categories": []
        }
        
        result = BulletinValidator.validate_bulletin_structure(valid_data)
        assert result.is_valid is True
    
    def test_validate_bulletin_structure_missing_fields(self):
        """Test validating bulletin with missing required fields"""
        invalid_data = {
            "bulletin_date": "2024-07-01",
            # Missing fiscal_year, month, year
        }
        
        result = BulletinValidator.validate_bulletin_structure(invalid_data)
        assert result.is_valid is False
        assert len(result.errors) >= 3  # Missing fiscal_year, month, year
    
    def test_validate_bulletin_structure_invalid_values(self):
        """Test validating bulletin with invalid values"""
        invalid_data = {
            "bulletin_date": "2024-07-01",
            "fiscal_year": 2050,  # Invalid
            "month": 13,  # Invalid
            "year": 1999,  # Invalid
            "categories": []
        }
        
        result = BulletinValidator.validate_bulletin_structure(invalid_data)
        assert result.is_valid is False
        assert len(result.errors) >= 3
    
    def test_validate_category_data_valid(self):
        """Test validating valid category data"""
        valid_category = {
            "category": "EB-2",
            "country": "India",
            "final_action_date": "2023-06-15",
            "status": "DATE"
        }
        
        result = BulletinValidator.validate_category_data(valid_category)
        assert result.is_valid is True
    
    def test_validate_category_data_missing_fields(self):
        """Test validating category data with missing fields"""
        invalid_category = {
            # Missing category and country
            "final_action_date": "2023-06-15",
            "status": "DATE"
        }
        
        result = BulletinValidator.validate_category_data(invalid_category)
        assert result.is_valid is False
        assert "Category is required" in result.errors[0]
        assert "Country is required" in result.errors[1]
    
    def test_validate_complete_bulletin(self, sample_bulletin_json):
        """Test validating complete bulletin"""
        result = BulletinValidator.validate_complete_bulletin(sample_bulletin_json)
        assert result.is_valid is True


class TestDataCleaner:
    """Test DataCleaner class"""
    
    def test_clean_bulletin_data(self):
        """Test cleaning bulletin data"""
        raw_data = {
            "bulletin_date": " 2024-07-01 ",
            "fiscal_year": " 2024 ",
            "month": "7",
            "year": " 2024 ",
            "categories": [
                {
                    "category": " EB-2 ",
                    "country": " India ",
                    "final_action_date": " 2023-06-15 ",
                    "status": " DATE "
                }
            ]
        }
        
        cleaned_data = DataCleaner.clean_bulletin_data(raw_data)
        
        assert cleaned_data["bulletin_date"] == "2024-07-01"
        assert cleaned_data["fiscal_year"] == 2024
        assert cleaned_data["month"] == 7
        assert cleaned_data["year"] == 2024
        assert len(cleaned_data["categories"]) == 1
    
    def test_clean_category_data(self):
        """Test cleaning category data"""
        raw_category = {
            "category": " EB-2 ",
            "country": " India ",
            "final_action_date": " 2023-06-15 ",
            "filing_date": " 2023-08-01 ",
            "status": " DATE ",
            "notes": " Test note "
        }
        
        cleaned_category = DataCleaner.clean_category_data(raw_category)
        
        assert cleaned_category["category"] == "EB-2"
        assert cleaned_category["country"] == "India"
        assert cleaned_category["final_action_date"] == "2023-06-15"
        assert cleaned_category["filing_date"] == "2023-08-01"
        assert cleaned_category["status"] == "DATE"
        assert cleaned_category["notes"] == "Test note"
    
    def test_clean_category_data_special_statuses(self):
        """Test cleaning category data with special statuses"""
        # Test Current status
        current_category = {
            "category": "EB-1",
            "country": "Worldwide",
            "final_action_date": "C"
        }
        
        cleaned = DataCleaner.clean_category_data(current_category)
        assert cleaned["status"] == "C"
        assert "final_action_date" not in cleaned
        
        # Test Unavailable status
        unavailable_category = {
            "category": "F1",
            "country": "China",
            "final_action_date": "U"
        }
        
        cleaned = DataCleaner.clean_category_data(unavailable_category)
        assert cleaned["status"] == "U"
        assert "final_action_date" not in cleaned
    
    def test_clean_category_data_invalid(self):
        """Test cleaning invalid category data"""
        invalid_category = {
            "category": "Invalid",
            "country": "Invalid",
        }
        
        cleaned = DataCleaner.clean_category_data(invalid_category)
        assert cleaned is None  # Should return None for invalid data