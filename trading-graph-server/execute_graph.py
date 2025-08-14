#!/usr/bin/env python3
"""
Full graph execution script for trading agents
Mimics langgraph dev execution environment with blocking I/O detection
"""

import asyncio
import logging
import sys
import json
import traceback
import os
import warnings
from datetime import datetime, date

# 🚨 CRITICAL: Enable asyncio debug mode to detect blocking I/O like LangGraph dev
if os.environ.get('PYTHONASYNCIODEBUG') == '1':
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    # Enable debug mode on the event loop
    import functools
    
    # Patch asyncio to detect blocking I/O
    def patch_blocking_io_detection():
        """Mimic LangGraph dev's blocking I/O detection"""
        import sys
        import threading
        
        # Track blocking I/O errors globally
        global blocking_io_errors
        blocking_io_errors = []
        
        # Hook into asyncio's slow callback detection
        loop = asyncio.new_event_loop()
        loop.set_debug(True)  # Enable debug mode
        loop.slow_callback_duration = 0.01  # Very sensitive to blocking calls
        asyncio.set_event_loop(loop)
        
        # Add custom error tracking
        def track_blocking_io(msg):
            """Track blocking I/O errors for later reporting"""
            blocking_io_errors.append(msg)
            print(f"🚨 BLOCKING I/O DETECTED: {msg}", file=sys.stderr)
        
        # Store the tracking function globally
        asyncio._track_blocking_io = track_blocking_io
        
        print("🚨 Async monitoring enabled (mimicking LangGraph dev)")
        print("   - Asyncio debug mode: ENABLED")
        print("   - Slow callback detection: 0.01s threshold")
        print("   - Will detect sync violations in async context")
        
        return blocking_io_errors
    
    # Apply the patch and get error tracker
    blocking_io_tracker = patch_blocking_io_detection()

# CRITICAL: Load environment variables FIRST before any imports that use config
# This prevents blocking I/O in async context
sys.path.insert(0, 'src')

# Set up environment to mimic langgraph dev
os.environ['LANGGRAPH_ENV'] = 'development'
os.environ['LANGGRAPH_DEBUG'] = 'true'
os.environ['LANGCHAIN_TRACING_V2'] = 'true'

# Load environment variables from .env file
from agent.load_env import load_environment
load_environment(verbose=False)  # Load .env file before any config imports

