#!/usr/bin/env python3
"""
Full graph execution script for trading agents
"""

import asyncio
import logging
import sys
import json
import traceback
import os
from datetime import datetime, date

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250807_145911.log')
    ]
)

# Reduce noise from some loggers
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def execute_full_graph(ticker="UNH", trade_date=None):
    """Execute the full trading graph with all nodes"""
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 Starting full graph execution for {ticker}")
        logger.info(f"📅 Trade Date: {trade_date or 'Today'}")
        
        # Import required modules
        from src.agent.graph.trading_graph import TradingAgentsGraph
        from src.agent.default_config import DEFAULT_CONFIG
        from src.agent.utils.debug_logging import debug_node
        
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
        
        with open('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250807_145911.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"💾 Detailed results saved to: /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250807_145911.json")
        
        # Display key insights
        logger.info("🔍 === KEY INSIGHTS ===")
        
        # Market analysis
        if 'market_report' in result:
            logger.info("📈 Market Analysis: Available")
        
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
        
        with open('/Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250807_145911.json', 'w') as f:
            json.dump(error_info, f, indent=2)
        
        return False

if __name__ == "__main__":
    # Get ticker from command line or use default
    ticker = sys.argv[1] if len(sys.argv) > 1 else "UNH"
    trade_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = asyncio.run(execute_full_graph(ticker, trade_date))
    
    if success:
        print(f"\n🎉 FULL GRAPH EXECUTION SUCCESSFUL for {ticker}!")
        sys.exit(0)
    else:
        print(f"\n💥 GRAPH EXECUTION FAILED for {ticker} - Check logs for details")
        sys.exit(1)
