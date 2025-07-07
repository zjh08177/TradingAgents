#!/usr/bin/env python3
"""
Test script to analyze TradingAgents API with detailed timing and logging
"""
import requests
import json
import time
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"

def test_analysis_with_timing(ticker="AAPL"):
    """Test the analysis endpoint with detailed timing"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting analysis for {ticker}")
    print(f"📅 Time: {datetime.now()}")
    print(f"{'='*60}\n")
    
    # Start timing
    start_time = time.time()
    
    # Make the request
    print(f"📤 Sending request to {BASE_URL}/analyze")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"ticker": ticker},
            timeout=1200  # 20 minutes timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Request completed in {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print summary
            print(f"\n{'='*60}")
            print("📋 ANALYSIS SUMMARY")
            print(f"{'='*60}")
            print(f"Ticker: {data.get('ticker', 'N/A')}")
            print(f"Date: {data.get('analysis_date', 'N/A')}")
            print(f"Signal: {data.get('processed_signal', 'N/A')}")
            print(f"Error: {data.get('error', 'None')}")
            
            # Check each report
            print(f"\n{'='*60}")
            print("📊 REPORTS STATUS")
            print(f"{'='*60}")
            reports = {
                "Market Report": data.get("market_report"),
                "Sentiment Report": data.get("sentiment_report"),
                "News Report": data.get("news_report"),
                "Fundamentals Report": data.get("fundamentals_report"),
                "Investment Plan": data.get("investment_plan"),
                "Trader Investment Plan": data.get("trader_investment_plan"),
                "Final Trade Decision": data.get("final_trade_decision")
            }
            
            for name, report in reports.items():
                if report:
                    print(f"✅ {name}: Generated ({len(str(report))} chars)")
                else:
                    print(f"❌ {name}: Missing or None")
            
            # Look for specific errors
            print(f"\n{'='*60}")
            print("🔍 ERROR ANALYSIS")
            print(f"{'='*60}")
            
            # Check for the Risk Judge error
            if data.get("investment_plan"):
                if "I'm sorry, but I need the text" in str(data.get("investment_plan", "")):
                    print("❌ Risk Judge Error: Missing input text")
                    print("   The Risk Judge is not receiving proper input from the aggregator")
            
            # Save full response for analysis
            with open("test_analysis_full_output.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Full response saved to test_analysis_full_output.json")
            
            return data
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 20 minutes")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_analysis_with_timing(ticker)