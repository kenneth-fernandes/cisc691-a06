"""
Data validation and parsing utilities for visa bulletin data
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

from .models import VisaCategory, CountryCode, BulletinStatus


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)


class DateValidator:
    """Utility class for date validation and parsing"""
    
    # Common date patterns in visa bulletins
    DATE_PATTERNS = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY or M/D/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY or M-D-YYYY
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})', # MM.DD.YYYY
    ]
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse various date formats commonly found in visa bulletins"""
        if not date_str or date_str.strip() == "":
            return None
        
        # Handle special status codes
        date_str = date_str.strip().upper()
        if date_str in ['C', 'CURRENT', 'U', 'UNAVAILABLE']:
            return None
        
        # Try different date patterns
        for pattern in DateValidator.DATE_PATTERNS:
            match = re.match(pattern, date_str.strip())
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3:
                        # Determine format based on pattern
                        if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # MM/DD/YYYY variants
                            month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                        
                        return date(year, month, day)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def validate_date_range(date_obj: date, min_year: int = 2000, max_year: int = 2030) -> bool:
        """Validate that a date is within reasonable range for visa bulletins"""
        if not date_obj:
            return True  # None dates are acceptable
        
        return min_year <= date_obj.year <= max_year
    
    @staticmethod
    def format_date_for_display(date_obj: Optional[date]) -> str:
        """Format date for display in UI"""
        if not date_obj:
            return "Not Available"
        return date_obj.strftime("%B %d, %Y")


class CategoryValidator:
    """Utility class for category validation"""
    
    # Alternative category names found in bulletins
    CATEGORY_ALIASES = {
        'EB1': 'EB-1',
        'EB2': 'EB-2', 
        'EB3': 'EB-3',
        'EB4': 'EB-4',
        'EB5': 'EB-5',
        'Employment First Preference': 'EB-1',
        'Employment Second Preference': 'EB-2',
        'Employment Third Preference': 'EB-3',
        'Employment Fourth Preference': 'EB-4',
        'Employment Fifth Preference': 'EB-5',
        'Family First Preference': 'F1',
        'Family Second Preference A': 'F2A',
        'Family Second Preference B': 'F2B',
        'Family Third Preference': 'F3',
        'Family Fourth Preference': 'F4',
    }
    
    @staticmethod
    def normalize_category(category_str: str) -> Optional[str]:
        """Normalize category string to standard format"""
        if not category_str:
            return None
        
        category_str = category_str.strip()
        
        # Direct match
        try:
            return VisaCategory(category_str).value
        except ValueError:
            pass
        
        # Try aliases
        normalized = CategoryValidator.CATEGORY_ALIASES.get(category_str)
        if normalized:
            return normalized
        
        # Try case-insensitive match
        for alias, standard in CategoryValidator.CATEGORY_ALIASES.items():
            if alias.lower() == category_str.lower():
                return standard
        
        return None
    
    @staticmethod
    def validate_category(category_str: str) -> ValidationResult:
        """Validate category string"""
        result = ValidationResult(True, [], [])
        
        if not category_str:
            result.add_error("Category cannot be empty")
            return result
        
        normalized = CategoryValidator.normalize_category(category_str)
        if not normalized:
            result.add_error(f"Invalid category: {category_str}")
            result.add_warning("Supported categories: EB-1, EB-2, EB-3, EB-4, EB-5, F1, F2A, F2B, F3, F4")
        
        return result


class CountryValidator:
    """Utility class for country validation"""
    
    # Alternative country names found in bulletins
    COUNTRY_ALIASES = {
        'CHINA-mainland born': 'China',
        'INDIA': 'India',
        'MEXICO': 'Mexico',
        'PHILIPPINES': 'Philippines',
        'All other countries': 'Worldwide',
        'All Others': 'Worldwide',
        'Rest of World': 'Worldwide',
        'ROW': 'Worldwide'
    }
    
    @staticmethod
    def normalize_country(country_str: str) -> Optional[str]:
        """Normalize country string to standard format"""
        if not country_str:
            return None
        
        country_str = country_str.strip()
        
        # Direct match
        try:
            return CountryCode(country_str).value
        except ValueError:
            pass
        
        # Try case-insensitive direct match for enum values
        for country_code in CountryCode:
            if country_code.value.lower() == country_str.lower():
                return country_code.value
        
        # Try aliases
        normalized = CountryValidator.COUNTRY_ALIASES.get(country_str)
        if normalized:
            return normalized
        
        # Try case-insensitive match for aliases
        for alias, standard in CountryValidator.COUNTRY_ALIASES.items():
            if alias.lower() == country_str.lower():
                return standard
        
        return None
    
    @staticmethod
    def validate_country(country_str: str) -> ValidationResult:
        """Validate country string"""
        result = ValidationResult(True, [], [])
        
        if not country_str:
            result.add_error("Country cannot be empty")
            return result
        
        normalized = CountryValidator.normalize_country(country_str)
        if not normalized:
            result.add_error(f"Invalid country: {country_str}")
            result.add_warning("Supported countries: China, India, Mexico, Philippines, Worldwide")
        
        return result


