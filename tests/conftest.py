"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date
import json

# Set environment variables before any imports
os.environ.update({
    "GOOGLE_API_KEY": "test_key_for_ci",
    "OPENAI_API_KEY": "test_key_for_ci", 
    "ANTHROPIC_API_KEY": "test_key_for_ci",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "test_db",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "test_password",
    "MONGO_HOST": "localhost",
    "MONGO_PORT": "27017",
    "MONGO_DB": "test_db",
    "MONGO_USER": "test_user",
    "MONGO_PASSWORD": "test_password",
    "DOCKER_MODE": "false",
    "DEBUG": "true"
})

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from visa.models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus
from visa.config import VisaConfig
from visa.parser import VisaBulletinParser


@pytest.fixture
def sample_visa_config():
    """Provide a sample visa configuration"""
    return VisaConfig()


@pytest.fixture
def sample_category_data():
    """Provide sample category data for testing"""
    return CategoryData(
        category=VisaCategory.EB2,
        country=CountryCode.INDIA,
        final_action_date=date(2023, 6, 15),
        filing_date=date(2023, 8, 1),
        status=BulletinStatus.DATE_SPECIFIED,
        notes="Test category data"
    )


@pytest.fixture
def sample_bulletin(sample_category_data):
    """Provide a sample visa bulletin for testing"""
    bulletin = VisaBulletin(
        bulletin_date=date(2024, 7, 1),
        fiscal_year=2024,
        month=7,
        year=2024,
        source_url="https://example.com/bulletin"
    )
    bulletin.add_category_data(sample_category_data)
    return bulletin


@pytest.fixture
def multiple_categories():
    """Provide multiple category data entries for testing"""
    categories = [
        CategoryData(
            category=VisaCategory.EB1,
            country=CountryCode.WORLDWIDE,
            status=BulletinStatus.CURRENT
        ),
        CategoryData(
            category=VisaCategory.EB2,
            country=CountryCode.INDIA,
            final_action_date=date(2023, 6, 15),
            status=BulletinStatus.DATE_SPECIFIED
        ),
        CategoryData(
            category=VisaCategory.F1,
            country=CountryCode.CHINA,
            status=BulletinStatus.UNAVAILABLE
        ),
        CategoryData(
            category=VisaCategory.F2A,
            country=CountryCode.MEXICO,
            final_action_date=date(2023, 3, 1),
            filing_date=date(2023, 5, 1),
            status=BulletinStatus.DATE_SPECIFIED
        )
    ]
    return categories


@pytest.fixture
def mock_html_content():
    """Provide mock HTML content for testing parser"""
    return """
    <html>
    <head><title>Visa Bulletin for July 2024</title></head>
    <body>
        <h1>Visa Bulletin for July 2024</h1>
        <table>
            <tr>
                <th>Category</th>
                <th>Worldwide</th>
                <th>China</th>
                <th>India</th>
                <th>Mexico</th>
                <th>Philippines</th>
            </tr>
            <tr>
                <td>EB-1</td>
                <td>C</td>
                <td>C</td>
                <td>C</td>
                <td>C</td>
                <td>C</td>
            </tr>
            <tr>
                <td>EB-2</td>
                <td>C</td>
                <td>01/01/2020</td>
                <td>01/15/2012</td>
                <td>C</td>
                <td>C</td>
            </tr>
            <tr>
                <td>F1</td>
                <td>U</td>
                <td>U</td>
                <td>U</td>
                <td>U</td>
                <td>U</td>
            </tr>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def mock_requests_session():
    """Provide a mock requests session for testing"""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    mock_session.head.return_value = mock_response
    return mock_session


@pytest.fixture
def parser_with_mock_session(sample_visa_config, mock_requests_session):
    """Provide a parser with mocked session"""
    parser = VisaBulletinParser(sample_visa_config)
    parser.scraper.session = mock_requests_session
    return parser


@pytest.fixture
def sample_bulletin_json():
    """Provide sample bulletin data as JSON"""
    return {
        "bulletin_date": "2024-07-01",
        "fiscal_year": 2024,
        "month": 7,
        "year": 2024,
        "source_url": "https://example.com/bulletin",
        "categories": [
            {
                "category": "EB-2",
                "country": "India",
                "final_action_date": "2023-06-15",
                "filing_date": "2023-08-01",
                "status": "DATE",
                "notes": "Test category"
            }
        ],
        "created_at": "2024-07-01T00:00:00",
        "updated_at": "2024-07-01T00:00:00"
    }


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def historical_bulletin_urls():
    """Provide sample historical bulletin URLs for testing"""
    return [
        ("https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2024/visa-bulletin-for-january-2024.html", 2024, 1),
        ("https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2024/visa-bulletin-for-february-2024.html", 2024, 2),
        ("https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2024/visa-bulletin-for-march-2024.html", 2024, 3),
    ]


# Utility functions for tests
def assert_valid_bulletin(bulletin):
    """Assert that a bulletin object is valid"""
    assert isinstance(bulletin, VisaBulletin)
    assert isinstance(bulletin.bulletin_date, date)
    assert isinstance(bulletin.fiscal_year, int)
    assert isinstance(bulletin.month, int)
    assert isinstance(bulletin.year, int)
    assert 1 <= bulletin.month <= 12
    assert 2020 <= bulletin.fiscal_year <= 2030


def assert_valid_category_data(category_data):
    """Assert that category data is valid"""
    assert isinstance(category_data, CategoryData)
    assert isinstance(category_data.category, VisaCategory)
    assert isinstance(category_data.country, CountryCode)
    assert isinstance(category_data.status, BulletinStatus)


@pytest.fixture(scope="session", autouse=True)
def mock_llm_providers():
    """Mock all LLM providers to avoid API key validation"""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Mock LLM response")
    
    with patch('langchain_google_genai.ChatGoogleGenerativeAI', return_value=mock_llm), \
         patch('langchain_openai.ChatOpenAI', return_value=mock_llm), \
         patch('langchain_anthropic.ChatAnthropic', return_value=mock_llm), \
         patch('langchain_ollama.ChatOllama', return_value=mock_llm):
        yield


@pytest.fixture
def mock_agent():
    """Mock agent for testing without real LLM calls"""
    with patch('api.routers.agent.get_or_create_agent') as mock:
        mock_agent_instance = MockAgent()
        mock.return_value = mock_agent_instance
        yield mock_agent_instance


class MockAgent:
    """Mock agent for testing"""
    
    def __init__(self):
        self.conversation_history = []
    
    def chat(self, message: str) -> str:
        """Mock chat method"""
        response = f"Mock response to: {message}"
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": response
        })
        return response
    
    def get_conversation_history(self):
        """Mock conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Mock clear conversation"""
        self.conversation_history = []