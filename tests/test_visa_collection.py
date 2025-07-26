"""
Unit tests for visa bulletin data collection modules
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, date
from pathlib import Path
import logging
import json

from visa.collection import HistoricalDataCollector, MonthlyDataFetcher, DataValidator
from visa.models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus
from visa.config import VisaConfig


class TestHistoricalDataCollector:
    """Test HistoricalDataCollector class"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock(spec=VisaConfig)
        return config
    
    @pytest.fixture
    def sample_bulletins(self):
        """Sample bulletins for testing"""
        bulletins = []
        for month in range(1, 4):  # 3 months
            bulletin = Mock(spec=VisaBulletin)
            bulletin.year = 2024
            bulletin.month = month
            bulletin.fiscal_year = 2024
            bulletin.bulletin_date = date(2024, month, 1)
            bulletin.categories = []
            bulletin.to_dict.return_value = {
                'year': 2024,
                'month': month,
                'fiscal_year': 2024,
                'bulletin_date': f'2024-{month:02d}-01',
                'categories': []
            }
            bulletins.append(bulletin)
        return bulletins
    
    @patch('visa.collection.historical.Path.mkdir')
    @patch('visa.collection.historical.logging.basicConfig')
    def test_initialization(self, mock_logging, mock_mkdir, mock_config):
        """Test collector initialization"""
        with patch('visa.collection.historical.VisaBulletinParser'):
            with patch('visa.collection.historical.VisaBulletinRepository'):
                collector = HistoricalDataCollector(config=mock_config)
                
                assert collector.config == mock_config
                assert collector.parser is not None
                assert collector.repository is not None
                assert collector.logger is not None
                mock_mkdir.assert_called_once_with(exist_ok=True)
    
    def test_initialization_default_config(self):
        """Test collector initialization with default config"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector()
                        assert collector.config is not None
    
    def test_collect_historical_data_method_exists(self, mock_config):
        """Test that collect_historical_data method exists"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector(config=mock_config)
                        
                        assert hasattr(collector, 'collect_historical_data')
                        assert callable(getattr(collector, 'collect_historical_data'))
    
    def test_validate_existing_data_method_exists(self, mock_config):
        """Test that validate_existing_data method exists"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector(config=mock_config)
                        
                        assert hasattr(collector, 'validate_existing_data')
                        assert callable(getattr(collector, 'validate_existing_data'))
    
    def test_get_collection_summary_method_exists(self, mock_config):
        """Test that get_collection_summary method exists"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector(config=mock_config)
                        
                        assert hasattr(collector, 'get_collection_summary')
                        assert callable(getattr(collector, 'get_collection_summary'))


