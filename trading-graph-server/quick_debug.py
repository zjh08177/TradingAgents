#!/usr/bin/env python3
"""
Quick debugging script - test individual components
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_graph_import():
    """Test if the graph can be imported"""
    print("🧪 Testing graph import...")
    try:
        from src.agent import graph
        print("✅ Graph imported successfully")
        print(f"📊 Graph type: {type(graph)}")
        return True
    except Exception as e:
        print(f"❌ Failed to import graph: {e}")
        return False

def test_trading_graph_class():
    """Test TradingAgentsGraph class instantiation and basic properties"""
    print("\n📊 TradingAgentsGraph Test")
    print("-----------------------------")
    
    try:
        from src.agent.graph.trading_graph import TradingAgentsGraph
        trading_graph = TradingAgentsGraph()
        print("✅ TradingAgentsGraph instance created")
        print(f"📊 Selected analysts: {trading_graph.selected_analysts}")
        print(f"📊 Configuration loaded: {'Yes' if trading_graph.config else 'No'}")
        print(f"📊 Graph compiled: {'Yes' if trading_graph.graph else 'No'}")
        return True
    except Exception as e:
        print(f"❌ TradingAgentsGraph test failed: {e}")
        return False

def test_api_keys():
    """Test if API keys are configured"""
    print("🧪 Testing API keys...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    keys_to_check = [
        ("OPENAI_API_KEY", "OpenAI"),
        ("FINNHUB_API_KEY", "Finnhub"),
        ("SERPER_API_KEY", "Serper"),
        ("LANGSMITH_API_KEY", "LangSmith")
    ]
    
    for key_name, service in keys_to_check:
        key_value = os.getenv(key_name)
        if key_value and key_value != f"your_{key_name.lower()}_here":
            print(f"✅ {service}: Configured")
        else:
            print(f"⚠️  {service}: Not configured")

def test_dependencies():
    """Test if required dependencies are installed"""
    print("🧪 Testing dependencies...")
    
    required_packages = [
        "langgraph",
        "langchain",
        "openai",
        "requests",
        "python-dotenv"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Missing")

def main():
    """Run all quick tests"""
    print("🚀 Quick Debugging Session")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("API Keys", test_api_keys),
        ("Graph Import", test_graph_import),
        ("TradingAgentsGraph Class", test_trading_graph_class)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Your graph is ready for testing!")
        print("🎨 Try LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123")
    else:
        print("\n🔧 Please fix the failing tests before proceeding")

if __name__ == "__main__":
    main() 