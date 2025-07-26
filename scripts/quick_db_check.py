#!/usr/bin/env python3
"""
Quick Database Check Script

Simple script to quickly check database contents and category coverage.

Usage:
    docker-compose exec web python scripts/quick_db_check.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from visa.database import VisaDatabase
from visa.repository import VisaBulletinRepository


def main():
    """Quick database status check"""
    print("🔍 QUICK DATABASE CHECK")
    print("=" * 40)
    
    try:
        # Database connection
        repo = VisaBulletinRepository()
        db = VisaDatabase()
        
        # Get basic stats
        stats = repo.get_statistics()
        print(f"📊 Database Statistics:")
        print(f"   Bulletins: {stats['bulletin_count']}")
        print(f"   Total entries: {stats['category_data_count']}")
        print(f"   Year range: {stats['year_range']}")
        print(f"   Categories tracked: {stats['categories_tracked']}")
        
        # Get category breakdown
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT category, COUNT(*) FROM category_data GROUP BY category ORDER BY category')
            categories = cursor.fetchall()
        
        print(f"\n📋 Category Breakdown:")
        eb_count = 0
        fb_count = 0
        
        for cat, count in categories:
            print(f"   {cat}: {count} entries")
            if cat.startswith('EB'):
                eb_count += 1
            elif cat.startswith('F'):
                fb_count += 1
        
        print(f"\n🎯 Summary:")
        print(f"   Employment-Based: {eb_count}/5 categories")
        print(f"   Family-Based: {fb_count}/5 categories")
        print(f"   Total: {len(categories)}/10 expected categories")
        
        if len(categories) == 10 and eb_count == 5 and fb_count == 5:
            print("\n✅ SUCCESS: All visa categories are present!")
        else:
            print(f"\n⚠️  WARNING: Expected 10 categories (5 EB + 5 FB), found {len(categories)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()