class TestMonthlyDataFetcher:
    """Test MonthlyDataFetcher class"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock(spec=VisaConfig)
        return config
    
    def test_initialization(self, mock_config):
        """Test fetcher initialization"""
        with patch('visa.collection.monthly.VisaBulletinParser'):
            with patch('visa.collection.monthly.VisaBulletinRepository'):
                with patch('visa.collection.monthly.Path.mkdir'):
                    with patch('visa.collection.monthly.logging.basicConfig'):
                        fetcher = MonthlyDataFetcher(config=mock_config)
                        assert fetcher.config == mock_config
    
    def test_fetch_current_bulletin_method_exists(self, mock_config):
        """Test that fetch_current_bulletin method exists"""
        with patch('visa.collection.monthly.VisaBulletinParser'):
            with patch('visa.collection.monthly.VisaBulletinRepository'):
                with patch('visa.collection.monthly.Path.mkdir'):
                    with patch('visa.collection.monthly.logging.basicConfig'):
                        fetcher = MonthlyDataFetcher(config=mock_config)
                        
                        assert hasattr(fetcher, 'fetch_current_bulletin')
                        assert callable(getattr(fetcher, 'fetch_current_bulletin'))
    
    def test_setup_logging_method_exists(self, mock_config):
        """Test that _setup_logging method exists"""
        with patch('visa.collection.monthly.VisaBulletinParser'):
            with patch('visa.collection.monthly.VisaBulletinRepository'):
                with patch('visa.collection.monthly.Path.mkdir'):
                    with patch('visa.collection.monthly.logging.basicConfig'):
                        fetcher = MonthlyDataFetcher(config=mock_config)
                        
                        assert hasattr(fetcher, '_setup_logging')
                        assert callable(getattr(fetcher, '_setup_logging'))


class TestDataValidator:
    """Test DataValidator class"""
    
    def test_initialization(self):
        """Test validator initialization"""
        with patch('visa.collection.validator.VisaBulletinRepository'):
            with patch('visa.collection.validator.BulletinValidator'):
                with patch('visa.collection.validator.DateValidator'):
                    with patch('visa.collection.validator.Path.mkdir'):
                        with patch('visa.collection.validator.logging.basicConfig'):
                            validator = DataValidator()
                            assert validator.repository is not None
    
    def test_validate_all_data_method_exists(self):
        """Test that validate_all_data method exists"""
        with patch('visa.collection.validator.VisaBulletinRepository'):
            with patch('visa.collection.validator.BulletinValidator'):
                with patch('visa.collection.validator.DateValidator'):
                    with patch('visa.collection.validator.Path.mkdir'):
                        with patch('visa.collection.validator.logging.basicConfig'):
                            validator = DataValidator()
                            
                            assert hasattr(validator, 'validate_all_data')
                            assert callable(getattr(validator, 'validate_all_data'))
    
    def test_setup_logging_method_exists(self):
        """Test that _setup_logging method exists"""
        with patch('visa.collection.validator.VisaBulletinRepository'):
            with patch('visa.collection.validator.BulletinValidator'):
                with patch('visa.collection.validator.DateValidator'):
                    with patch('visa.collection.validator.Path.mkdir'):
                        with patch('visa.collection.validator.logging.basicConfig'):
                            validator = DataValidator()
                            
                            assert hasattr(validator, '_setup_logging')
                            assert callable(getattr(validator, '_setup_logging'))


@pytest.mark.integration
class TestCollectionIntegration:
    """Integration tests for collection modules"""
    
    def test_modules_can_be_instantiated_together(self):
        """Test that all collection modules can be instantiated together"""
        config = Mock(spec=VisaConfig)
        
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.monthly.Path.mkdir'):
                    with patch('visa.collection.monthly.logging.basicConfig'):
                        with patch('visa.collection.validator.Path.mkdir'):
                            with patch('visa.collection.validator.logging.basicConfig'):
                                with patch('visa.collection.historical.VisaBulletinParser'):
                                    with patch('visa.collection.historical.VisaBulletinRepository'):
                                        with patch('visa.collection.monthly.VisaBulletinParser'):
                                            with patch('visa.collection.monthly.VisaBulletinRepository'):
                                                with patch('visa.collection.validator.VisaBulletinRepository'):
                                                    with patch('visa.collection.validator.BulletinValidator'):
                                                        with patch('visa.collection.validator.DateValidator'):
                                                            
                                                            historical_collector = HistoricalDataCollector(config)
                                                            monthly_fetcher = MonthlyDataFetcher(config)
                                                            validator = DataValidator()
                                                            
                                                            assert historical_collector is not None
                                                            assert monthly_fetcher is not None
                                                            assert validator is not None
    
    def test_collection_workflow_methods_exist(self):
        """Test that the main workflow methods exist on all classes"""
        config = Mock(spec=VisaConfig)
        
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.monthly.Path.mkdir'):
                    with patch('visa.collection.monthly.logging.basicConfig'):
                        with patch('visa.collection.validator.Path.mkdir'):
                            with patch('visa.collection.validator.logging.basicConfig'):
                                with patch('visa.collection.historical.VisaBulletinParser'):
                                    with patch('visa.collection.historical.VisaBulletinRepository'):
                                        with patch('visa.collection.monthly.VisaBulletinParser'):
                                            with patch('visa.collection.monthly.VisaBulletinRepository'):
                                                with patch('visa.collection.validator.VisaBulletinRepository'):
                                                    with patch('visa.collection.validator.BulletinValidator'):
                                                        with patch('visa.collection.validator.DateValidator'):
                                                            
                                                            # Test HistoricalDataCollector methods
                                                            collector = HistoricalDataCollector(config)
                                                            assert hasattr(collector, 'collect_historical_data')
                                                            assert hasattr(collector, 'validate_existing_data')
                                                            assert hasattr(collector, 'get_collection_summary')
                                                            
                                                            # Test MonthlyDataFetcher methods
                                                            fetcher = MonthlyDataFetcher(config)
                                                            assert hasattr(fetcher, 'fetch_current_bulletin')
                                                            
                                                            # Test DataValidator methods
                                                            validator = DataValidator()
                                                            assert hasattr(validator, 'validate_all_data')


@pytest.mark.mock
class TestCollectionMocked:
    """Mock tests for collection modules"""
    
    @patch('visa.collection.historical.logging')
    def test_logging_configuration(self, mock_logging):
        """Test logging is properly configured"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.VisaBulletinParser'):
                with patch('visa.collection.historical.VisaBulletinRepository'):
                    collector = HistoricalDataCollector()
                    
                    # Verify logging was configured
                    mock_logging.basicConfig.assert_called_once()
                    mock_logging.getLogger.assert_called()
    
    @patch('pathlib.Path.mkdir')
    def test_directory_creation(self, mock_mkdir):
        """Test that data directories are created"""
        with patch('visa.collection.historical.logging.basicConfig'):
            with patch('visa.collection.historical.VisaBulletinParser'):
                with patch('visa.collection.historical.VisaBulletinRepository'):
                    collector = HistoricalDataCollector()
                    
                    # Verify directory creation was attempted
                    mock_mkdir.assert_called_with(exist_ok=True)
    
    def test_config_injection(self):
        """Test configuration dependency injection"""
        config = Mock(spec=VisaConfig)
        
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector(config=config)
                        assert collector.config == config
    
    def test_default_config_creation(self):
        """Test default configuration is created when none provided"""
        with patch('visa.collection.historical.Path.mkdir'):
            with patch('visa.collection.historical.logging.basicConfig'):
                with patch('visa.collection.historical.VisaBulletinParser'):
                    with patch('visa.collection.historical.VisaBulletinRepository'):
                        collector = HistoricalDataCollector()
                        assert collector.config is not None


# Test fixtures
@pytest.fixture
def sample_bulletin_dict():
    """Sample bulletin dictionary for testing"""
    return {
        'bulletin_date': '2024-07-01',
        'fiscal_year': 2024,
        'month': 7,
        'year': 2024,
        'source_url': 'https://example.com',
        'categories': [
            {
                'category': 'EB-2',
                'country': 'India',
                'final_action_date': '2022-01-15',
                'filing_date': '2022-06-01',
                'status': 'DATE',
                'notes': 'Test category'
            }
        ]
    }


@pytest.fixture
def sample_bulletin():
    """Sample VisaBulletin object for testing"""
    bulletin = VisaBulletin(
        bulletin_date=date(2024, 7, 1),
        fiscal_year=2024,
        month=7,
        year=2024,
        source_url="https://example.com"
    )
    
    cat_data = CategoryData(
        category=VisaCategory.EB2,
        country=CountryCode.INDIA,
        final_action_date=date(2022, 1, 15),
        filing_date=date(2022, 6, 1),
        status=BulletinStatus.DATE_SPECIFIED,
        notes="Test category"
    )
    bulletin.add_category_data(cat_data)
    
    return bulletin