class BulletinValidator:
    """Validator for complete visa bulletin data"""
    
    @staticmethod
    def validate_bulletin_structure(data: Dict[str, Any]) -> ValidationResult:
        """Validate the structure of bulletin data"""
        result = ValidationResult(True, [], [])
        
        # Required fields
        required_fields = ['bulletin_date', 'fiscal_year', 'month', 'year']
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Validate fiscal year
        if 'fiscal_year' in data:
            fy = data['fiscal_year']
            if not isinstance(fy, int) or fy < 2020 or fy > 2030:
                result.add_error(f"Invalid fiscal year: {fy} (must be between 2020-2030)")
        
        # Validate month
        if 'month' in data:
            month = data['month']
            if not isinstance(month, int) or month < 1 or month > 12:
                result.add_error(f"Invalid month: {month} (must be 1-12)")
        
        # Validate year
        if 'year' in data:
            year = data['year']
            if not isinstance(year, int) or year < 2020 or year > 2030:
                result.add_error(f"Invalid year: {year} (must be between 2020-2030)")
        
        # Check for categories data
        if 'categories' not in data or not data['categories']:
            result.add_warning("No category data found in bulletin")
        
        return result
    
    @staticmethod
    def validate_category_data(cat_data: Dict[str, Any]) -> ValidationResult:
        """Validate individual category data entry"""
        result = ValidationResult(True, [], [])
        
        # Validate category
        if 'category' not in cat_data:
            result.add_error("Category is required")
        else:
            cat_result = CategoryValidator.validate_category(cat_data['category'])
            result.errors.extend(cat_result.errors)
            result.warnings.extend(cat_result.warnings)
            if not cat_result.is_valid:
                result.is_valid = False
        
        # Validate country
        if 'country' not in cat_data:
            result.add_error("Country is required")
        else:
            country_result = CountryValidator.validate_country(cat_data['country'])
            result.errors.extend(country_result.errors)
            result.warnings.extend(country_result.warnings)
            if not country_result.is_valid:
                result.is_valid = False
        
        # Validate dates if present
        for date_field in ['final_action_date', 'filing_date']:
            if date_field in cat_data and cat_data[date_field]:
                parsed_date = DateValidator.parse_date(str(cat_data[date_field]))
                if parsed_date and not DateValidator.validate_date_range(parsed_date):
                    result.add_warning(f"Date {cat_data[date_field]} is outside normal range")
        
        return result
    
    @staticmethod
    def validate_complete_bulletin(bulletin_data: Dict[str, Any]) -> ValidationResult:
        """Validate a complete bulletin with all category data"""
        result = BulletinValidator.validate_bulletin_structure(bulletin_data)
        
        if 'categories' in bulletin_data:
            for i, cat_data in enumerate(bulletin_data['categories']):
                cat_result = BulletinValidator.validate_category_data(cat_data)
                
                # Prefix errors with category index for clarity
                for error in cat_result.errors:
                    result.add_error(f"Category {i+1}: {error}")
                
                for warning in cat_result.warnings:
                    result.add_warning(f"Category {i+1}: {warning}")
                
                if not cat_result.is_valid:
                    result.is_valid = False
        
        return result


class DataCleaner:
    """Utility class for cleaning and normalizing bulletin data"""
    
    @staticmethod
    def clean_bulletin_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize raw bulletin data"""
        cleaned = raw_data.copy()
        
        # Clean date strings
        if 'bulletin_date' in cleaned:
            cleaned['bulletin_date'] = str(cleaned['bulletin_date']).strip()
        
        # Clean numeric fields
        for field in ['fiscal_year', 'month', 'year']:
            if field in cleaned and isinstance(cleaned[field], str):
                try:
                    cleaned[field] = int(cleaned[field].strip())
                except ValueError:
                    pass  # Keep original value, will be caught by validation
        
        # Clean categories
        if 'categories' in cleaned:
            cleaned_categories = []
            for cat_data in cleaned['categories']:
                cleaned_cat = DataCleaner.clean_category_data(cat_data)
                if cleaned_cat:  # Only include if not empty
                    cleaned_categories.append(cleaned_cat)
            cleaned['categories'] = cleaned_categories
        
        return cleaned
    
    @staticmethod
    def clean_category_data(raw_cat_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean individual category data"""
        cleaned = {}
        
        # Clean category
        if 'category' in raw_cat_data:
            category = CategoryValidator.normalize_category(str(raw_cat_data['category']).strip())
            if category:
                cleaned['category'] = category
        
        # Clean country
        if 'country' in raw_cat_data:
            country = CountryValidator.normalize_country(str(raw_cat_data['country']).strip())
            if country:
                cleaned['country'] = country
        
        # Initialize status
        status_set = False
        
        # Clean dates
        for date_field in ['final_action_date', 'filing_date']:
            if date_field in raw_cat_data and raw_cat_data[date_field]:
                date_str = str(raw_cat_data[date_field]).strip()
                parsed_date = DateValidator.parse_date(date_str)
                if parsed_date:
                    cleaned[date_field] = parsed_date.isoformat()
                elif date_str.upper() in ['C', 'CURRENT']:
                    cleaned['status'] = 'C'
                    status_set = True
                elif date_str.upper() in ['U', 'UNAVAILABLE']:
                    cleaned['status'] = 'U'
                    status_set = True
        
        # Clean status (only if not already set from date fields)
        if 'status' in raw_cat_data:
            status = str(raw_cat_data['status']).strip().upper()
            if status in ['C', 'CURRENT']:
                cleaned['status'] = 'C'
                status_set = True
            elif status in ['U', 'UNAVAILABLE']:
                cleaned['status'] = 'U'
                status_set = True
            elif not status_set:
                cleaned['status'] = 'DATE'
        elif not status_set:
            cleaned['status'] = 'DATE'  # Default status
        
        # Clean notes
        if 'notes' in raw_cat_data and raw_cat_data['notes']:
            cleaned['notes'] = str(raw_cat_data['notes']).strip()
        
        # Only return if we have required fields
        if 'category' in cleaned and 'country' in cleaned:
            return cleaned
        
        return None