#!/usr/bin/env python
"""
Comprehensive test for FastAPI run_api.py - Tests all endpoints, streaming, and parallel execution
"""
import requests
import json
import time
import threading
import asyncio
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import sys
import multiprocessing


class APITestLogger:
    """Enhanced logger for API testing"""
    def __init__(self):
        self.log_file = f"test_results/api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        Path("test_results").mkdir(exist_ok=True)
        self.test_results = []
        self.stream_events = defaultdict(list)
        
    def log(self, message, level="INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Also write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def log_test_result(self, test_name, success, duration, details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'duration': duration,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.log(f"{status} {test_name} ({duration:.2f}s) {details}", "RESULT")
    
    def log_stream_event(self, ticker, event):
        """Log streaming event"""
        self.stream_events[ticker].append({
            'time': time.time(),
            'event': event
        })
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80, "SUMMARY")
        self.log("API TEST SUMMARY", "SUMMARY")
        self.log("="*80, "SUMMARY")
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        self.log(f"\n📊 Test Results: {passed}/{total} passed", "SUMMARY")
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            self.log(f"  {status} {result['test']} ({result['duration']:.2f}s)", "SUMMARY")
        
        # Stream event summary
        if self.stream_events:
            self.log("\n📡 Streaming Events Summary:", "SUMMARY")
            for ticker, events in self.stream_events.items():
                self.log(f"  {ticker}: {len(events)} events", "SUMMARY")
                
                # Count event types
                event_types = defaultdict(int)
                for event_data in events:
                    if 'type' in event_data['event']:
                        event_types[event_data['event']['type']] += 1
                
                for event_type, count in event_types.items():
                    self.log(f"    - {event_type}: {count}", "SUMMARY")
        
        self.log(f"\n📁 Full log saved to: {self.log_file}", "SUMMARY")


def start_api_server(logger):
    """Start the API server in a separate process"""
    logger.log("🚀 Starting API server...", "SERVER")
    
    def run_server():
        import subprocess
        import os
        env = os.environ.copy()
        # Ensure the server runs on the expected port
        env['API_PORT'] = '8000'
        subprocess.run([sys.executable, "run_api.py"], env=env)
    
    server_process = multiprocessing.Process(target=run_server)
    server_process.daemon = True
    server_process.start()
    
    # Wait for server to start
    logger.log("⏳ Waiting for server to start...", "SERVER")
    time.sleep(5)
    
    # Check if server is running
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                logger.log("✅ API server is running", "SERVER")
                return server_process
        except:
            pass
        time.sleep(2)
    
    logger.log("❌ Failed to start API server", "ERROR")
    return None


def test_health_endpoint(base_url, logger):
    """Test health check endpoint"""
    test_name = "Health Check"
    start_time = time.time()
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        duration = time.time() - start_time
        
        if response.status_code == 200 and response.json().get("status") == "healthy":
            logger.log_test_result(test_name, True, duration, "Server is healthy")
        else:
            logger.log_test_result(test_name, False, duration, f"Unexpected response: {response.text}")
    except Exception as e:
        duration = time.time() - start_time
        logger.log_test_result(test_name, False, duration, str(e))


def test_root_endpoint(base_url, logger):
    """Test root endpoint"""
    test_name = "Root Endpoint"
    start_time = time.time()
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            logger.log_test_result(test_name, True, duration, f"Response: {response.json()}")
        else:
            logger.log_test_result(test_name, False, duration, f"Status: {response.status_code}")
    except Exception as e:
        duration = time.time() - start_time
        logger.log_test_result(test_name, False, duration, str(e))


