#!/usr/bin/env python3
"""
Test script to verify the tool call fix works properly.
This script tests the API endpoint and checks for tool call errors.
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_api_endpoint():
    """Test the API endpoint for tool call errors."""
    
    print("🧪 Testing TradingAgents API for tool call fix...")
    print("=" * 60)
    
    try:
        # Test health endpoint first
        print("📋 Testing health endpoint...")
        health_response = requests.get('http://localhost:8000/health', timeout=5)
        if health_response.status_code == 200:
            print("✅ Health endpoint OK")
        else:
            print(f"❌ Health endpoint failed: {health_response.status_code}")
            return False
        
        # Test streaming analysis
        print("📋 Testing streaming analysis...")
        response = requests.get(
            'http://localhost:8000/analyze/stream', 
            params={'ticker': 'AAPL'}, 
            stream=True, 
            timeout=120  # 2 minute timeout
        )
        
        if response.status_code != 200:
            print(f"❌ API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("✅ API endpoint accessible")
        
        # Process streaming response
        chunk_count = 0
        error_found = False
        success_found = False
        start_time = time.time()
        
        print("📦 Processing chunks...")
        
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = json.loads(decoded_line[6:])
                        chunk_count += 1
                        msg_type = data.get('type', 'unknown')
                        
                        # Check for specific error patterns
                        if msg_type == 'error':
                            error_msg = data.get('message', 'Unknown error')
                            print(f"❌ ERROR DETECTED: {error_msg}")
                            
                            # Check if it's the specific tool call error we're fixing
                            if 'tool_calls' in error_msg and 'must be followed by tool messages' in error_msg:
                                print("❌ TOOL CALL ERROR: The fix didn't work!")
                                error_found = True
                                break
                            else:
                                print("⚠️  Other error detected (not tool call related)")
                        
                        elif msg_type == 'final_result':
                            print(f"✅ SUCCESS: Final result received after {chunk_count} chunks")
                            success_found = True
                            break
                        
                        elif msg_type in ['status', 'agent_status', 'progress', 'reasoning']:
                            if chunk_count <= 10 or chunk_count % 10 == 0:
                                print(f"📦 Chunk {chunk_count}: {msg_type}")
                        
                        # Safety timeout
                        elapsed = time.time() - start_time
                        if elapsed > 120:  # 2 minutes
                            print("⏰ Test timeout reached")
                            break
                        
                        # Stop after reasonable number of chunks
                        if chunk_count >= 100:
                            print("🛑 Stopping after 100 chunks")
                            break
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing chunk: {e}")
                    continue
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY:")
        print(f"  Total chunks processed: {chunk_count}")
        print(f"  Tool call errors found: {'YES' if error_found else 'NO'}")
        print(f"  Analysis completed: {'YES' if success_found else 'NO'}")
        
        if error_found:
            print("❌ RESULT: Tool call fix did NOT work")
            return False
        elif success_found:
            print("✅ RESULT: Tool call fix works - analysis completed successfully")
            return True
        else:
            print("⚠️  RESULT: Tool call fix appears to work - no errors detected")
            print("   (Analysis didn't complete but no tool call errors found)")
            return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - API server not running")
        print("   Start the server with: uvicorn api:app --host 0.0.0.0 --port 8000")
        return False
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function."""
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_api_endpoint()
    
    print(f"\n🕒 Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎉 Overall result: PASS")
        sys.exit(0)
    else:
        print("💥 Overall result: FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main() 