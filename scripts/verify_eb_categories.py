#!/usr/bin/env python3
"""
Employment-Based Categories Verification Script

This script verifies that the Employment-Based visa categories (EB-1 through EB-5) 
are being properly parsed and stored in the database.

Usage:
    docker-compose exec web python scripts/verify_eb_categories.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from visa.database import VisaDatabase
from visa.repository import VisaBulletinRepository
from visa.parser import VisaBulletinParser
from visa.config import VisaConfig


class EBCategoryVerifier:
    """Comprehensive verification of Employment-Based category parsing"""
    
    def __init__(self):
        self.db = VisaDatabase()
        self.repo = VisaBulletinRepository()
        self.parser = VisaBulletinParser(VisaConfig())
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0
            }
        }
    
    def log_test(self, test_name: str, passed: bool, message: str, details: Any = None):
        """Log test result"""
        self.results['tests'][test_name] = {
            'passed': passed,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total_tests'] += 1
        if passed:
            self.results['summary']['passed_tests'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results['summary']['failed_tests'] += 1
            print(f"❌ {test_name}: {message}")
            
        if details:
            print(f"   Details: {details}")
    
    def test_database_connection(self):
        """Test 1: Database connection and basic stats"""
        try:
            stats = self.repo.get_statistics()
            self.log_test(
                "Database Connection",
                True,
                f"Connected successfully - {stats['bulletin_count']} bulletins",
                stats
            )
            return stats
        except Exception as e:
            self.log_test(
                "Database Connection", 
                False, 
                f"Connection failed: {str(e)}"
            )
            return None
    
    def test_category_coverage(self):
        """Test 2: Check if all 10 visa categories are present"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT category FROM category_data ORDER BY category')
                categories = [row[0] for row in cursor.fetchall()]
            
            expected_categories = ['EB-1', 'EB-2', 'EB-3', 'EB-4', 'EB-5', 'F1', 'F2A', 'F2B', 'F3', 'F4']
            missing_categories = [cat for cat in expected_categories if cat not in categories]
            extra_categories = [cat for cat in categories if cat not in expected_categories]
            
            eb_categories = [cat for cat in categories if cat.startswith('EB')]
            fb_categories = [cat for cat in categories if cat.startswith('F')]
            
            passed = len(missing_categories) == 0 and len(categories) == 10
            
            details = {
                'found_categories': categories,
                'eb_categories': eb_categories,
                'fb_categories': fb_categories,
                'missing_categories': missing_categories,
                'extra_categories': extra_categories
            }
            
            if passed:
                message = f"All 10 categories found: {len(eb_categories)} EB + {len(fb_categories)} FB"
            else:
                message = f"Missing categories: {missing_categories}, Extra: {extra_categories}"
            
            self.log_test("Category Coverage", passed, message, details)
            return categories
            
        except Exception as e:
            self.log_test("Category Coverage", False, f"Test failed: {str(e)}")
            return []
    
    def test_category_distribution(self):
        """Test 3: Check category entry distribution"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT category, COUNT(*) as count, 
                           COUNT(CASE WHEN final_action_date IS NOT NULL THEN 1 END) as with_dates
                    FROM category_data 
                    GROUP BY category 
                    ORDER BY category
                ''')
                distribution = cursor.fetchall()
            
            category_stats = {}
            total_entries = 0
            total_with_dates = 0
            
            for cat, count, with_dates in distribution:
                category_stats[cat] = {
                    'total_entries': count,
                    'entries_with_dates': with_dates,
                    'date_success_rate': (with_dates / count * 100) if count > 0 else 0
                }
                total_entries += count
                total_with_dates += with_dates
            
            overall_date_success = (total_with_dates / total_entries * 100) if total_entries > 0 else 0
            
            # Check if EB categories have reasonable entry counts
            eb_entries = sum(stats['total_entries'] for cat, stats in category_stats.items() if cat.startswith('EB'))
            fb_entries = sum(stats['total_entries'] for cat, stats in category_stats.items() if cat.startswith('F'))
            
            passed = eb_entries > 0 and fb_entries > 0 and overall_date_success > 50
            
            details = {
                'category_stats': category_stats,
                'total_entries': total_entries,
                'total_with_dates': total_with_dates,
                'overall_date_success_rate': round(overall_date_success, 1),
                'eb_entries': eb_entries,
                'fb_entries': fb_entries
            }
            
            message = f"Entries: {total_entries} total, {total_with_dates} with dates ({overall_date_success:.1f}%)"
            
            self.log_test("Category Distribution", passed, message, details)
            return category_stats
            
        except Exception as e:
            self.log_test("Category Distribution", False, f"Test failed: {str(e)}")
            return {}
    
    def test_single_bulletin_parsing(self):
        """Test 4: Parse a single bulletin and verify EB categories"""
        try:
            # Try to parse a recent bulletin
            bulletin = self.parser.parse_bulletin_by_date(2024, 8)
            
            if not bulletin:
                self.log_test("Single Bulletin Parsing", False, "Failed to parse bulletin 2024-08")
                return None
            
            # Analyze categories in the bulletin
            category_counts = {}
            eb_data = []
            
            for cat_data in bulletin.categories:
                cat_name = cat_data.category.value
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
                
                if cat_name.startswith('EB'):
                    eb_data.append({
                        'category': cat_name,
                        'country': cat_data.country.value,
                        'final_action_date': str(cat_data.final_action_date) if cat_data.final_action_date else None,
                        'status': cat_data.status
                    })
            
            eb_categories_found = [cat for cat in category_counts.keys() if cat.startswith('EB')]
            total_categories = len(category_counts)
            
            passed = len(eb_categories_found) >= 5 and total_categories >= 10
            
            details = {
                'bulletin_date': f"{bulletin.year}-{bulletin.month:02d}",
                'total_categories_in_bulletin': total_categories,
                'category_counts': category_counts,
                'eb_categories_found': eb_categories_found,
                'sample_eb_data': eb_data[:5]  # First 5 EB entries
            }
            
            message = f"Found {len(eb_categories_found)} EB categories in {total_categories} total categories"
            
            self.log_test("Single Bulletin Parsing", passed, message, details)
            return bulletin
            
        except Exception as e:
            self.log_test("Single Bulletin Parsing", False, f"Parsing failed: {str(e)}")
            return None
    
    def test_eb_data_samples(self):
        """Test 5: Verify EB data with actual dates"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get sample EB data with dates
                cursor.execute('''
                    SELECT vb.year, vb.month, cd.category, cd.country, 
                           cd.final_action_date, cd.status
                    FROM category_data cd
                    JOIN visa_bulletins vb ON cd.bulletin_id = vb.id
                    WHERE cd.category LIKE 'EB%'
                    ORDER BY cd.category, vb.year DESC, vb.month DESC
                    LIMIT 20
                ''')
                
                eb_samples = cursor.fetchall()
                
                # Count EB entries with dates
                cursor.execute('''
                    SELECT COUNT(*) as total, 
                           COUNT(CASE WHEN final_action_date IS NOT NULL THEN 1 END) as with_dates
                    FROM category_data 
                    WHERE category LIKE 'EB%'
                ''')
                
                total_eb, eb_with_dates = cursor.fetchone()
                eb_date_success = (eb_with_dates / total_eb * 100) if total_eb > 0 else 0
            
            passed = total_eb > 0 and eb_date_success > 30  # At least 30% should have dates
            
            sample_data = []
            for row in eb_samples:
                year, month, cat, country, date, status = row
                sample_data.append({
                    'bulletin': f"{year}-{month:02d}",
                    'category': cat,
                    'country': country,
                    'date': str(date) if date else None,
                    'status': status
                })
            
            details = {
                'total_eb_entries': total_eb,
                'eb_entries_with_dates': eb_with_dates,
                'eb_date_success_rate': round(eb_date_success, 1),
                'sample_data': sample_data
            }
            
            message = f"EB entries: {total_eb} total, {eb_with_dates} with dates ({eb_date_success:.1f}%)"
            
            self.log_test("EB Data Samples", passed, message, details)
            return sample_data
            
        except Exception as e:
            self.log_test("EB Data Samples", False, f"Test failed: {str(e)}")
            return []
    
    def test_parser_logic(self):
        """Test 6: Test parser logic directly"""
        try:
            from visa.parser import BulletinTableParser
            
            parser = BulletinTableParser()
            
            # Test category parsing with different formats
            test_cases = [
                ('1st', 'EB-1'),
                ('2nd', 'EB-2'), 
                ('3rd', 'EB-3'),
                ('Other Workers', 'EB-3'),
                ('4th', 'EB-4'),
                ('Certain Religious Workers', 'EB-4'),
                ('5th Unreserved', 'EB-5'),
                ('F1', 'F1'),
                ('F2A', 'F2A')
            ]
            
            results = []
            passed_count = 0
            
            for input_text, expected in test_cases:
                try:
                    result = parser._parse_category(input_text)
                    actual = result.value if result else None
                    passed = actual == expected
                    
                    if passed:
                        passed_count += 1
                    
                    results.append({
                        'input': input_text,
                        'expected': expected,
                        'actual': actual,
                        'passed': passed
                    })
                except Exception as e:
                    results.append({
                        'input': input_text,
                        'expected': expected,
                        'actual': None,
                        'error': str(e),
                        'passed': False
                    })
            
            overall_passed = passed_count >= len(test_cases) * 0.8  # 80% success rate
            
            details = {
                'test_cases': results,
                'passed_count': passed_count,
                'total_cases': len(test_cases),
                'success_rate': round(passed_count / len(test_cases) * 100, 1)
            }
            
            message = f"Parser logic: {passed_count}/{len(test_cases)} test cases passed"
            
            self.log_test("Parser Logic", overall_passed, message, details)
            return results
            
        except Exception as e:
            self.log_test("Parser Logic", False, f"Test failed: {str(e)}")
            return []
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("🧪 EMPLOYMENT-BASED CATEGORIES VERIFICATION")
        print("=" * 60)
        print()
        
        # Run all tests
        self.test_database_connection()
        self.test_category_coverage()
        self.test_category_distribution()
        self.test_single_bulletin_parsing()
        self.test_eb_data_samples()
        self.test_parser_logic()
        
        # Calculate final success rate
        total = self.results['summary']['total_tests']
        passed = self.results['summary']['passed_tests']
        self.results['summary']['success_rate'] = round((passed / total * 100), 1) if total > 0 else 0
        
        print()
        print("📊 VERIFICATION SUMMARY")
        print("=" * 30)
        print(f"Total tests: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed_tests']}")
        print(f"Failed: {self.results['summary']['failed_tests']}")
        print(f"Success rate: {self.results['summary']['success_rate']}%")
        
        if self.results['summary']['success_rate'] >= 80:
            print("\n🎉 VERIFICATION SUCCESSFUL!")
            print("✅ Employment-Based categories are working correctly!")
        else:
            print("\n❌ VERIFICATION FAILED!")
            print("⚠️  Some tests failed - Employment-Based categories need attention")
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Save verification results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/eb_verification_{timestamp}.json"
        
        Path(filename).parent.mkdir(exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Results saved to: {filename}")
        return filename


def main():
    """Main verification function"""
    verifier = EBCategoryVerifier()
    
    try:
        results = verifier.run_all_tests()
        report_file = verifier.save_results()
        
        # Exit with appropriate code
        if results['summary']['success_rate'] >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n⏹️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()