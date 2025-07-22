#!/usr/bin/env python3
"""
Example usage of the visa bulletin parser
"""
import asyncio
import logging
from src.visa.parser import VisaBulletinParser, ParsingError
from src.visa.config import VisaConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_current_bulletin():
    """Demo parsing the current bulletin"""
    logger.info("🚀 Starting current visa bulletin parsing...")
    
    config = VisaConfig()
    parser = VisaBulletinParser(config)
    
    try:
        # Parse current bulletin from State Department website
        bulletin = parser.parse_current_bulletin()
        
        if bulletin:
            logger.info(f"✅ Successfully parsed bulletin for {bulletin.bulletin_date}")
            logger.info(f"📅 Fiscal Year: {bulletin.fiscal_year}")
            logger.info(f"🔗 Source: {bulletin.source_url}")
            logger.info(f"📊 Categories found: {len(bulletin.categories)}")
            
            # Display some category data
            logger.info("\n📋 Sample category data:")
            for i, category in enumerate(bulletin.categories[:5]):  # Show first 5
                logger.info(f"  {i+1}. {category.category.value} - {category.country.value}: "
                          f"{category.final_action_date or category.status.value}")
            
            if len(bulletin.categories) > 5:
                logger.info(f"  ... and {len(bulletin.categories) - 5} more categories")
                
            # Show employment vs family breakdown
            employment_cats = bulletin.get_employment_categories()
            family_cats = bulletin.get_family_categories()
            
            logger.info(f"\n📈 Employment-based categories: {len(employment_cats)}")
            logger.info(f"👨‍👩‍👧‍👦 Family-based categories: {len(family_cats)}")
            
        else:
            logger.warning("❌ No bulletin data found")
            
    except ParsingError as e:
        logger.error(f"❌ Parsing error: {e}")
        logger.error(f"   Error type: {e.error_type}")
        if e.source_url:
            logger.error(f"   Source URL: {e.source_url}")
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

def demo_historical_bulletins():
    """Demo parsing historical bulletins"""
    logger.info("\n" + "="*60)
    logger.info("🕒 Starting historical visa bulletin parsing...")
    
    config = VisaConfig()
    parser = VisaBulletinParser(config)
    
    try:
        # Parse a specific historical bulletin
        logger.info("\n📅 Parsing specific bulletin (June 2024)...")
        june_bulletin = parser.parse_bulletin_by_date(2024, 6)
        
        if june_bulletin:
            logger.info(f"✅ June 2024 bulletin: {len(june_bulletin.categories)} categories")
        
        # Parse a range of historical bulletins (last 6 months of 2024)
        logger.info(f"\n📊 Parsing historical bulletins for 2024...")
        historical_bulletins = parser.parse_historical_bulletins(
            start_year=2024, 
            end_year=2024,
            verify_urls=True,
            max_workers=3
        )
        
        if historical_bulletins:
            logger.info(f"\n📈 Historical analysis summary:")
            logger.info(f"   📅 Date range: {historical_bulletins[0].bulletin_date} to {historical_bulletins[-1].bulletin_date}")
            logger.info(f"   📊 Total bulletins: {len(historical_bulletins)}")
            
            # Calculate some basic statistics
            total_categories = sum(len(b.categories) for b in historical_bulletins)
            avg_categories = total_categories / len(historical_bulletins) if historical_bulletins else 0
            
            logger.info(f"   📋 Average categories per bulletin: {avg_categories:.1f}")
            
            # Show recent trends
            logger.info(f"\n📋 Recent bulletins:")
            for bulletin in historical_bulletins[-3:]:  # Show last 3
                employment_count = len(bulletin.get_employment_categories())
                family_count = len(bulletin.get_family_categories())
                logger.info(f"   📅 {bulletin.bulletin_date.strftime('%Y-%m')}: "
                          f"{employment_count} EB + {family_count} Family categories")
                
        else:
            logger.warning("❌ No historical bulletins found")
            
    except ParsingError as e:
        logger.error(f"❌ Historical parsing error: {e}")
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in historical parsing: {e}")

def main():
    """Example usage of the visa bulletin parser with both current and historical parsing"""
    
    # Demo current bulletin parsing
    demo_current_bulletin()
    
    # Demo historical bulletin parsing
    demo_historical_bulletins()
    
    logger.info("\n" + "="*60)
    logger.info("🎉 Visa bulletin parser demo complete!")
    logger.info("\nNew capabilities added:")
    logger.info("  ✅ Current bulletin parsing (as before)")
    logger.info("  ✅ Historical bulletin parsing by date range")
    logger.info("  ✅ Single historical bulletin parsing")
    logger.info("  ✅ Parallel processing for bulk operations")
    logger.info("  ✅ URL verification and error handling")

if __name__ == "__main__":
    main()