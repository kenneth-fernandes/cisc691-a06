#!/usr/bin/env python3
"""
Sample Data Viewer Script

View sample visa bulletin data to verify EB categories and dates.

Usage:
    docker-compose exec web python scripts/view_sample_data.py
    docker-compose exec web python scripts/view_sample_data.py --category EB-2
    docker-compose exec web python scripts/view_sample_data.py --with-dates-only
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from visa.database import VisaDatabase


def view_sample_data(category_filter=None, with_dates_only=False, limit=20):
    """View sample data from the database"""
    
    db = VisaDatabase()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT vb.year, vb.month, cd.category, cd.country, 
                   cd.final_action_date, cd.status
            FROM category_data cd
            JOIN visa_bulletins vb ON cd.bulletin_id = vb.id
        '''
        
        conditions = []
        params = []
        
        if category_filter:
            conditions.append('cd.category = %s')
            params.append(category_filter)
        
        if with_dates_only:
            conditions.append('cd.final_action_date IS NOT NULL')
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY cd.category, vb.year DESC, vb.month DESC'
        query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            print("No data found matching criteria")
            return
        
        print(f"📅 SAMPLE VISA BULLETIN DATA ({len(results)} entries)")
        print("=" * 70)
        print(f"{'Bulletin':<10} {'Category':<6} {'Country':<12} {'Date':<12} {'Status':<10}")
        print("-" * 70)
        
        for row in results:
            year, month, cat, country, date, status = row
            bulletin = f"{year}-{month:02d}"
            date_str = str(date) if date else "None"
            print(f"{bulletin:<10} {cat:<6} {country:<12} {date_str:<12} {status:<10}")


def view_category_summary():
    """Show summary of all categories"""
    
    db = VisaDatabase()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get category summary with date statistics
        cursor.execute('''
            SELECT category, 
                   COUNT(*) as total_entries,
                   COUNT(CASE WHEN final_action_date IS NOT NULL THEN 1 END) as entries_with_dates,
                   MIN(final_action_date) as earliest_date,
                   MAX(final_action_date) as latest_date
            FROM category_data 
            GROUP BY category 
            ORDER BY category
        ''')
        
        results = cursor.fetchall()
        
        print("📊 CATEGORY SUMMARY")
        print("=" * 80)
        print(f"{'Category':<8} {'Total':<6} {'W/Dates':<8} {'%':<6} {'Earliest':<12} {'Latest':<12}")
        print("-" * 80)
        
        total_entries = 0
        total_with_dates = 0
        
        for row in results:
            cat, total, with_dates, earliest, latest = row
            percentage = (with_dates / total * 100) if total > 0 else 0
            earliest_str = str(earliest) if earliest else "None"
            latest_str = str(latest) if latest else "None"
            
            print(f"{cat:<8} {total:<6} {with_dates:<8} {percentage:<5.1f}% {earliest_str:<12} {latest_str:<12}")
            
            total_entries += total
            total_with_dates += with_dates
        
        overall_percentage = (total_with_dates / total_entries * 100) if total_entries > 0 else 0
        
        print("-" * 80)
        print(f"{'TOTAL':<8} {total_entries:<6} {total_with_dates:<8} {overall_percentage:<5.1f}%")


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="View sample visa bulletin data")
    parser.add_argument('--category', help='Filter by specific category (e.g., EB-2, F1)')
    parser.add_argument('--with-dates-only', action='store_true', 
                       help='Show only entries with actual dates')
    parser.add_argument('--limit', type=int, default=20, 
                       help='Number of records to show (default: 20)')
    parser.add_argument('--summary', action='store_true',
                       help='Show category summary instead of sample data')
    
    args = parser.parse_args()
    
    try:
        if args.summary:
            view_category_summary()
        else:
            view_sample_data(
                category_filter=args.category,
                with_dates_only=args.with_dates_only,
                limit=args.limit
            )
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()