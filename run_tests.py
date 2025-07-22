#!/usr/bin/env python3
"""
Test runner script for the visa bulletin prediction system
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install -r requirements.txt")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run test suite for visa bulletin system")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--mock", action="store_true", help="Run only mock tests")
    parser.add_argument("--slow", action="store_true", help="Run slow/network tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-cov", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (unit + integration, no network)")
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    # Determine which tests to run
    test_commands = []
    
    if args.fast:
        # Fast tests: unit + integration (no network) + mock
        cmd = base_cmd + ["tests/", "-m", "unit or (integration and not network) or mock"]
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        if args.html_cov:
            cmd.extend(["--cov=src", "--cov-report=html"])
        test_commands.append((cmd, "Fast Test Suite (Unit + Integration + Mock)"))
        
    elif args.unit:
        cmd = base_cmd + ["tests/", "-m", "unit"]
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        test_commands.append((cmd, "Unit Tests"))
        
    elif args.integration:
        cmd = base_cmd + ["tests/", "-m", "integration"]
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        test_commands.append((cmd, "Integration Tests"))
        
    elif args.mock:
        cmd = base_cmd + ["tests/", "-m", "mock"]
        if args.coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        test_commands.append((cmd, "Mock Tests"))
        
    elif args.slow:
        cmd = base_cmd + ["tests/", "-m", "slow or network"]
        test_commands.append((cmd, "Slow/Network Tests"))
        
    else:
        # Run all tests by category
        commands = [
            (base_cmd + ["tests/", "-m", "unit", "--cov=src", "--cov-report=term-missing"], "Unit Tests"),
            (base_cmd + ["tests/", "-m", "integration and not network", "--cov=src", "--cov-append", "--cov-report=term-missing"], "Integration Tests (No Network)"),
            (base_cmd + ["tests/", "-m", "mock", "--cov=src", "--cov-append", "--cov-report=term-missing"], "Mock Tests"),
        ]
        
        if args.html_cov:
            commands[-1][0].extend(["--cov-report=html"])
            
        test_commands.extend(commands)
        
        # Optionally run slow tests
        if args.slow:
            test_commands.append((base_cmd + ["tests/", "-m", "slow or network"], "Slow/Network Tests"))
    
    print("🚀 Starting Visa Bulletin Test Suite")
    print(f"📁 Working directory: {Path.cwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Run all test commands
    all_passed = True
    results = []
    
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
        if not success:
            all_passed = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {description}")
    
    if args.coverage or args.html_cov:
        print(f"\n📈 Coverage reports generated:")
        if args.coverage:
            print("   • Terminal coverage report (above)")
        if args.html_cov:
            print("   • HTML coverage report: htmlcov/index.html")
    
    print(f"\n🎯 Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\n💡 Tips:")
        print("   • Run with --verbose for more details")
        print("   • Check test output above for specific failures")
        print("   • Network tests may fail due to external dependencies")
        sys.exit(1)
    
    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()