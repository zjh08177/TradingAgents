#!/usr/bin/env python3
"""
Advanced debugging script for Trading Graph Server
Provides detailed error analysis and step-by-step debugging
"""

import requests
import json
import time
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Server configuration
BASE_URL = "http://127.0.0.1:8123"
HEADERS = {"Content-Type": "application/json"}

def test_server_health():
    """Test if the LangGraph server is running with detailed diagnostics"""
    logger.info("🔍 Testing server health...")
    
    endpoints_to_test = [
        "/docs",
        "/openapi.json", 
        "/health"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            logger.info(f"✅ {endpoint}: {response.status_code}")
            if endpoint == "/openapi.json" and response.status_code == 200:
                api_info = response.json()
                logger.info(f"📋 API Title: {api_info.get('info', {}).get('title', 'Unknown')}")
                logger.info(f"📋 API Version: {api_info.get('info', {}).get('version', 'Unknown')}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {endpoint}: {str(e)}")
            return False
    
    return True

def create_assistant_with_debug():
    """Create an assistant with detailed error handling"""
    logger.info("🤖 Creating assistant...")
    
    data = {"graph_id": "trading_agents"}
    
    try:
        response = requests.post(f"{BASE_URL}/assistants", json=data, headers=HEADERS)
        logger.info(f"📡 Response status: {response.status_code}")
        logger.info(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            assistant_data = response.json()
            assistant_id = assistant_data["assistant_id"]
            logger.info(f"✅ Assistant created: {assistant_id}")
            logger.info(f"📋 Assistant details: {json.dumps(assistant_data, indent=2)}")
            return assistant_id
        else:
            logger.error(f"❌ Failed to create assistant: {response.status_code}")
            logger.error(f"❌ Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception creating assistant: {str(e)}")
        return None

def create_thread_with_debug():
    """Create a thread with detailed error handling"""
    logger.info("🧵 Creating thread...")
    
    try:
        response = requests.post(f"{BASE_URL}/threads", json={}, headers=HEADERS)
        logger.info(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            thread_data = response.json()
            thread_id = thread_data["thread_id"]
            logger.info(f"✅ Thread created: {thread_id}")
            logger.info(f"📋 Thread details: {json.dumps(thread_data, indent=2)}")
            return thread_id
        else:
            logger.error(f"❌ Failed to create thread: {response.status_code}")
            logger.error(f"❌ Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception creating thread: {str(e)}")
        return None

def run_trading_analysis_with_debug(assistant_id, thread_id, ticker="AAPL"):
    """Run trading analysis with comprehensive debugging"""
    logger.info(f"📈 Starting trading analysis for {ticker}...")
    
    # Create comprehensive input data
    input_data = {
        "ticker": ticker,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "company_of_interest": ticker,
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "fundamentals_report": "",
        "market_analysis_report": "",
        "news_sentiment_report": "",
        "social_media_report": "",
        "research_report": "",
        "risk_assessment": "",
        "trading_recommendation": "",
        "confidence_score": 0.0
    }
    
    data = {
        "assistant_id": assistant_id,
        "input": input_data
    }
    
    logger.info(f"📋 Input data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs", 
            json=data, 
            headers=HEADERS,
            timeout=30
        )
        
        logger.info(f"📡 Response status: {response.status_code}")
        logger.info(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            run_data = response.json()
            run_id = run_data["run_id"]
            logger.info(f"✅ Analysis started: {run_id}")
            logger.info(f"📋 Run details: {json.dumps(run_data, indent=2)}")
            return run_id
        else:
            logger.error(f"❌ Failed to start run: {response.status_code}")
            logger.error(f"❌ Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception starting run: {str(e)}")
        return None

def monitor_run_with_debug(thread_id, run_id, timeout=300):
    """Monitor run progress with detailed logging"""
    logger.info(f"⏱️ Monitoring run {run_id} (timeout: {timeout}s)")
    
    start_time = time.time()
    last_status = None
    status_count = {}
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/threads/{thread_id}/runs/{run_id}")
            
            if response.status_code == 200:
                run_data = response.json()
                current_status = run_data["status"]
                
                # Count status occurrences
                status_count[current_status] = status_count.get(current_status, 0) + 1
                
                # Log status changes
                if current_status != last_status:
                    logger.info(f"🔄 Status changed: {last_status} → {current_status}")
                    last_status = current_status
                
                # Log periodic updates
                if status_count[current_status] % 10 == 1:
                    elapsed = time.time() - start_time
                    logger.info(f"⏰ Status: {current_status} (elapsed: {elapsed:.1f}s)")
                
                # Check for completion
                if current_status == "success":
                    logger.info("✅ Run completed successfully!")
                    logger.info(f"📊 Final run data: {json.dumps(run_data, indent=2)}")
                    return True, run_data
                elif current_status in ["failed", "cancelled", "error"]:
                    logger.error(f"❌ Run failed with status: {current_status}")
                    logger.error(f"📊 Failed run data: {json.dumps(run_data, indent=2)}")
                    
                    # Try to get error details
                    if "error" in run_data:
                        logger.error(f"🔍 Error details: {run_data['error']}")
                    
                    return False, run_data
            else:
                logger.error(f"❌ Failed to get run status: {response.status_code}")
                logger.error(f"❌ Error response: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Exception monitoring run: {str(e)}")
        
        time.sleep(2)
    
    logger.error("⏰ Timeout waiting for completion")
    return False, None

def get_thread_state_with_debug(thread_id):
    """Get thread state with detailed analysis"""
    logger.info(f"📊 Getting thread state for {thread_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/threads/{thread_id}/state")
        
        if response.status_code == 200:
            state_data = response.json()
            logger.info("✅ Thread state retrieved successfully")
            logger.info(f"📋 State keys: {list(state_data.keys())}")
            
            if "values" in state_data:
                values = state_data["values"]
                logger.info(f"📊 Values keys: {list(values.keys()) if values else 'No values'}")
                
                # Log report lengths
                reports = [
                    "fundamentals_report", "market_analysis_report", 
                    "news_sentiment_report", "social_media_report",
                    "research_report", "risk_assessment", "trading_recommendation"
                ]
                
                for report in reports:
                    if report in values and values[report]:
                        logger.info(f"📄 {report}: {len(values[report])} characters")
                    else:
                        logger.info(f"📄 {report}: Empty or missing")
            
            return state_data
        else:
            logger.error(f"❌ Failed to get state: {response.status_code}")
            logger.error(f"❌ Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Exception getting state: {str(e)}")
        return None

def main():
    """Main debugging function with comprehensive error handling"""
    logger.info("🚀 Starting comprehensive debugging session")
    logger.info("=" * 80)
    
    # Test server health
    if not test_server_health():
        logger.error("❌ Server health check failed")
        sys.exit(1)
    
    # Create assistant
    assistant_id = create_assistant_with_debug()
    if not assistant_id:
        logger.error("❌ Failed to create assistant")
        sys.exit(1)
    
    # Create thread
    thread_id = create_thread_with_debug()
    if not thread_id:
        logger.error("❌ Failed to create thread")
        sys.exit(1)
    
    # Run analysis
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    run_id = run_trading_analysis_with_debug(assistant_id, thread_id, ticker)
    if not run_id:
        logger.error("❌ Failed to start analysis")
        sys.exit(1)
    
    # Monitor progress
    success, run_data = monitor_run_with_debug(thread_id, run_id)
    
    # Get final state regardless of success/failure
    final_state = get_thread_state_with_debug(thread_id)
    
    if success:
        logger.info("🎉 Debugging session completed successfully!")
        logger.info(f"🎨 View in Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123")
        logger.info(f"📚 API Docs: http://127.0.0.1:8123/docs")
    else:
        logger.error("❌ Debugging session completed with errors")
        logger.error("🔍 Check debug_test.log for detailed error information")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    main() 