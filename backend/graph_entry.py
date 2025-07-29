"""
LangGraph Cloud Entry Point for Trading Agents

This module provides the compiled graph for deployment to LangGraph Cloud.
It creates and exports a properly configured TradingAgentsGraph instance.
"""

import os
from typing import Dict, Any
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.agent_states import AgentState


def create_cloud_config() -> Dict[str, Any]:
    """Create configuration optimized for LangGraph Cloud deployment."""
    config = DEFAULT_CONFIG.copy()
    
    # Cloud-optimized settings
    config.update({
        # Use environment variables for cloud deployment
        "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "/Users/bytedance/Documents/TradingAgents/results"),
        "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", "/tmp/data"),
        "data_cache_dir": "/tmp/cache",
        
        # Optimize for cloud performance
        "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "1")),
        "max_risk_discuss_rounds": int(os.getenv("MAX_RISK_DISCUSS_ROUNDS", "1")),
        "max_recur_limit": int(os.getenv("MAX_RECUR_LIMIT", "50")),
        
        # Ensure online tools are enabled
        "online_tools": True,
        
        # API keys from environment
        "serper_key": os.getenv("SERPER_API_KEY", ""),
    })
    
    return config


def create_compiled_graph():
    """Create and compile the trading graph for LangGraph Cloud."""
    
    # Create cloud-optimized config
    config = create_cloud_config()
    
    # Initialize the trading graph with cloud config
    # The graph is automatically compiled during initialization
    trading_graph = TradingAgentsGraph(debug=False, config=config)
    
    # Return the compiled graph that was created during initialization
    return trading_graph.graph


# Export the compiled graph for LangGraph Cloud
compiled_graph = create_compiled_graph()

# For debugging/testing locally
if __name__ == "__main__":
    print("🚀 Trading Agents Graph compiled successfully for LangGraph Cloud!")
    print(f"📊 Graph nodes: {list(compiled_graph.get_graph().nodes.keys())}")
    print(f"🔗 Graph edges: {len(compiled_graph.get_graph().edges)}") 