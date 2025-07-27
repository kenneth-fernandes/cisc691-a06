#!/usr/bin/env python3
"""
Manual API testing script for verification and debugging
"""
import requests
import json
import time
import sys
from typing import Dict, Any
import argparse


class APITester:
    """Manual API testing utility"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
    
    def test_connection(self) -> bool:
        """Test basic API connection"""
        print("🔗 Testing API connection...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API connection successful")
                return True
            else:
                print(f"❌ API connection failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ API connection error: {e}")
            return False
    
    def test_health_endpoints(self):
        """Test health and info endpoints"""
        print("\n🏥 Testing health endpoints...")
        
        # Root endpoint
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"Root endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Version: {data.get('version', 'Unknown')}")
                print(f"  Message: {data.get('message', 'None')}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Health check
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"Health endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {data.get('status', 'Unknown')}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
    
    def test_agent_endpoints(self):
        """Test agent chat endpoints"""
        print("\n🤖 Testing agent endpoints...")
        
        test_cases = [
            {
                "name": "Basic chat",
                "data": {
                    "message": "Hello, how are you?",
                    "session_id": "test-session-1"
                }
            },
            {
                "name": "Chat with config",
                "data": {
                    "message": "Tell me about EB-2 visas",
                    "session_id": "test-session-2",
                    "config": {
                        "provider": "google",
                        "temperature": 0.7
                    }
                }
            },
            {
                "name": "Follow-up message",
                "data": {
                    "message": "What about the current trends?",
                    "session_id": "test-session-1"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/agent/chat",
                    json=test_case['data']
                )
                duration = time.time() - start_time
                
                print(f"    Status: {response.status_code}")
                print(f"    Duration: {duration:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    Session ID: {data.get('session_id', 'None')}")
                    print(f"    Response length: {len(data.get('response', ''))}")
                    print(f"    Response time: {data.get('response_time', 'None')}s")
                else:
                    print(f"    Error: {response.text}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print("\n📊 Testing analytics endpoints...")
        
        # Test basic info endpoints
        info_endpoints = [
            "/api/analytics/categories",
            "/api/analytics/countries",
            "/api/analytics/stats"
        ]
        
        for endpoint in info_endpoints:
            print(f"\n  Testing: {endpoint}")
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'categories' in endpoint:
                        print(f"    Employment-based: {len(data.get('employment_based', []))}")
                        print(f"    Family-based: {len(data.get('family_based', []))}")
                    elif 'countries' in endpoint:
                        print(f"    Countries: {len(data.get('countries', []))}")
                    elif 'stats' in endpoint:
                        print(f"    Total bulletins: {data.get('total_bulletins', 'Unknown')}")
                        print(f"    Year range: {data.get('year_range', 'Unknown')}")
                else:
                    print(f"    Error: {response.text}")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        # Test bulletins endpoint
        print(f"\n  Testing: /api/analytics/bulletins")
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/bulletins")
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    Bulletins count: {data.get('count', 'Unknown')}")
                print(f"    Year range: {data.get('year_range', 'Unknown')}")
            else:
                print(f"    Error: {response.text}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test specific bulletin
        print(f"\n  Testing: /api/analytics/bulletins/2024/8")
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/bulletins/2024/8")
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    Fiscal year: {data.get('fiscal_year', 'Unknown')}")
                print(f"    Categories: {len(data.get('categories', []))}")
            elif response.status_code == 404:
                print("    No bulletin found for 2024/8 (expected if no data)")
            else:
                print(f"    Error: {response.text}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test historical data
        print(f"\n  Testing: /api/analytics/historical")
        try:
            response = self.session.get(
                f"{self.base_url}/api/analytics/historical",
                params={"category": "EB2", "country": "India"}
            )
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    Data points: {data.get('data_points', 'Unknown')}")
                print(f"    Category: {data.get('category', 'Unknown')}")
                print(f"    Country: {data.get('country', 'Unknown')}")
            else:
                print(f"    Error: {response.text}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Test trend analysis
        print(f"\n  Testing: /api/analytics/trends")
        try:
            response = self.session.post(
                f"{self.base_url}/api/analytics/trends",
                json={
                    "category": "EB-2",
                    "country": "India",
                    "years_back": 3
                }
            )
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"    Category: {data.get('category', 'Unknown')}")
                print(f"    Country: {data.get('country', 'Unknown')}")
                analysis = data.get('analysis', {})
                print(f"    Trend: {analysis.get('trend', 'Unknown')}")
            else:
                print(f"    Error: {response.text}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n⚠️  Testing error handling...")
        
        error_tests = [
            {
                "name": "Invalid endpoint",
                "method": "GET",
                "url": "/api/nonexistent",
                "expected": 404
            },
            {
                "name": "Invalid HTTP method",
                "method": "GET",
                "url": "/api/agent/chat",
                "expected": 405
            },
            {
                "name": "Missing required field",
                "method": "POST",
                "url": "/api/agent/chat",
                "data": {"session_id": "test"},
                "expected": 422
            },
            {
                "name": "Invalid category",
                "method": "POST",
                "url": "/api/analytics/trends",
                "data": {
                    "category": "INVALID",
                    "country": "India",
                    "years_back": 3
                },
                "expected": 400
            }
        ]
        
        for test in error_tests:
            print(f"\n  Testing: {test['name']}")
            try:
                if test['method'] == 'GET':
                    response = self.session.get(f"{self.base_url}{test['url']}")
                else:
                    response = self.session.post(
                        f"{self.base_url}{test['url']}",
                        json=test.get('data', {})
                    )
                
                print(f"    Status: {response.status_code}")
                print(f"    Expected: {test['expected']}")
                
                if response.status_code == test['expected']:
                    print("    ✅ Error handling correct")
                else:
                    print("    ⚠️  Unexpected status code")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    def test_performance(self):
        """Test basic performance metrics"""
        print("\n⚡ Testing performance...")
        
        # Test response times
        endpoints = [
            "/health",
            "/api/analytics/categories",
            "/api/analytics/countries"
        ]
        
        for endpoint in endpoints:
            print(f"\n  Testing response time: {endpoint}")
            times = []
            
            for i in range(3):
                try:
                    start_time = time.time()
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    duration = time.time() - start_time
                    times.append(duration)
                    print(f"    Attempt {i+1}: {duration:.3f}s ({response.status_code})")
                except Exception as e:
                    print(f"    Attempt {i+1}: Error - {e}")
            
            if times:
                avg_time = sum(times) / len(times)
                print(f"    Average: {avg_time:.3f}s")
                
                if avg_time < 1.0:
                    print("    ✅ Good performance")
                elif avg_time < 3.0:
                    print("    ⚠️  Acceptable performance")
                else:
                    print("    ❌ Poor performance")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Starting comprehensive API tests...\n")
        
        if not self.test_connection():
            print("❌ Cannot connect to API. Please ensure the service is running.")
            return False
        
        self.test_health_endpoints()
        self.test_agent_endpoints()
        self.test_analytics_endpoints()
        self.test_error_handling()
        self.test_performance()
        
        print("\n✅ All tests completed!")
        return True
    
    def interactive_mode(self):
        """Interactive testing mode"""
        print("🔍 Interactive API testing mode")
        print("Available commands:")
        print("  1. Test connection")
        print("  2. Test health endpoints")
        print("  3. Test agent endpoints")
        print("  4. Test analytics endpoints")
        print("  5. Test error handling")
        print("  6. Test performance")
        print("  7. Run all tests")
        print("  8. Custom request")
        print("  q. Quit")
        
        while True:
            try:
                choice = input("\nEnter choice: ").strip()
                
                if choice == 'q':
                    break
                elif choice == '1':
                    self.test_connection()
                elif choice == '2':
                    self.test_health_endpoints()
                elif choice == '3':
                    self.test_agent_endpoints()
                elif choice == '4':
                    self.test_analytics_endpoints()
                elif choice == '5':
                    self.test_error_handling()
                elif choice == '6':
                    self.test_performance()
                elif choice == '7':
                    self.run_all_tests()
                elif choice == '8':
                    self.custom_request()
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
    
    def custom_request(self):
        """Make a custom API request"""
        try:
            method = input("HTTP method (GET/POST): ").strip().upper()
            endpoint = input("Endpoint (e.g., /api/analytics/categories): ").strip()
            
            if method == "POST":
                print("Enter JSON data (or press Enter for empty):")
                data_str = input().strip()
                data = json.loads(data_str) if data_str else {}
            else:
                data = None
            
            print(f"\nMaking request: {method} {self.base_url}{endpoint}")
            
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            else:
                print("Unsupported method")
                return
            
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except json.JSONDecodeError:
            print("Invalid JSON data")
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manual API testing script")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--suite", choices=["all", "health", "agent", "analytics", "error", "performance"], 
                       default="all", help="Test suite to run")
    
    args = parser.parse_args()
    
    tester = APITester(args.url)
    
    if args.interactive:
        tester.interactive_mode()
    else:
        if args.suite == "all":
            success = tester.run_all_tests()
            sys.exit(0 if success else 1)
        elif args.suite == "health":
            tester.test_health_endpoints()
        elif args.suite == "agent":
            tester.test_agent_endpoints()
        elif args.suite == "analytics":
            tester.test_analytics_endpoints()
        elif args.suite == "error":
            tester.test_error_handling()
        elif args.suite == "performance":
            tester.test_performance()


if __name__ == "__main__":
    main()