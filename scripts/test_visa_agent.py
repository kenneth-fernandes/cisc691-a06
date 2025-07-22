import os
from datetime import date
from dotenv import load_dotenv

import sys
from pathlib import Path

# Add project root to Python path
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from src.agent.factory import create_agent, get_available_modes
from src.visa.models import VisaBulletin, CategoryData, VisaCategory, CountryCode, BulletinStatus

# Test constants
TEST_CATEGORY = VisaCategory.EB2
TEST_COUNTRY = CountryCode.INDIA
TEST_START_DATE = date(2024, 1, 1)
TEST_END_DATE = date(2024, 7, 1)
TEST_MONTHS = 3

def create_test_bulletin() -> VisaBulletin:
    """Create a sample bulletin for testing"""
    bulletin = VisaBulletin(
        bulletin_date=date(2024, 7, 1),
        fiscal_year=2024,
        month=7,
        year=2024
    )
    
    category_data = CategoryData(
        category=VisaCategory.F2A,
        country=CountryCode.MEXICO,
        final_action_date=date(2022, 8, 15),
        filing_date=date(2023, 1, 1),
        status=BulletinStatus.DATE_SPECIFIED
    )
    
    bulletin.add_category_data(category_data)
    return bulletin

def test_visa_agent():
    """Test visa bulletin expertise functionality"""
    print("🔄 Loading environment variables...")
    load_dotenv()
    
    print("🤖 Creating visa expert agent...")
    agent = create_agent(
        provider=os.getenv('LLM_PROVIDER', 'google'),
        mode="visa_expert"
    )
    
    # Test visa movement analysis
    print("\n📊 1. Testing visa movement analysis:")
    print(f"   Analyzing {TEST_CATEGORY.value} for {TEST_COUNTRY.value}...")
    result = agent.analyze_visa_movement(
        category=TEST_CATEGORY,
        country=TEST_COUNTRY,
        start_date=TEST_START_DATE,
        end_date=TEST_END_DATE
    )
    print("📋 Analysis Result:")
    print(result)
    
    # Test movement prediction
    print("\n🔮 2. Testing movement prediction:")
    print(f"   Predicting next {TEST_MONTHS} months for {TEST_CATEGORY.value}...")
    result = agent.predict_visa_movement(
        category=TEST_CATEGORY,
        country=TEST_COUNTRY,
        months=TEST_MONTHS
    )
    print("📋 Prediction Result:")
    print(result)
    
    # Test status explanation
    print("\n📱 3. Testing status explanation:")
    print(f"   Explaining current status for {TEST_CATEGORY.value}...")
    result = agent.explain_visa_status(
        category=TEST_CATEGORY,
        country=TEST_COUNTRY,
        bulletin=create_test_bulletin()
    )
    print("📋 Status Explanation:")
    print(result)

if __name__ == "__main__":
    test_visa_agent()