#!/usr/bin/env python3
"""
Comprehensive test script for TradingAgents API
Tests all functionality and provides detailed timing information
"""
import requests
import json
import time
from datetime import datetime
import sys
import os

# API configuration
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"📍 {title}")
    print(f"{'='*60}")

def test_health_endpoint():
    """Test the health check endpoint"""
    print_section("Testing Health Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print_section("Testing Root Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Root endpoint passed: {response.json()}")
            return True
        else:
            print(f"❌ Root endpoint failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_analysis_endpoint(ticker="AAPL"):
    """Test the analysis endpoint with detailed timing"""
    print_section(f"Testing Analysis Endpoint for {ticker}")
    
    print(f"📤 Sending POST request to {BASE_URL}/analyze")
    print(f"📊 Payload: {{'ticker': '{ticker}'}}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"ticker": ticker},
            timeout=1800  # 30 minutes timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Request completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analysis summary
            print_section("ANALYSIS SUMMARY")
            print(f"Ticker: {data.get('ticker', 'N/A')}")
            print(f"Date: {data.get('analysis_date', 'N/A')}")
            print(f"Signal: {data.get('processed_signal', 'N/A')}")
            print(f"Error: {data.get('error', 'None')}")
            
            # Report status
            print_section("REPORTS STATUS")
            reports = {
                "Market Report": data.get("market_report"),
                "Sentiment Report": data.get("sentiment_report"),
                "News Report": data.get("news_report"),
                "Fundamentals Report": data.get("fundamentals_report"),
                "Investment Plan": data.get("investment_plan"),
                "Trader Investment Plan": data.get("trader_investment_plan"),
                "Final Trade Decision": data.get("final_trade_decision")
            }
            
            all_reports_present = True
            for name, report in reports.items():
                if report:
                    print(f"✅ {name}: Generated ({len(str(report))} chars)")
                    # Show preview of each report
                    preview = str(report)[:200].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
                else:
                    print(f"❌ {name}: Missing or None")
                    all_reports_present = False
            
            # Error analysis
            print_section("ERROR ANALYSIS")
            
            # Check for specific errors
            errors_found = []
            
            # Check for API key error
            if data.get("error") and "API key" in str(data.get("error")):
                errors_found.append("API Key Error: Invalid or missing API key")
            
            # Check for Risk Judge error
            for report_name, report_content in reports.items():
                if report_content and "I'm sorry, but I need the text" in str(report_content):
                    errors_found.append(f"Risk Judge Error in {report_name}: Missing input data")
            
            if errors_found:
                print("❌ Errors found:")
                for error in errors_found:
                    print(f"   - {error}")
            else:
                print("✅ No errors detected in reports")
            
            # Save full response
            output_file = f"test_output_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Full response saved to {output_file}")
            
            # Overall test result
            print_section("TEST RESULT")
            if all_reports_present and not errors_found and data.get("processed_signal"):
                print("✅ TEST PASSED")
                print("   - All reports generated")
                print("   - No errors detected")
                print("   - Signal produced")
                return True
            else:
                print("❌ TEST FAILED")
                if not all_reports_present:
                    print("   - Some reports missing")
                if errors_found:
                    print("   - Errors detected in processing")
                if not data.get("processed_signal"):
                    print("   - No signal produced")
                return False
                
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"\n❌ Error during request: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print(f"\n{'='*60}")
    print(f"🚀 TradingAgents API Comprehensive Test Suite")
    print(f"📅 {datetime.now()}")
    print(f"🌐 API URL: {BASE_URL}")
    print(f"{'='*60}")
    
    # Check if API is running
    if not test_health_endpoint():
        print("\n❌ API is not running! Please start the API server first.")
        print("Run: python3 run_api.py")
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_root_endpoint():
        tests_passed += 1
    
    if test_health_endpoint():
        tests_passed += 1
    
    if test_analysis_endpoint("AAPL"):
        tests_passed += 1
    
    # Final summary
    print_section("FINAL SUMMARY")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total_tests - tests_passed} TESTS FAILED!")
        return False

if __name__ == "__main__":
    # Allow ticker override from command line
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        print(f"Testing with ticker: {ticker}")
        success = test_analysis_endpoint(ticker)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)