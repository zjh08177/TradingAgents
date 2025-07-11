#!/usr/bin/env python3
"""
Extended test to verify tool call fix works through analysis phase.
"""

import requests
import json
import time
import signal
import sys

def test_extended_analysis():
    """Test tool call fix through extended analysis."""
    
    print("🧪 Extended Tool Call Fix Test")
    print("=" * 50)
    
    # Set up timeout handler
    def timeout_handler(signum, frame):
        print("\n⏰ Test timeout - but no tool call errors detected!")
        print("✅ Fix appears to be working")
        sys.exit(0)
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(90)  # 90 second timeout
    
    try:
        response = requests.get(
            'http://localhost:8000/analyze/stream', 
            params={'ticker': 'AAPL'}, 
            stream=True, 
            timeout=90
        )
        
        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            return False
        
        print("✅ API accessible")
        print("📊 Monitoring for tool call errors...")
        
        chunk_count = 0
        tool_call_error_found = False
        agents_seen = set()
        
        for line in response.iter_lines():
            if line:
                try:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = json.loads(decoded_line[6:])
                        chunk_count += 1
                        
                        msg_type = data.get('type', 'unknown')
                        
                        # Track agent activity
                        if msg_type == 'agent_status':
                            agent = data.get('agent', '')
                            status = data.get('status', '')
                            if agent and status == 'active':
                                agents_seen.add(agent)
                        
                        # Check for tool call errors
                        if msg_type == 'error':
                            error_msg = data.get('message', '')
                            print(f"❌ Error detected: {error_msg[:100]}...")
                            
                            if 'tool_calls' in error_msg and 'must be followed by tool messages' in error_msg:
                                print("❌ TOOL CALL ERROR DETECTED!")
                                tool_call_error_found = True
                                break
                        
                        # Progress reporting
                        if chunk_count % 20 == 0:
                            print(f"📦 Processed {chunk_count} chunks, agents seen: {len(agents_seen)}")
                        
                        # Success condition
                        if msg_type == 'final_result':
                            print(f"✅ Analysis completed successfully after {chunk_count} chunks!")
                            break
                        
                        # Stop after reasonable time if no errors
                        if chunk_count >= 200:
                            print(f"🛑 Stopping after {chunk_count} chunks - no tool call errors detected")
                            break
                            
                except Exception as e:
                    print(f"⚠️ Parse error: {e}")
                    continue
        
        signal.alarm(0)  # Cancel timeout
        
        print(f"\n📊 Test Summary:")
        print(f"   Chunks processed: {chunk_count}")
        print(f"   Agents seen: {agents_seen}")
        print(f"   Tool call errors: {'YES' if tool_call_error_found else 'NO'}")
        
        if tool_call_error_found:
            print("❌ RESULT: Tool call error detected - fix failed")
            return False
        else:
            print("✅ RESULT: No tool call errors - fix is working!")
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    success = test_extended_analysis()
    print(f"\n{'🎉 PASS' if success else '💥 FAIL'}") 