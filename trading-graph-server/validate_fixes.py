#!/usr/bin/env python3
"""
Comprehensive validation script to ensure all fixes are working correctly.
Tests: bear_researcher, serper_utils, graph import, and langgraph compatibility.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_bear_researcher_import():
    """Test bear_researcher import and basic functionality"""
    print("🐻 Testing bear_researcher import...")
    try:
        from src.agent.researchers.bear_researcher import create_bear_researcher
        print("  ✅ bear_researcher import successful")
        return True
    except Exception as e:
        print(f"  ❌ bear_researcher import failed: {e}")
        return False

def test_serper_utils_import():
    """Test serper_utils import and log_data_fetch fix"""
    print("🌐 Testing serper_utils import...")
    try:
        from src.agent.dataflows.serper_utils import getNewsDataSerperAPI
        print("  ✅ serper_utils import successful")
        return True
    except Exception as e:
        print(f"  ❌ serper_utils import failed: {e}")
        return False

def test_graph_import():
    """Test full trading graph import"""
    print("📊 Testing trading graph import...")
    try:
        from src.agent.graph.trading_graph import TradingAgentsGraph
        print("  ✅ trading graph import successful")
        return True
    except Exception as e:
        print(f"  ❌ trading graph import failed: {e}")
        return False

def test_graph_creation():
    """Test creating a graph instance"""
    print("🏗️ Testing graph creation...")
    try:
        from src.agent.graph.trading_graph import TradingAgentsGraph
        
        # Mock minimal config
        config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
        }
        
        graph = TradingAgentsGraph(config)
        print("  ✅ graph creation successful")
        return True
    except Exception as e:
        print(f"  ❌ graph creation failed: {e}")
        return False

def test_bear_researcher_in_graph():
    """Test that bear_researcher is properly integrated in the graph"""
    print("🔗 Testing bear_researcher integration in graph...")
    try:
        from src.agent.graph.trading_graph import TradingAgentsGraph
        
        config = {
            "model": "gpt-4o-mini", 
            "temperature": 0.7,
        }
        
        graph = TradingAgentsGraph(config)
        compiled_graph = graph.create_graph()
        
        # Check if bear_researcher node exists
        nodes = list(compiled_graph.nodes.keys())
        if "bear_researcher" in nodes:
            print("  ✅ bear_researcher node found in graph")
            return True
        else:
            print(f"  ❌ bear_researcher node not found. Available nodes: {nodes}")
            return False
    except Exception as e:
        print(f"  ❌ bear_researcher integration test failed: {e}")
        return False

async def test_log_data_fetch():
    """Test that log_data_fetch calls work correctly"""
    print("📝 Testing log_data_fetch functionality...")
    try:
        from src.agent.utils.debug_logging import log_data_fetch
        import logging
        
        # Set up logger
        logger = logging.getLogger("test")
        
        # Test the function with correct parameters
        log_data_fetch("test_source", ["item1", "item2"], logger)
        print("  ✅ log_data_fetch call successful")
        return True
    except Exception as e:
        print(f"  ❌ log_data_fetch test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 Starting comprehensive validation tests...")
    print("=" * 60)
    
    tests = [
        test_bear_researcher_import,
        test_serper_utils_import, 
        test_graph_import,
        test_graph_creation,
        test_bear_researcher_in_graph,
    ]
    
    # Add async test
    async_tests = [
        test_log_data_fetch,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run sync tests
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
    
    # Run async tests
    for async_test in async_tests:
        try:
            if asyncio.run(async_test()):
                passed += 1
        except Exception as e:
            print(f"  ❌ Async test {async_test.__name__} crashed: {e}")
    
    print("=" * 60)
    print(f"🏁 Validation Complete: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 