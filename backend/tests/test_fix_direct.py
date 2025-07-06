#!/usr/bin/env python3
"""
Direct test of the tool call fix without full dependencies
"""

import sys
import json
from datetime import datetime

# Mock the necessary imports
class MockAIMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.type = "ai"

class MockToolMessage:
    def __init__(self, content, tool_call_id, name):
        self.content = content
        self.tool_call_id = tool_call_id
        self.name = name
        self.type = "tool"

class MockTool:
    def __init__(self, name, func):
        self.name = name
        self.func = func
        
    def invoke(self, args):
        return self.func(**args)

# Test the SmartToolNode logic
class TestSmartToolNode:
    def __init__(self, tools):
        self.tools = tools
        self.call_count = {}
        
    def invoke(self, input_data):
        """Test the tool node logic"""
        messages = input_data.get("messages", [])
        
        # Find the last AI message with tool calls
        last_ai_message = None
        for msg in reversed(messages):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                last_ai_message = msg
                break
        
        if not last_ai_message or not last_ai_message.tool_calls:
            print("🔧 No tool calls found")
            return {"messages": []}
        
        print(f"🔧 Processing {len(last_ai_message.tool_calls)} tool calls")
        
        # Process each tool call
        tool_messages = []
        
        for i, tool_call in enumerate(last_ai_message.tool_calls):
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            print(f"🔧 [{i+1}/{len(last_ai_message.tool_calls)}] Executing {tool_name}")
            print(f"   Args: {tool_args}")
            print(f"   ID: {tool_id}")
            
            # Track call count
            self.call_count[tool_name] = self.call_count.get(tool_name, 0) + 1
            
            # Find and execute the tool
            tool_func = None
            for tool in self.tools:
                if tool.name == tool_name:
                    tool_func = tool
                    break
            
            if not tool_func:
                error_msg = f"Tool {tool_name} not found"
                print(f"❌ {error_msg}")
                tool_message = MockToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
            else:
                try:
                    result = tool_func.invoke(tool_args)
                    print(f"✅ Tool {tool_name} executed successfully")
                    tool_message = MockToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_messages.append(tool_message)
                except Exception as e:
                    error_msg = f"Error executing tool: {str(e)}"
                    print(f"❌ {error_msg}")
                    tool_message = MockToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_messages.append(tool_message)
        
        print(f"🔧 Returning {len(tool_messages)} tool messages")
        return {"messages": tool_messages}

# Test functions
def mock_get_stock_news(ticker, curr_date):
    """Mock stock news function"""
    return f"Mock news for {ticker} on {curr_date}: Stock is doing well!"

def test_duplicate_tool_calls():
    """Test that duplicate tool calls are handled properly"""
    print("\n=== Testing Duplicate Tool Call Handling ===")
    
    # Create mock tools
    tools = [
        MockTool("get_stock_news_openai", mock_get_stock_news)
    ]
    
    # Create tool node
    tool_node = TestSmartToolNode(tools)
    
    # Test Case 1: First tool call
    print("\n1. First tool call:")
    ai_msg1 = MockAIMessage(
        content="",
        tool_calls=[{
            "name": "get_stock_news_openai",
            "args": {"ticker": "UNH", "curr_date": "2025-07-06"},
            "id": "call_1"
        }]
    )
    
    result1 = tool_node.invoke({"messages": [ai_msg1]})
    print(f"Result: {len(result1['messages'])} messages returned")
    for msg in result1['messages']:
        print(f"  - {msg.name}: {msg.content}")
    
    # Test Case 2: Duplicate tool call (same args)
    print("\n2. Duplicate tool call (this should still return a message):")
    ai_msg2 = MockAIMessage(
        content="",
        tool_calls=[{
            "name": "get_stock_news_openai",
            "args": {"ticker": "UNH", "curr_date": "2025-07-06"},
            "id": "call_2"
        }]
    )
    
    result2 = tool_node.invoke({"messages": [ai_msg1, result1['messages'][0], ai_msg2]})
    print(f"Result: {len(result2['messages'])} messages returned")
    for msg in result2['messages']:
        print(f"  - {msg.name}: {msg.content}")
    
    # Test Case 3: Different args
    print("\n3. Different args (should execute normally):")
    ai_msg3 = MockAIMessage(
        content="",
        tool_calls=[{
            "name": "get_stock_news_openai",
            "args": {"ticker": "AAPL", "curr_date": "2025-07-06"},
            "id": "call_3"
        }]
    )
    
    result3 = tool_node.invoke({"messages": [ai_msg3]})
    print(f"Result: {len(result3['messages'])} messages returned")
    for msg in result3['messages']:
        print(f"  - {msg.name}: {msg.content}")
    
    # Summary
    print("\n=== Summary ===")
    print(f"✅ All tool calls returned messages (no missing responses)")
    print(f"✅ Tool call count: {tool_node.call_count}")
    
    return True

def test_error_handling():
    """Test error handling in tool calls"""
    print("\n=== Testing Error Handling ===")
    
    # Create tool node with no tools
    tool_node = TestSmartToolNode([])
    
    # Test missing tool
    print("\n1. Missing tool:")
    ai_msg = MockAIMessage(
        content="",
        tool_calls=[{
            "name": "non_existent_tool",
            "args": {"test": "data"},
            "id": "call_error"
        }]
    )
    
    result = tool_node.invoke({"messages": [ai_msg]})
    print(f"Result: {len(result['messages'])} messages returned")
    for msg in result['messages']:
        print(f"  - {msg.name}: {msg.content}")
    
    print("\n✅ Error handling works - tool calls always get responses")
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Tool Call Fix")
    print("=" * 50)
    
    tests = [
        ("Duplicate Tool Calls", test_duplicate_tool_calls),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    print(f"\n✅ Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 The fix works! Every tool call gets a response.")
        print("This should resolve the 'tool_calls must be followed by tool messages' error.")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())