"""
Unit tests for visa models
"""
import pytest
from datetime import date, datetime
from visa.models import (
    VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus,
    PredictionResult, TrendAnalysis
)


class TestVisaCategory:
    """Test VisaCategory enum"""
    
    def test_employment_categories(self):
        """Test employment-based categories"""
        employment_cats = [VisaCategory.EB1, VisaCategory.EB2, VisaCategory.EB3, 
                          VisaCategory.EB4, VisaCategory.EB5]
        for cat in employment_cats:
            assert cat.value.startswith("EB-")
    
    def test_family_categories(self):
        """Test family-based categories"""
        family_cats = [VisaCategory.F1, VisaCategory.F2A, VisaCategory.F2B, 
                      VisaCategory.F3, VisaCategory.F4]
        for cat in family_cats:
            assert cat.value.startswith("F")


class TestCountryCode:
    """Test CountryCode enum"""
    
    def test_country_values(self):
        """Test country code values"""
        assert CountryCode.WORLDWIDE.value == "Worldwide"
        assert CountryCode.CHINA.value == "China"
        assert CountryCode.INDIA.value == "India"
        assert CountryCode.MEXICO.value == "Mexico"
        assert CountryCode.PHILIPPINES.value == "Philippines"


class TestBulletinStatus:
    """Test BulletinStatus enum"""
    
    def test_status_values(self):
        """Test status values"""
        assert BulletinStatus.CURRENT.value == "C"
        assert BulletinStatus.UNAVAILABLE.value == "U"
        assert BulletinStatus.DATE_SPECIFIED.value == "DATE"


class TestCategoryData:
    """Test CategoryData model"""
    
    def test_basic_creation(self):
        """Test basic category data creation"""
        category_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 6, 15),
            status=BulletinStatus.DATE_SPECIFIED
        )
        
        assert category_data.category == VisaCategory.EB2
        assert category_data.country == CountryCode.INDIA
        assert category_data.final_action_date == date(2023, 6, 15)
        assert category_data.status == BulletinStatus.DATE_SPECIFIED
    
    def test_current_status(self):
        """Test category with current status"""
        category_data = CategoryData(
            category=VisaCategory.EB1,
            country=CountryCode.WORLDWIDE,
            status=BulletinStatus.CURRENT
        )
        
        assert category_data.final_action_date is None
        assert category_data.status == BulletinStatus.CURRENT
    
    def test_unavailable_status(self):
        """Test category with unavailable status"""
        category_data = CategoryData(
            category=VisaCategory.F1,
            country=CountryCode.CHINA,
            status=BulletinStatus.UNAVAILABLE
        )
        
        assert category_data.final_action_date is None
        assert category_data.status == BulletinStatus.UNAVAILABLE
    
    def test_string_conversion(self):
        """Test category data with string inputs"""
        category_data = CategoryData(
            category="EB-2",
            country="India",
            status="DATE"
        )
        
        assert category_data.category == VisaCategory.EB2
        assert category_data.country == CountryCode.INDIA
        assert category_data.status == BulletinStatus.DATE_SPECIFIED
    
    def test_to_dict(self):
        """Test converting category data to dictionary"""
        category_data = CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 6, 15),
            filing_date=date(2023, 8, 1),
            status=BulletinStatus.DATE_SPECIFIED,
            notes="Test note"
        )
        
        data_dict = category_data.to_dict()
        
        assert data_dict["category"] == "EB-2"
        assert data_dict["country"] == "India"
        assert data_dict["final_action_date"] == "2023-06-15"
        assert data_dict["filing_date"] == "2023-08-01"
        assert data_dict["status"] == "DATE"
        assert data_dict["notes"] == "Test note"
    
    def test_from_dict(self):
        """Test creating category data from dictionary"""
        data_dict = {
            "category": "EB-2",
            "country": "India",
            "final_action_date": "2023-06-15",
            "filing_date": "2023-08-01",
            "status": "DATE",
            "notes": "Test note"
        }
        
        category_data = CategoryData.from_dict(data_dict)
        
        assert category_data.category == VisaCategory.EB2
        assert category_data.country == CountryCode.INDIA
        assert category_data.final_action_date == date(2023, 6, 15)
        assert category_data.filing_date == date(2023, 8, 1)
        assert category_data.status == BulletinStatus.DATE_SPECIFIED
        assert category_data.notes == "Test note"


