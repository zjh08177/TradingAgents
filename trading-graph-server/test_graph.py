#!/usr/bin/env python3
"""
Test script for Trading Graph Server
Demonstrates the trading analysis workflow via LangGraph API
"""

import requests
import json
import time
import sys

# Server configuration
BASE_URL = "http://127.0.0.1:8123"
HEADERS = {"Content-Type": "application/json"}

def test_server_health():
    """Test if the LangGraph server is running"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def create_assistant():
    """Create an assistant with the trading_agents graph"""
    data = {"graph_id": "trading_agents"}
    response = requests.post(f"{BASE_URL}/assistants", json=data, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["assistant_id"]
    else:
        raise Exception(f"Failed to create assistant: {response.text}")

def create_thread():
    """Create a new thread for the trading analysis"""
    response = requests.post(f"{BASE_URL}/threads", json={}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["thread_id"]
    else:
        raise Exception(f"Failed to create thread: {response.text}")

def run_trading_analysis(assistant_id, thread_id, ticker="TSLA"):
    """Run trading analysis for a given ticker"""
    data = {
        "assistant_id": assistant_id,
        "input": {
            "ticker": ticker,
            "analysis_date": "2025-07-22",
            "company_of_interest": ticker,
            "trade_date": "2025-07-22",
            "fundamentals_report": "",
            "market_analysis_report": "",
            "news_sentiment_report": "",
            "social_media_report": "",
            "research_report": "",
            "risk_assessment": "",
            "trading_recommendation": "",
            "confidence_score": 0.0
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/runs", 
        json=data, 
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return response.json()["run_id"]
    else:
        raise Exception(f"Failed to start run: {response.text}")

def wait_for_completion(thread_id, run_id, timeout=120):
    """Wait for the trading analysis to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{BASE_URL}/threads/{thread_id}/runs/{run_id}")
        
        if response.status_code == 200:
            status = response.json()["status"]
            print(f"Run status: {status}")
            
            if status == "success":
                return True
            elif status in ["failed", "cancelled"]:
                print(f"Run failed with status: {status}")
                return False
        
        time.sleep(2)
    
    print("Timeout waiting for completion")
    return False

def get_results(thread_id):
    """Get the final trading analysis results"""
    response = requests.get(f"{BASE_URL}/threads/{thread_id}/state")
    
    if response.status_code == 200:
        return response.json()["values"]
    else:
        raise Exception(f"Failed to get results: {response.text}")

def print_results(results, ticker):
    """Print the trading analysis results in a formatted way"""
    print(f"\n{'='*80}")
    print(f"🎯 TRADING ANALYSIS RESULTS FOR {ticker}")
    print(f"{'='*80}")
    
    print(f"📈 Ticker: {results.get('ticker', 'N/A')}")
    print(f"📅 Analysis Date: {results.get('analysis_date', 'N/A')}")
    print(f"🎖️ Confidence Score: {results.get('confidence_score', 0.0)}")
    
    print(f"\n📊 REPORTS:")
    print(f"{'─'*40}")
    
    reports = [
        ("🏢 Fundamentals", "fundamentals_report"),
        ("📈 Market Analysis", "market_analysis_report"), 
        ("📰 News Sentiment", "news_sentiment_report"),
        ("💬 Social Media", "social_media_report"),
        ("📋 Research Plan", "research_report"),
        ("⚠️ Risk Assessment", "risk_assessment"),
        ("💰 Trading Decision", "trading_recommendation")
    ]
    
    for name, key in reports:
        report = results.get(key, "No data")
        print(f"\n{name}:")
        print(f"{report[:200]}{'...' if len(report) > 200 else ''}")

def main():
    """Main test function"""
    print("🚀 Testing Trading Graph Server")
    print("=" * 50)
    
    # Check if server is running
    print("1. Checking server health...")
    if not test_server_health():
        print("❌ Server is not running. Please start with:")
        print("   cd trading-graph-server && source venv/bin/activate")
        print("   langgraph dev --allow-blocking")
        sys.exit(1)
    print("✅ Server is running")
    
    try:
        # Create assistant
        print("\n2. Creating assistant...")
        assistant_id = create_assistant()
        print(f"✅ Assistant created: {assistant_id}")
        
        # Create thread
        print("\n3. Creating thread...")
        thread_id = create_thread()
        print(f"✅ Thread created: {thread_id}")
        
        # Run analysis
        ticker = sys.argv[1] if len(sys.argv) > 1 else "TSLA"
        print(f"\n4. Starting trading analysis for {ticker}...")
        run_id = run_trading_analysis(assistant_id, thread_id, ticker)
        print(f"✅ Analysis started: {run_id}")
        
        # Wait for completion
        print("\n5. Waiting for analysis to complete...")
        if wait_for_completion(thread_id, run_id):
            print("✅ Analysis completed successfully")
            
            # Get and display results
            print("\n6. Retrieving results...")
            results = get_results(thread_id)
            print_results(results, ticker)
            
            print(f"\n{'='*80}")
            print("🎉 TRADING GRAPH SERVER TEST COMPLETED SUCCESSFULLY!")
            print("🎨 View in LangGraph Studio:")
            print(f"   https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
            print(f"📚 API Documentation:")
            print(f"   http://127.0.0.1:2024/docs")
            print(f"{'='*80}")
            
        else:
            print("❌ Analysis failed to complete")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 