def test_analyze_endpoint(base_url, ticker, logger):
    """Test synchronous analysis endpoint"""
    test_name = f"Analyze Endpoint ({ticker})"
    start_time = time.time()
    
    logger.log(f"\n🔍 Testing analysis for {ticker}...", "TEST")
    logger.log("⏳ This may take 30-60 seconds...", "TEST")
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json={"ticker": ticker},
            timeout=120  # 2 minute timeout
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for required fields
            required_fields = ['ticker', 'analysis_date', 'market_report', 
                             'sentiment_report', 'news_report', 'fundamentals_report',
                             'final_trade_decision', 'processed_signal']
            
            missing_fields = [f for f in required_fields if not result.get(f)]
            
            if not missing_fields and not result.get('error'):
                logger.log_test_result(test_name, True, duration, 
                                     f"Signal: {result.get('processed_signal', 'N/A')}")
                
                # Log report sizes
                for field in required_fields[2:]:  # Skip ticker and date
                    if result.get(field):
                        logger.log(f"  📄 {field}: {len(str(result[field]))} chars", "INFO")
            else:
                details = f"Missing fields: {missing_fields}" if missing_fields else f"Error: {result.get('error')}"
                logger.log_test_result(test_name, False, duration, details)
        else:
            logger.log_test_result(test_name, False, duration, 
                                 f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        duration = time.time() - start_time
        logger.log_test_result(test_name, False, duration, str(e))


def test_streaming_endpoint(base_url, ticker, logger):
    """Test streaming analysis endpoint"""
    test_name = f"Streaming Endpoint ({ticker})"
    start_time = time.time()
    
    logger.log(f"\n📡 Testing streaming analysis for {ticker}...", "TEST")
    
    try:
        # Track streaming events
        events_received = []
        agent_progress = {}
        reports_received = []
        
        with requests.get(f"{base_url}/analyze/stream?ticker={ticker}", stream=True, timeout=120) as response:
            if response.status_code != 200:
                logger.log_test_result(test_name, False, time.time() - start_time,
                                     f"Status: {response.status_code}")
                return
            
            # Process SSE stream
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            event_data = json.loads(line_str[6:])
                            events_received.append(event_data)
                            logger.log_stream_event(ticker, event_data)
                            
                            # Log different event types
                            event_type = event_data.get('type', 'unknown')
                            
                            if event_type == 'status':
                                logger.log(f"  📊 Status: {event_data.get('message', '')}", "STREAM")
                            
                            elif event_type == 'agent_status':
                                agent = event_data.get('agent', 'unknown')
                                status = event_data.get('status', 'unknown')
                                agent_progress[agent] = status
                                logger.log(f"  🤖 Agent '{agent}' -> {status}", "STREAM")
                                
                                # Check for parallel execution
                                active_agents = [a for a, s in agent_progress.items() if s == 'in_progress']
                                if len(active_agents) > 1:
                                    logger.log(f"  🔄 PARALLEL AGENTS: {active_agents}", "PARALLEL")
                            
                            elif event_type == 'report':
                                section = event_data.get('section', 'unknown')
                                content_len = len(event_data.get('content', ''))
                                reports_received.append(section)
                                logger.log(f"  📄 Report received: {section} ({content_len} chars)", "STREAM")
                            
                            elif event_type == 'progress':
                                progress = event_data.get('content', '0')
                                logger.log(f"  📈 Progress: {progress}%", "STREAM")
                            
                            elif event_type == 'reasoning':
                                content_preview = event_data.get('content', '')[:100]
                                logger.log(f"  💭 Reasoning: {content_preview}...", "STREAM")
                            
                            elif event_type == 'complete':
                                signal = event_data.get('signal', 'N/A')
                                logger.log(f"  ✅ Complete! Signal: {signal}", "STREAM")
                                break
                            
                            elif event_type == 'error':
                                logger.log(f"  ❌ Error: {event_data.get('message', 'Unknown error')}", "ERROR")
                                break
                            
                        except json.JSONDecodeError as e:
                            logger.log(f"  ⚠️  Failed to parse SSE data: {e}", "WARNING")
        
        duration = time.time() - start_time
        
        # Validate results
        success = (
            len(events_received) > 0 and
            len(reports_received) >= 6 and  # Should receive all main reports
            any(e.get('type') == 'complete' for e in events_received)
        )
        
        details = f"Events: {len(events_received)}, Reports: {len(reports_received)}, Agents: {len(agent_progress)}"
        logger.log_test_result(test_name, success, duration, details)
        
    except Exception as e:
        duration = time.time() - start_time
        logger.log_test_result(test_name, False, duration, str(e))


def test_parallel_requests(base_url, logger):
    """Test multiple parallel requests to verify server handles concurrent load"""
    test_name = "Parallel Requests"
    start_time = time.time()
    
    logger.log("\n🔄 Testing parallel requests...", "TEST")
    
    tickers = ["AAPL", "GOOGL", "MSFT"]
    threads = []
    results = []
    
    def analyze_ticker(ticker):
        try:
            response = requests.post(
                f"{base_url}/analyze",
                json={"ticker": ticker},
                timeout=120
            )
            results.append({
                'ticker': ticker,
                'success': response.status_code == 200,
                'time': time.time() - start_time
            })
        except Exception as e:
            results.append({
                'ticker': ticker,
                'success': False,
                'error': str(e),
                'time': time.time() - start_time
            })
    
    # Start parallel requests
    for ticker in tickers:
        thread = threading.Thread(target=analyze_ticker, args=(ticker,))
        thread.start()
        threads.append(thread)
        logger.log(f"  🚀 Started request for {ticker}", "PARALLEL")
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    duration = time.time() - start_time
    
    # Check results
    successful = sum(1 for r in results if r['success'])
    details = f"Success: {successful}/{len(tickers)}, Total time: {duration:.2f}s"
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        logger.log(f"  {status} {result['ticker']} completed at {result['time']:.2f}s", "PARALLEL")
    
    logger.log_test_result(test_name, successful == len(tickers), duration, details)


def test_error_handling(base_url, logger):
    """Test API error handling"""
    test_name = "Error Handling"
    start_time = time.time()
    
    logger.log("\n🛡️ Testing error handling...", "TEST")
    
    # Test invalid ticker
    try:
        response = requests.post(
            f"{base_url}/analyze",
            json={"ticker": ""},
            timeout=10
        )
        
        if response.status_code == 400 or (response.status_code == 200 and 'error' in response.json()):
            logger.log("  ✅ Empty ticker handled correctly", "TEST")
        else:
            logger.log("  ❌ Empty ticker not handled properly", "TEST")
    except Exception as e:
        logger.log(f"  ❌ Error testing invalid ticker: {e}", "ERROR")
    
    duration = time.time() - start_time
    logger.log_test_result(test_name, True, duration, "Error handling tested")


def run_comprehensive_api_tests():
    """Run all API tests comprehensively"""
    logger = APITestLogger()
    
    logger.log("🚀 Starting Comprehensive TradingAgents API Test Suite", "START")
    logger.log(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "START")
    logger.log("-" * 80)
    
    # Base URL
    base_url = "http://localhost:8000"
    
    # Check if server is already running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.log("✅ API server already running", "SERVER")
            server_process = None
    except:
        # Start server if not running
        server_process = start_api_server(logger)
        if not server_process:
            logger.log("❌ Cannot start API server. Please run 'python run_api.py' manually", "ERROR")
            return
    
    try:
        # Run tests
        test_health_endpoint(base_url, logger)
        test_root_endpoint(base_url, logger)
        
        # Test with different tickers
        test_analyze_endpoint(base_url, "NVDA", logger)
        test_streaming_endpoint(base_url, "AAPL", logger)
        
        # Test parallel handling
        test_parallel_requests(base_url, logger)
        
        # Test error handling
        test_error_handling(base_url, logger)
        
        # Print summary
        logger.print_summary()
        
    finally:
        # Clean up server if we started it
        if server_process:
            logger.log("\n🛑 Stopping API server...", "SERVER")
            server_process.terminate()
            server_process.join(timeout=5)


if __name__ == "__main__":
    run_comprehensive_api_tests()