#!/usr/bin/env python
"""
Simple script to test the TradingAgents API
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
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

def test_analysis(ticker="AAPL"):
    """Test analysis endpoint"""
    print(f"Testing analysis endpoint with ticker: {ticker}")
    print("⏳ This may take 30-60 seconds...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"ticker": ticker}
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
            else:
                print("✅ Analysis completed successfully!")
                
                # Show available reports
                reports = [
                    'market_report', 'sentiment_report', 'news_report',
                    'fundamentals_report', 'final_trade_decision'
                ]
                available_reports = [r for r in reports if result.get(r)]
                print(f"✅ Available reports: {', '.join(available_reports)}")
        else:
            print(f"❌ Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Is the server running?")
        print("   Run: python run_api.py")
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

def main():
    print("🚀 TradingAgents API Test Suite")
    print(f"📍 Testing API at: {BASE_URL}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Test endpoints
    test_root()
    test_health()
    
    # Ask user if they want to test analysis
    user_input = input("Do you want to test the analysis endpoint? (y/n): ").lower()
    if user_input == 'y':
        ticker = input("Enter ticker to analyze (default: AAPL): ").strip().upper()
        if not ticker:
            ticker = "AAPL"
        test_analysis(ticker)
    
    print("-" * 50)
    print("✅ Testing complete!")

if __name__ == "__main__":
    main() 