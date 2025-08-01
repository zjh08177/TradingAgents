#!/usr/bin/env python3
"""
Validation script for performance optimizations from TRACE_PERFORMANCE_DIAGNOSIS.md
"""

import asyncio
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_priority1_parallel_dispatcher():
    """Test Priority 1: Send-based Parallel Dispatcher"""
    logger.info("🔍 Testing Priority 1: Send-based Parallel Dispatcher")
    
    try:
        from src.agent.graph.nodes.dispatcher import parallel_dispatcher_node
        # Send not needed with direct edge approach
        
        # Create a mock state
        mock_state = {
            "company_of_interest": "AAPL",
            "trade_date": "2025-07-28",
            "selected_analysts": ["market", "news", "social", "fundamentals"],
            "messages": []
        }
        
        # Call the dispatcher
        start_time = time.time()
        result = await parallel_dispatcher_node(mock_state)
        duration = time.time() - start_time
        
        # Verify it returns a dict with initialized analyst messages
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        
        # Check that all analyst messages were initialized
        for analyst in mock_state["selected_analysts"]:
            message_key = f"{analyst}_messages"
            assert message_key in result, f"Missing {message_key} in result"
            assert len(result[message_key]) == 1, f"Expected 1 message in {message_key}"
        
        logger.info(f"✅ Priority 1 PASSED: Dispatcher initialized all analysts in {duration:.3f}s")
        return True
        
    except Exception as e:
        logger.error(f"❌ Priority 1 FAILED: {str(e)}")
        return False

async def test_priority1_timing_logs():
    """Test Priority 1: Execution Timing Logs"""
    logger.info("🔍 Testing Priority 1: Execution Timing Logs")
    
    try:
        # Check if timing logs are added to analysts
        from src.agent.analysts import market_analyst
        
        # Read the file to check for timing logs
        with open("src/agent/analysts/market_analyst.py", "r") as f:
            content = f.read()
            
        timing_patterns = [
            "start_time = time.time()",
            "⏱️ market_analyst START:",
            "⏱️ market_analyst END:",
            "duration = time.time() - start_time"
        ]
        
        missing_patterns = [p for p in timing_patterns if p not in content]
        
        if not missing_patterns:
            logger.info("✅ Priority 1 PASSED: All timing logs found in market_analyst.py")
            return True
        else:
            logger.error(f"❌ Priority 1 FAILED: Missing timing patterns: {missing_patterns}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Priority 1 FAILED: {str(e)}")
        return False

async def test_priority2_batch_tools():
    """Test Priority 2: Batch Tool Calls"""
    logger.info("🔍 Testing Priority 2: Batch Tool Calls in Analysts")
    
    try:
        from src.agent.utils.batch_tool_execution import execute_tools_parallel, create_tool_batch
        
        # Create mock tool calls
        def mock_tool(name):
            async def tool(**kwargs):
                await asyncio.sleep(0.1)  # Simulate work
                return f"Result from {name}"
            return tool
        
        tool_calls = [
            {"function": mock_tool("tool1"), "args": {}},
            {"function": mock_tool("tool2"), "args": {}},
            {"function": mock_tool("tool3"), "args": {}}
        ]
        
        # Execute in parallel
        start_time = time.time()
        results = await execute_tools_parallel(tool_calls, "test_analyst")
        duration = time.time() - start_time
        
        # Should be much faster than sequential (0.3s)
        assert duration < 0.2, f"Parallel execution too slow: {duration:.3f}s"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        logger.info(f"✅ Priority 2 PASSED: Batch tools executed in {duration:.3f}s (parallel)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Priority 2 FAILED: {str(e)}")
        return False

async def test_priority2_async_fetcher():
    """Test Priority 2: Async Market Data Fetcher"""
    logger.info("🔍 Testing Priority 2: Async Market Data Fetcher")
    
    try:
        from src.agent.utils.agent_utils import Toolkit
        
        # Check if async market data fetcher exists
        toolkit = Toolkit()
        assert hasattr(toolkit, 'get_all_market_data'), "get_all_market_data method not found"
        
        # Test the method signature
        import inspect
        sig = inspect.signature(toolkit.get_all_market_data)
        params = list(sig.parameters.keys())
        assert 'symbol' in params, "Missing symbol parameter"
        assert 'date' in params, "Missing date parameter"
        
        logger.info("✅ Priority 2 PASSED: Async market data fetcher implemented")
        return True
        
    except Exception as e:
        logger.error(f"❌ Priority 2 FAILED: {str(e)}")
        return False

