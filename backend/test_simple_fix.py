#!/usr/bin/env python3
"""
Simple test to verify tool call fix is working.
"""

import requests
import json
import time

def test_tool_call_fix():
    """Test if tool call fix prevents the specific error."""
    
    print("🧪 Simple Tool Call Fix Test")
    print("=" * 40)
    
    try:
        # Test with a simple ticker
        response = requests.get(
            'http://localhost:8000/analyze/stream', 
            params={'ticker': 'AAPL'}, 
            stream=True, 
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            return False
        
        print("✅ API accessible")
        
        chunk_count = 0
        tool_call_error_found = False
        
        # Read first 20 chunks to check for tool call errors
        for line in response.iter_lines():
            if line and chunk_count < 20:
                try:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = json.loads(decoded_line[6:])
                        chunk_count += 1
                        
                        msg_type = data.get('type', 'unknown')
                        print(f"📦 Chunk {chunk_count}: {msg_type}")
                        
                        # Check for the specific tool call error
                        if msg_type == 'error':
                            error_msg = data.get('message', '')
                            print(f"❌ Error: {error_msg}")
                            
                            if 'tool_calls' in error_msg and 'must be followed by tool messages' in error_msg:
                                print("❌ TOOL CALL ERROR DETECTED - Fix failed!")
                                tool_call_error_found = True
                                break
                        
                        # If we get through some chunks without the error, the fix is working
                        if chunk_count >= 15:
                            break
                            
                except Exception as e:
                    print(f"⚠️ Parse error: {e}")
                    continue
            else:
                break
        
        if tool_call_error_found:
            print("❌ RESULT: Tool call error still occurs")
            return False
        else:
            print("✅ RESULT: No tool call errors detected in first 15 chunks")
            print("   Fix appears to be working!")
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_tool_call_fix()
    print(f"\n{'🎉 PASS' if success else '💥 FAIL'}") 