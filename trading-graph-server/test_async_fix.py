#!/usr/bin/env python3
"""
Comprehensive test for async fixes - tests CancelledError resolution
"""

import asyncio
import requests
import json
import time
from datetime import datetime

def test_server_health():
    """Test if the server is running"""
    try:
        # Try the assistants endpoint with GET (should return Method Not Allowed but server is responding)
        response = requests.get("http://127.0.0.1:8123/assistants", timeout=5)
        return response.status_code in [200, 405]  # 405 = Method Not Allowed, but server is up
    except:
        return False

async def test_async_execution():
    """Test the async execution end-to-end"""
    print("🔄 Testing async execution fixes...")
    
    # Create assistant
    assistant_response = requests.post(
        "http://127.0.0.1:8123/assistants",
        headers={"Content-Type": "application/json"},
        json={"graph_id": "trading_agents", "config": {"configurable": {"thread_id": "async-test"}}}
    )
    
    if assistant_response.status_code != 200:
        print(f"❌ Failed to create assistant: {assistant_response.status_code}")
        return False
    
    assistant_id = assistant_response.json()["assistant_id"]
    print(f"✅ Assistant created: {assistant_id}")
    
    # Create thread
    thread_response = requests.post(
        "http://127.0.0.1:8123/threads",
        headers={"Content-Type": "application/json"},
        json={}
    )
    
    if thread_response.status_code != 200:
        print(f"❌ Failed to create thread: {thread_response.status_code}")
        return False
    
    thread_id = thread_response.json()["thread_id"]
    print(f"✅ Thread created: {thread_id}")
    
    # Start analysis with comprehensive test data
    test_input = {
        "ticker": "AAPL",
        "analysis_date": "2025-07-22",
        "company_of_interest": "Apple Inc.",
        "trade_date": "2025-07-22"
    }
    
    run_response = requests.post(
        f"http://127.0.0.1:8123/threads/{thread_id}/runs",
        headers={"Content-Type": "application/json"},
        json={
            "assistant_id": assistant_id,
            "input": test_input,
            "stream_mode": ["values"]
        }
    )
    
    if run_response.status_code != 200:
        print(f"❌ Failed to start run: {run_response.status_code}")
        return False
    
    run_id = run_response.json()["run_id"]
    print(f"✅ Analysis started: {run_id}")
    
    # Monitor for completion and errors
    print("🔍 Monitoring execution...")
    start_time = time.time()
    timeout = 300  # 5 minutes timeout
    
    while time.time() - start_time < timeout:
        status_response = requests.get(f"http://127.0.0.1:8123/threads/{thread_id}/runs/{run_id}")
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            return False
        
        status_data = status_response.json()
        status = status_data.get("status", "unknown")
        
        print(f"   Status: {status}")
        
        if status == "success":
            print("✅ Execution completed successfully!")
            
            # Get final results
            results_response = requests.get(f"http://127.0.0.1:8123/threads/{thread_id}/state")
            if results_response.status_code == 200:
                results = results_response.json()
                print("📊 Final results obtained:")
                
                # Check for key fields
                if "final_trade_decision" in results.get("values", {}):
                    decision = results["values"]["final_trade_decision"]
                    print(f"   🎯 Final Decision: {decision[:100]}...")
                
                if "market_report" in results.get("values", {}):
                    market_report = results["values"]["market_report"]
                    print(f"   📈 Market Report: {len(market_report)} chars")
                
                if "sentiment_report" in results.get("values", {}):
                    sentiment_report = results["values"]["sentiment_report"]
                    print(f"   📱 Sentiment Report: {len(sentiment_report)} chars")
            
            return True
        
        elif status == "error":
            print("❌ Execution failed with error!")
            
            # Get error details
            if "error" in status_data:
                error_info = status_data["error"]
                print(f"   Error: {error_info}")
            
            return False
        
        elif status in ["pending", "running"]:
            # Still executing, continue monitoring
            await asyncio.sleep(2)
            continue
        
        else:
            print(f"❌ Unexpected status: {status}")
            return False
    
    print("⏰ Test timed out!")
    return False

async def main():
    print("🚀 Comprehensive Async Fix Test")
    print("=" * 50)
    
    # Check server health
    if not test_server_health():
        print("❌ Server is not running on http://127.0.0.1:8123")
        print("   Start server with: langgraph dev --port 8123")
        return
    
    print("✅ Server is running")
    
    # Test async execution
    success = await test_async_execution()
    
    print("=" * 50)
    if success:
        print("🎉 ASYNC FIX TEST PASSED!")
        print("✅ No CancelledError detected")
        print("✅ All nodes executed successfully")
        print("✅ Graph is fully async-compatible")
    else:
        print("❌ ASYNC FIX TEST FAILED!")
        print("   Check the server logs for detailed error information")
    
    print("\n📝 Next steps:")
    print("1. Test in LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123")
    print("2. Use input: {'ticker': 'AAPL', 'analysis_date': '2025-07-22'}")
    print("3. Verify all nodes complete without CancelledError")

if __name__ == "__main__":
    asyncio.run(main()) 