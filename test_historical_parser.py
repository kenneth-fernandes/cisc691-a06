#!/usr/bin/env python3
"""
Test script for historical visa bulletin parsing functionality
"""
import logging
from src.visa.parser import VisaBulletinParser, ParsingError
from src.visa.config import VisaConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_single_historical_bulletin():
    """Test parsing a single historical bulletin"""
    logger.info("=== Testing Single Historical Bulletin ===")
    
    config = VisaConfig()
    parser = VisaBulletinParser(config)
    
    try:
        # Test parsing a specific bulletin (June 2024)
        bulletin = parser.parse_bulletin_by_date(2024, 6)
        
        if bulletin:
            logger.info(f"✅ Successfully parsed bulletin for {bulletin.bulletin_date}")
            logger.info(f"📅 Fiscal Year: {bulletin.fiscal_year}")
            logger.info(f"🔗 Source: {bulletin.source_url}")
            logger.info(f"📊 Categories found: {len(bulletin.categories)}")
            
            # Show sample categories
            if bulletin.categories:
                logger.info("📋 Sample categories:")
                for i, cat in enumerate(bulletin.categories[:3]):
                    logger.info(f"  {i+1}. {cat.category.value} - {cat.country.value}: {cat.final_action_date or cat.status.value}")
        else:
            logger.warning("❌ No bulletin found for the specified date")
            
    except Exception as e:
        logger.error(f"❌ Error testing single bulletin: {e}")

def test_historical_range():
    """Test parsing a range of historical bulletins"""
    logger.info("\n=== Testing Historical Bulletin Range ===")
    
    config = VisaConfig()
    parser = VisaBulletinParser(config)
    
    try:
        # Test parsing a small range (last 3 months of 2024)
        bulletins = parser.parse_historical_bulletins(
            start_year=2024, 
            end_year=2024,
            verify_urls=True,
            max_workers=3
        )
        
        logger.info(f"📊 Historical parsing results:")
        logger.info(f"   ✅ Total bulletins parsed: {len(bulletins)}")
        
        if bulletins:
            logger.info("📋 Parsed bulletins summary:")
            for bulletin in bulletins[-5:]:  # Show last 5
                employment_count = len(bulletin.get_employment_categories())
                family_count = len(bulletin.get_family_categories())
                logger.info(f"   📅 {bulletin.bulletin_date}: {employment_count} EB + {family_count} Family categories")
        
    except Exception as e:
        logger.error(f"❌ Error testing historical range: {e}")

def test_url_generation():
    """Test URL generation functionality"""
    logger.info("\n=== Testing URL Generation ===")
    
    config = VisaConfig()
    parser = VisaBulletinParser(config)
    
    try:
        # Test URL generation
        url = parser.scraper.generate_historical_bulletin_url(2024, 6)
        logger.info(f"📎 Generated URL: {url}")
        
        # Test URL verification
        is_accessible = parser.scraper.verify_bulletin_url(url)
        logger.info(f"🔍 URL accessible: {is_accessible}")
        
        # Test getting URL list
        urls = parser.scraper.get_historical_bulletin_urls(2024, 2024)
        logger.info(f"📋 Found {len(urls)} URLs for 2024")
        
        # Show sample URLs
        for i, (url, year, month) in enumerate(urls[:3]):
            logger.info(f"   {i+1}. {year}-{month:02d}: {url}")
        
    except Exception as e:
        logger.error(f"❌ Error testing URL generation: {e}")

def main():
    """Run all historical parser tests"""
    logger.info("🚀 Starting historical visa bulletin parser tests...")
    
    # Run individual tests
    test_url_generation()
    test_single_historical_bulletin()
    test_historical_range()
    
    logger.info("\n✅ Historical parser testing complete!")

if __name__ == "__main__":
    main()