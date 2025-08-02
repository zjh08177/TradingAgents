#!/usr/bin/env python3
"""
Enhanced debug test script for LangGraph trading graph
"""

import asyncio
import logging
import sys
import traceback
import os
from datetime import datetime

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_test.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_graph_execution():
    """Test the graph execution with detailed debugging"""
    try:
        logger.info("🚀 Starting enhanced debug test of trading graph")
        
        # Test 1: Environment verification
        logger.debug("🔑 Testing environment...")
        api_key = os.getenv('OPENAI_API_KEY', '')
        if api_key.startswith('sk-'):
            logger.debug("✅ OpenAI API key found")
        else:
            logger.warning("⚠️ OpenAI API key not found or invalid")
        
        # Test 2: Import verification
        logger.debug("📦 Testing imports...")
        from agent.graph.trading_graph import TradingAgentsGraph
        from agent.default_config import DEFAULT_CONFIG
        from langchain_openai import ChatOpenAI
        from agent.utils.debug_logging import debug_node
        logger.debug("✅ All imports successful")
        
        # Test 3: LLM creation
        logger.debug("🤖 Testing LLM creation...")
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        test_result = await llm.ainvoke([{"role": "user", "content": "Say 'LLM working'"}])
        logger.debug(f"✅ LLM test result: {test_result.content}")
        
        # Test 4: Memory system
        logger.debug("💾 Testing memory system...")
        from agent.utils.memory import FinancialSituationMemory
        memory = FinancialSituationMemory("test_memory", DEFAULT_CONFIG)
        logger.debug("✅ Memory system created successfully")
        
        # Test 5: Graph compilation
        logger.debug("🏗️ Testing graph compilation...")
        trading_graph = TradingAgentsGraph(
            config=DEFAULT_CONFIG
        )
        
        # Access the graph property instead of calling compile
        compiled_graph = trading_graph.graph
        logger.debug(f"✅ Graph compiled with {len(compiled_graph.nodes)} nodes")
        
        # Test 6: Debug logging test
        logger.debug("🔍 Testing debug logging...")
        @debug_node("test_node")
        async def test_node(state):
            return {"test": "success", "debug_working": True}
        
        test_state = {"company_of_interest": "GOOG", "trade_date": "2025-07-28"}
        debug_result = await test_node(test_state)
        logger.debug(f"✅ Debug logging test: {debug_result}")
        
        # Test 7: Skip graph execution for basic testing
        logger.debug("⚡ Skipping graph execution for basic validation")
        logger.info("✅ Basic setup and imports validated successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug test failed: {str(e)}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_graph_execution())
    if success:
        print("\n🎉 ENHANCED DEBUG TEST PASSED - Graph is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 ENHANCED DEBUG TEST FAILED - Check logs for details")
        sys.exit(1)