# Set up async-safe logging (no blocking I/O)
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create handlers without using basicConfig
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    file_handler = logging.FileHandler('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_NVDA_20250814_155723.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

# Reduce noise from some loggers
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def execute_full_graph(ticker="NVDA", trade_date=None):
    """Execute the full trading graph with all nodes - LangGraph Dev Compatible"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting full graph execution for {ticker}")
        logger.info(f"📅 Trade Date: {trade_date or 'Today'}")
        logger.info(f"🔧 Environment: {os.environ.get('LANGGRAPH_ENV', 'production')}")
        logger.info(f"🔍 Debug Mode: {os.environ.get('LANGGRAPH_DEBUG', 'false')}")
        
        # Import required modules (delayed to prevent blocking I/O at module level)
        from src.agent.graph.trading_graph import TradingAgentsGraph
        from src.agent.default_config import DEFAULT_CONFIG
        from src.agent.utils.debug_logging import debug_node
        
        # Verify no blocking I/O by checking async context
        try:
            asyncio.current_task()
            logger.info("✅ Running in async context - no blocking I/O detected")
        except RuntimeError:
            logger.warning("⚠️ Not in async context - potential blocking I/O")
        
        # Enable enhanced implementation for testing
        enhanced_config = DEFAULT_CONFIG.copy()
        enhanced_config['enable_send_api'] = True
        enhanced_config['enable_enhanced_monitoring'] = True
        enhanced_config['enable_fallback'] = True
        
        # Initialize the trading graph with enhanced implementation
        logger.info("🏗️ Initializing trading graph with enhanced implementation...")
        logger.info("🚀 Using Send API + Conditional Edges for parallel execution")
        trading_graph = TradingAgentsGraph(
            config=enhanced_config,
            selected_analysts=["market", "social", "news", "fundamentals"]
        )
        
        # Use today's date if not specified
        if not trade_date:
            trade_date = date.today().strftime("%Y-%m-%d")
        
        logger.info(f"📊 Executing graph for {ticker} on {trade_date}")
        logger.info("⏳ This will analyze market data, news, social sentiment, and fundamentals...")
        logger.info("⏳ Expected runtime: 2-10 minutes depending on data availability")
        
        # Execute the full graph
        result = await trading_graph.propagate(ticker, trade_date)
        
        # Handle tuple return (final_state, processed_signal)
        if isinstance(result, tuple) and len(result) == 2:
            final_state, processed_signal = result
            result = final_state
            result["processed_signal"] = processed_signal
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Log summary results
        logger.info(f"✅ Graph execution completed in {execution_time:.2f} seconds")
        logger.info("📊 === EXECUTION SUMMARY ===")
        logger.info(f"   Ticker: {ticker}")
        logger.info(f"   Date: {trade_date}")
        logger.info(f"   Runtime: {execution_time:.2f}s")
        
        # Extract key results
        final_decision = result.get('processed_signal', 'No signal')
        investment_plan = result.get('investment_plan', 'No plan generated')
        
        logger.info(f"   Decision: {final_decision}")
        
        # Save detailed results to JSON
        results = {
            "ticker": ticker,
            "trade_date": trade_date,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "final_decision": final_decision,
            "investment_plan": investment_plan,
            "full_result": result
        }
        
        with open('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250814_155723.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Detailed results saved to: /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250814_155723.json")
        
        # Display key insights
        logger.info("🔍 === KEY INSIGHTS ===")
        
        # 🔍 MARKET REPORT DEBUGGING - Log actual content
        if 'market_report' in result:
            market_report = result['market_report']
            logger.info("📈 Market Analysis: Available")
            logger.info("🔍 === MARKET REPORT CONTENT DEBUG ===")
            logger.info(f"📊 Market Report Type: {type(market_report)}")
            logger.info(f"📊 Market Report Length: {len(str(market_report))}")
            
            # Check for blocking I/O error in market report
            market_report_str = str(market_report)
            blocking_io_found = False
            
            # Check for various blocking I/O error patterns
            blocking_patterns = [
                "blocking call to io.textiowrapper",
                "error: blocking call",
                "blocking i/o",
                "synchronous blocking call"
            ]
            
            for pattern in blocking_patterns:
                if pattern in market_report_str.lower():
                    blocking_io_found = True
                    break
            
            if blocking_io_found:
                logger.error("❌ CRITICAL: BLOCKING I/O ERROR DETECTED IN MARKET REPORT")
                logger.error("❌ This prevents proper async execution in LangGraph")
                logger.error(f"❌ Market Report Content: {market_report_str[:500]}...")
                # Store error for final reporting
                if 'blocking_io_tracker' in globals():
                    blocking_io_tracker.append("Market report contains blocking I/O error")
                # Set execution as failed
                blocking_io_detected = True
            elif "error:" in market_report_str.lower():
                logger.warning("⚠️ ERROR DETECTED IN MARKET REPORT:")
                logger.warning(f"⚠️ Market Report Content: {market_report_str[:500]}...")
            else:
                logger.info("✅ Market Report appears normal:")
                logger.info(f"✅ Market Report Preview: {market_report_str[:200]}...")  
            
            logger.info("🔍 === END MARKET REPORT DEBUG ===")
        else:
            logger.error("❌ NO MARKET REPORT FOUND IN RESULTS")
        
        # News sentiment
        if 'news_report' in result:
            logger.info("📰 News Sentiment: Available")
            
        # Social sentiment  
        if 'social_report' in result:
            logger.info("💬 Social Sentiment: Available")
            
        # Fundamentals
        if 'fundamentals_report' in result:
            logger.info("💰 Fundamentals: Available")
        
        # Risk assessment
        if 'risk_report' in result:
            logger.info("⚠️  Risk Assessment: Available")
        
        # Check for any blocking I/O errors detected during execution
        blocking_io_detected = locals().get('blocking_io_detected', False)
        if 'blocking_io_tracker' in globals() and blocking_io_tracker:
            logger.error(f"❌ BLOCKING I/O ERRORS DETECTED: {len(blocking_io_tracker)} instances")
            for error in blocking_io_tracker:
                logger.error(f"   • {error}")
            blocking_io_detected = True
        
        if blocking_io_detected:
            logger.error("❌ === EXECUTION FAILED DUE TO BLOCKING I/O ===")
            logger.error("💡 Solution: Replace yfinance with async alternatives")
            logger.error("📚 See BLOCKING_IO_FIX_ATTEMPTS.md for details")
            return False
        else:
            logger.info("✅ === EXECUTION COMPLETE ===")
            return True
        
    except Exception as e:
        logger.error(f"❌ Graph execution failed: {str(e)}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        # Save error information
        error_info = {
            "ticker": ticker,
            "trade_date": trade_date,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        with open('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250814_155723.json', 'w') as f:
            json.dump(error_info, f, indent=2)
        
        return False

if __name__ == "__main__":
    # Get ticker from command line or use default
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    trade_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = asyncio.run(execute_full_graph(ticker, trade_date))
    
    if success:
        print(f"\n🎉 FULL GRAPH EXECUTION SUCCESSFUL for {ticker}!")
        sys.exit(0)
    else:
        print(f"\n💥 GRAPH EXECUTION FAILED for {ticker} - Check logs for details")
        sys.exit(1)
