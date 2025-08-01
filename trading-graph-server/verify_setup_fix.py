#!/usr/bin/env python3
"""
Verify the exact fix in setup.py works correctly
This simulates the exact scenario from setup.py line 138
"""
import asyncio
import sys
import os
import logging

# Add src to path to import our actual code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the actual fixed code
from agent.graph.setup import GraphBuilder

class MockLLM:
    """Mock LLM for testing"""
    pass

def test_setup_graph_in_async_context():
    """Test that setup_graph works in async context (LangGraph dev)"""
    logger.info("🔍 Testing setup_graph in async context (simulating LangGraph dev)")
    
    # Create mock GraphBuilder
    config = {"enable_batch_prompt_processing": True}
    builder = GraphBuilder(MockLLM(), MockLLM(), config)
    
    # Mock the prompt processor to avoid import issues
    class MockPromptProcessor:
        async def process_analyst_prompts_batch(self, configs):
            logger.info("Mock batch processing")
            return type('obj', (object,), {
                'prompts': {},
                'processing_time': 0.1,
                'speedup': 4.0,
                'token_savings': 1000
            })
    
    builder.prompt_processor = MockPromptProcessor()
    
    # This is the critical test - calling _preprocess_prompts_sync in async context
    try:
        builder._preprocess_prompts_sync(["market", "news", "social", "fundamentals"])
        logger.info("✅ SUCCESS: _preprocess_prompts_sync worked in async context!")
        return True
    except RuntimeError as e:
        logger.error(f"❌ FAILED: {e}")
        return False

async def main():
    """Run test in async context"""
    logger.info("=" * 60)
    logger.info("🚀 Verifying setup.py fix for LangGraph dev")
    logger.info("=" * 60)
    
    # Test 1: In sync context
    logger.info("\n📌 Test 1: Sync context")
    try:
        config = {"enable_batch_prompt_processing": True}
        builder = GraphBuilder(MockLLM(), MockLLM(), config)
        builder.prompt_processor = type('obj', (object,), {
            'process_analyst_prompts_batch': lambda self, x: asyncio.run(asyncio.sleep(0.01))
        })()
        
        # This should work
        builder._preprocess_prompts_sync(["market", "news"])
        logger.info("✅ Sync context test PASSED")
    except Exception as e:
        logger.error(f"❌ Sync context test FAILED: {e}")
    
    # Test 2: In async context (the critical one)
    logger.info("\n📌 Test 2: Async context (LangGraph dev scenario)")
    success = test_setup_graph_in_async_context()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("🎉 VERIFICATION COMPLETE!")
        logger.info("The fix in setup.py correctly handles the async context issue.")
        logger.info("LangGraph dev should now work without RuntimeError!")
        logger.info("=" * 60)
    else:
        logger.error("\n❌ Fix verification failed")
        sys.exit(1)

if __name__ == "__main__":
    # Run in async context to simulate LangGraph dev
    asyncio.run(main())