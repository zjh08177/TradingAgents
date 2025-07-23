#!/usr/bin/env python3
"""
Debug test script to identify and fix async issues in the trading graph
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_graph_execution():
    """Test the graph execution with detailed debugging"""
    try:
        logger.info("🚀 Starting debug test of trading graph")
        
        # Import the graph components
        logger.debug("📦 Importing trading graph components...")
        from agent.graph.trading_graph import TradingAgentsGraph
        from agent.default_config import DEFAULT_CONFIG
        
        logger.debug("✅ Successfully imported graph components")
        
        # Create trading graph instance
        trading_graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            config=DEFAULT_CONFIG
        )
        logger.debug("✅ Trading graph instance created")
        
        # Test data
        test_input = {
            "ticker": "AAPL",
            "analysis_date": "2025-07-22",
            "company_of_interest": "Apple Inc.",
            "trade_date": "2025-07-22"
        }
        
        logger.info(f"🎯 Testing with input: {test_input}")
        
        # Try to run the graph
        logger.info("🏃 Starting graph execution...")
        try:
            final_state, processed_signal = await trading_graph.propagate(
                test_input["company_of_interest"], 
                test_input["trade_date"]
            )
            
            logger.info("✅ Graph execution completed successfully!")
            logger.info(f"📊 Final state keys: {list(final_state.keys()) if final_state else 'None'}")
            logger.info(f"🎯 Processed signal: {processed_signal}")
            
            return True
            
        except Exception as graph_error:
            logger.error(f"❌ Graph execution failed: {graph_error}")
            logger.error(f"❌ Error type: {type(graph_error).__name__}")
            logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
            return False
            
    except ImportError as import_error:
        logger.error(f"❌ Import error: {import_error}")
        logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
        return False

async def test_individual_components():
    """Test individual components to isolate issues"""
    logger.info("🔍 Testing individual components...")
    
    try:
        # Test LLM creation
        logger.debug("🧠 Testing LLM creation...")
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        logger.debug("✅ LLM created successfully")
        
        # Test simple LLM call
        logger.debug("💬 Testing simple LLM call...")
        messages = [{"role": "user", "content": "Say 'Hello, World!'"}]
        response = await llm.ainvoke(messages)
        logger.debug(f"✅ LLM response: {response.content}")
        
        # Test analyst creation
        logger.debug("🔬 Testing analyst creation...")
        from agent.analysts.market_analyst import create_market_analyst
        
        market_analyst = create_market_analyst(llm, [])
        logger.debug("✅ Market analyst created successfully")
        
        # Test memory system
        logger.debug("💾 Testing memory system...")
        from agent.utils.memory import FinancialSituationMemory
        from agent.default_config import DEFAULT_CONFIG
        
        memory = FinancialSituationMemory("test_memory", DEFAULT_CONFIG)
        logger.debug("✅ Memory system created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Component test failed: {e}")
        logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
        return False

async def main():
    """Main debug function"""
    logger.info("=" * 80)
    logger.info("🐛 COMPREHENSIVE DEBUG TEST STARTED")
    logger.info("=" * 80)
    
    # Test individual components first
    logger.info("Phase 1: Testing individual components...")
    component_success = await test_individual_components()
    
    if not component_success:
        logger.error("❌ Component tests failed, skipping graph test")
        return False
    
    logger.info("✅ All components tested successfully")
    
    # Test full graph execution
    logger.info("Phase 2: Testing full graph execution...")
    graph_success = await test_graph_execution()
    
    logger.info("=" * 80)
    if graph_success:
        logger.info("🎉 ALL DEBUG TESTS PASSED!")
        logger.info("✅ Graph is working correctly")
    else:
        logger.error("❌ DEBUG TESTS FAILED!")
        logger.error("   Check debug.log for detailed error information")
    
    logger.info("=" * 80)
    return graph_success

if __name__ == "__main__":
    asyncio.run(main()) 