class TestVisaBulletin:
    """Test VisaBulletin model"""
    
    def test_basic_creation(self):
        """Test basic bulletin creation"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        assert bulletin.bulletin_date == date(2024, 7, 1)
        assert bulletin.fiscal_year == 2024
        assert bulletin.month == 7
        assert bulletin.year == 2024
        assert bulletin.categories == []
    
    def test_invalid_fiscal_year(self):
        """Test bulletin with invalid fiscal year"""
        with pytest.raises(ValueError, match="Invalid fiscal year"):
            VisaBulletin(
                bulletin_date=date(2024, 7, 1),
                fiscal_year=2050,  # Invalid
                month=7,
                year=2024
            )
    
    def test_invalid_month(self):
        """Test bulletin with invalid month"""
        with pytest.raises(ValueError, match="Invalid month"):
            VisaBulletin(
                bulletin_date=date(2024, 7, 1),
                fiscal_year=2024,
                month=13,  # Invalid
                year=2024
            )
    
    def test_add_category_data(self, sample_category_data):
        """Test adding category data to bulletin"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        assert len(bulletin.categories) == 0
        bulletin.add_category_data(sample_category_data)
        assert len(bulletin.categories) == 1
        assert bulletin.categories[0] == sample_category_data
    
    def test_get_category_data(self, sample_bulletin):
        """Test getting specific category data"""
        category_data = sample_bulletin.get_category_data(
            VisaCategory.EB2, CountryCode.INDIA
        )
        assert category_data is not None
        assert category_data.category == VisaCategory.EB2
        assert category_data.country == CountryCode.INDIA
        
        # Test non-existent category
        missing_data = sample_bulletin.get_category_data(
            VisaCategory.F1, CountryCode.CHINA
        )
        assert missing_data is None
    
    def test_get_employment_categories(self, multiple_categories):
        """Test getting employment-based categories"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        for cat_data in multiple_categories:
            bulletin.add_category_data(cat_data)
        
        employment_cats = bulletin.get_employment_categories()
        assert len(employment_cats) == 2  # EB1 and EB2
        
        for cat in employment_cats:
            assert cat.category.value.startswith("EB-")
    
    def test_get_family_categories(self, multiple_categories):
        """Test getting family-based categories"""
        bulletin = VisaBulletin(
            bulletin_date=date(2024, 7, 1),
            fiscal_year=2024,
            month=7,
            year=2024
        )
        
        for cat_data in multiple_categories:
            bulletin.add_category_data(cat_data)
        
        family_cats = bulletin.get_family_categories()
        assert len(family_cats) == 2  # F1 and F2A
        
        for cat in family_cats:
            assert cat.category.value.startswith("F")
    
    def test_to_dict(self, sample_bulletin):
        """Test converting bulletin to dictionary"""
        bulletin_dict = sample_bulletin.to_dict()
        
        assert bulletin_dict["bulletin_date"] == "2024-07-01"
        assert bulletin_dict["fiscal_year"] == 2024
        assert bulletin_dict["month"] == 7
        assert bulletin_dict["year"] == 2024
        assert bulletin_dict["source_url"] == "https://example.com/bulletin"
        assert len(bulletin_dict["categories"]) == 1
        assert isinstance(bulletin_dict["created_at"], str)
        assert isinstance(bulletin_dict["updated_at"], str)
    
    def test_from_dict(self, sample_bulletin_json):
        """Test creating bulletin from dictionary"""
        bulletin = VisaBulletin.from_dict(sample_bulletin_json)
        
        assert bulletin.bulletin_date == date(2024, 7, 1)
        assert bulletin.fiscal_year == 2024
        assert bulletin.month == 7
        assert bulletin.year == 2024
        assert bulletin.source_url == "https://example.com/bulletin"
        assert len(bulletin.categories) == 1
        
        category = bulletin.categories[0]
        assert category.category == VisaCategory.EB2
        assert category.country == CountryCode.INDIA


class TestPredictionResult:
    """Test PredictionResult model"""
    
    def test_basic_creation(self):
        """Test basic prediction result creation"""
        prediction = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 10, 1),
            confidence_score=0.85,
            prediction_type="advancement",
            target_month=10,
            target_year=2024
        )
        
        assert prediction.category == VisaCategory.EB2
        assert prediction.country == CountryCode.INDIA
        assert prediction.predicted_date == date(2024, 10, 1)
        assert prediction.confidence_score == 0.85
        assert prediction.prediction_type == "advancement"
        assert prediction.target_month == 10
        assert prediction.target_year == 2024
        assert prediction.model_version == "1.0"
    
    def test_to_dict(self):
        """Test converting prediction to dictionary"""
        prediction = PredictionResult(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            predicted_date=date(2024, 10, 1),
            confidence_score=0.85,
            prediction_type="advancement",
            target_month=10,
            target_year=2024
        )
        
        pred_dict = prediction.to_dict()
        
        assert pred_dict["category"] == "EB-2"
        assert pred_dict["country"] == "India"
        assert pred_dict["predicted_date"] == "2024-10-01"
        assert pred_dict["confidence_score"] == 0.85
        assert pred_dict["prediction_type"] == "advancement"
        assert pred_dict["target_month"] == 10
        assert pred_dict["target_year"] == 2024


class TestTrendAnalysis:
    """Test TrendAnalysis model"""
    
    def test_basic_creation(self):
        """Test basic trend analysis creation"""
        trend = TrendAnalysis(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 7, 1),
            total_advancement_days=180,
            average_monthly_advancement=30.0,
            volatility_score=0.25,
            trend_direction="advancing"
        )
        
        assert trend.category == VisaCategory.EB2
        assert trend.country == CountryCode.INDIA
        assert trend.start_date == date(2024, 1, 1)
        assert trend.end_date == date(2024, 7, 1)
        assert trend.total_advancement_days == 180
        assert trend.average_monthly_advancement == 30.0
        assert trend.volatility_score == 0.25
        assert trend.trend_direction == "advancing"
    
    def test_to_dict(self):
        """Test converting trend analysis to dictionary"""
        trend = TrendAnalysis(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 7, 1),
            total_advancement_days=180,
            average_monthly_advancement=30.0,
            volatility_score=0.25,
            trend_direction="advancing"
        )
        
        trend_dict = trend.to_dict()
        
        assert trend_dict["category"] == "EB-2"
        assert trend_dict["country"] == "India"
        assert trend_dict["start_date"] == "2024-01-01"
        assert trend_dict["end_date"] == "2024-07-01"
        assert trend_dict["total_advancement_days"] == 180
        assert trend_dict["average_monthly_advancement"] == 30.0
        assert trend_dict["volatility_score"] == 0.25
        assert trend_dict["trend_direction"] == "advancing"