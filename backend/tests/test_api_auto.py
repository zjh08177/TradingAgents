#!/usr/bin/env python
"""
Automated test script for TradingAgents API
"""
import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analysis(ticker="AAPL"):
    """Test analysis endpoint"""
    print(f"Testing analysis endpoint with ticker: {ticker}")
    print("⏳ This may take 5-10 minutes for comprehensive analysis...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"ticker": ticker},
            timeout=600  # 10 minute timeout
        )
        end_time = time.time()
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Time taken: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ticker: {result['ticker']}")
            print(f"✅ Date: {result['analysis_date']}")
            print(f"✅ Signal: {result.get('processed_signal', 'N/A')}")
            
            if result.get('error'):
                print(f"⚠️  Error in analysis: {result['error']}")
                return False
            else:
                print("✅ Analysis completed successfully!")
                
                # Show available reports
                reports = [
                    'market_report', 'sentiment_report', 'news_report',
                    'fundamentals_report', 'final_trade_decision'
                ]
                available_reports = [r for r in reports if result.get(r)]
                print(f"✅ Available reports: {', '.join(available_reports)}")
                
                # Check if all expected reports are present
                missing_reports = [r for r in reports if not result.get(r)]
                if missing_reports:
                    print(f"⚠️  Missing reports: {', '.join(missing_reports)}")
                else:
                    print("✅ All expected reports are present!")
                
                return True
        else:
            print(f"❌ Error response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is the server running?")
        print("   Run: python run_api.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 TradingAgents API Automated Test Suite")
    print(f"📍 Testing API at: {BASE_URL}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Test endpoints
    success_count = 0
    total_tests = 3
    
    if test_root():
        success_count += 1
    print()
    
    if test_health():
        success_count += 1
    print()
    
    if test_analysis("AAPL"):
        success_count += 1
    print()
    
    print("-" * 50)
    print(f"✅ Tests completed: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 