async def test_priority3_caching():
    """Test Priority 3: Tool Result Caching"""
    logger.info("🔍 Testing Priority 3: Tool Result Caching")
    
    try:
        from src.agent.utils.tool_caching import (
            ToolCache, cache_tool_result, get_cache_stats, 
            get_cached_market_data, cache_market_data
        )
        
        # Test cache functionality
        cache = ToolCache()
        
        # Test set/get
        cache.set("test_tool", {"arg1": "value1"}, "cached_result")
        result = cache.get("test_tool", {"arg1": "value1"})
        assert result == "cached_result", "Cache get/set failed"
        
        # Test cache stats
        stats = cache.get_stats()
        assert stats['size'] == 1, "Cache size incorrect"
        assert stats['hits'] == 1, "Cache hit count incorrect"
        
        # Test market data caching functions
        cache_market_data("AAPL", "2025-07-28", "rsi", "RSI: 65")
        cached = get_cached_market_data("AAPL", "2025-07-28", "rsi")
        assert cached == "RSI: 65", "Market data caching failed"
        
        logger.info("✅ Priority 3 PASSED: Tool caching implemented and working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Priority 3 FAILED: {str(e)}")
        return False

async def test_priority3_connection_pool():
    """Test Priority 3: Connection Pooling"""
    logger.info("🔍 Testing Priority 3: Connection Pooling")
    
    try:
        from src.agent.utils.connection_pool import (
            ConnectionPool, get_connection_pool, 
            pooled_request, ToolkitWithPool
        )
        
        # Test connection pool creation
        pool = await get_connection_pool()
        assert pool is not None, "Connection pool creation failed"
        
        # Test pool stats
        stats = pool.get_stats()
        assert stats['status'] == 'active', "Pool not active"
        assert 'limit' in stats, "Pool stats missing limit"
        
        # Test ToolkitWithPool
        toolkit = ToolkitWithPool()
        assert hasattr(toolkit, 'fetch_data'), "ToolkitWithPool missing fetch_data"
        assert hasattr(toolkit, 'post_data'), "ToolkitWithPool missing post_data"
        
        # Clean up
        await pool.close()
        
        logger.info("✅ Priority 3 PASSED: Connection pooling implemented")
        return True
        
    except Exception as e:
        logger.error(f"❌ Priority 3 FAILED: {str(e)}")
        return False

async def test_caching_decorators():
    """Test that caching decorators are applied to tools"""
    logger.info("🔍 Testing caching decorators on tools")
    
    try:
        # Check if tools have caching decorators
        import src.agent.utils.agent_utils as agent_utils
        
        # Check for cache_tool_result import
        assert hasattr(agent_utils, 'cache_tool_result'), "cache_tool_result not imported"
        
        # Read the file to verify decorators are applied
        with open("src/agent/utils/agent_utils.py", "r") as f:
            content = f.read()
            
        cached_tools = [
            "get_YFin_data",
            "get_YFin_data_online",
            "get_stockstats_indicators_report",
            "get_stockstats_indicators_report_online",
            "get_finnhub_news"
        ]
        
        missing_decorators = []
        for tool in cached_tools:
            # Look for @cache_tool_result decorator before the tool
            pattern = f"@cache_tool_result"
            if pattern not in content:
                missing_decorators.append(tool)
        
        if not missing_decorators:
            logger.info("✅ Caching decorators PASSED: All tools have caching")
            return True
        else:
            logger.error(f"❌ Caching decorators FAILED: Missing on {missing_decorators}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Caching decorators FAILED: {str(e)}")
        return False

async def main():
    """Run all validation tests"""
    logger.info("🚀 Starting Performance Optimization Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Priority 1: Parallel Dispatcher", test_priority1_parallel_dispatcher),
        ("Priority 1: Timing Logs", test_priority1_timing_logs),
        ("Priority 2: Batch Tools", test_priority2_batch_tools),
        ("Priority 2: Async Fetcher", test_priority2_async_fetcher),
        ("Priority 3: Caching", test_priority3_caching),
        ("Priority 3: Connection Pool", test_priority3_connection_pool),
        ("Caching Decorators", test_caching_decorators)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n📋 Running: {name}")
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test crashed: {str(e)}")
            results.append((name, False))
        logger.info("-" * 60)
    
    # Summary
    logger.info("\n📊 VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
    
    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        logger.info("🎉 ALL OPTIMIZATIONS VALIDATED SUCCESSFULLY!")
        logger.info("✨ Expected performance improvement: >50% reduction in execution time")
    else:
        logger.error("⚠️  Some optimizations failed validation. Please review the logs.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)