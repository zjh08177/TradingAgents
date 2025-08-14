"""Unified Agent module for LangGraph server integration."""

import asyncio
import logging
from datetime import date
from typing import Dict, Any

from langchain_core.runnables import RunnableConfig
from .default_config import DEFAULT_CONFIG

# Set up logging - use NullHandler to avoid blocking I/O in async context
# The actual logging configuration should be done by the application, not the library
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Only add NullHandler if no handlers are configured
    # This prevents blocking I/O while still allowing the app to configure logging
    logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)

async def run_trading_analysis(company_name: str, analysis_date: str = None) -> dict:
    """Main entry point for running trading analysis"""
    if analysis_date is None:
        analysis_date = str(date.today())
    
    try:
        from .graph.trading_graph import TradingAgentsGraph
        
        # Create and run the trading graph
        trading_graph = TradingAgentsGraph(
            config=DEFAULT_CONFIG,
            selected_analysts=["market", "social", "news", "fundamentals"]
        )
        
        # Run the analysis
        final_state, processed_signal = await trading_graph.propagate(company_name, analysis_date)
        
        return {
            "company": company_name,
            "date": analysis_date,
            "final_state": final_state,
            "signal": processed_signal
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def create_studio_compatible_graph():
    """Create a LangGraph Studio compatible graph"""
    import importlib
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Dynamic import to avoid circular dependencies
        # Import using absolute path from src
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from agent.graph.trading_graph import TradingAgentsGraph
        
        # Create graph instance with simplified signature
        trading_graph_instance = TradingAgentsGraph(
            config=DEFAULT_CONFIG,
            selected_analysts=["market", "social", "news", "fundamentals"]
        )
        
        return trading_graph_instance.graph
        
    except Exception as e:
        logger.error(f"Failed to create graph: {e}")
        raise

def graph(config: RunnableConfig):
    """
    LangGraph Studio compatible graph factory function.
    
    Args:
        config: RunnableConfig instance (required by LangGraph API)
        
    Returns:
        The configured trading graph instance
    """
    logger.info(f"Creating graph with config: {config}")
    return create_studio_compatible_graph()

def get_graph():
    """Get a graph instance for direct use."""
    return create_studio_compatible_graph()

__all__ = [
    "run_trading_analysis",
    "create_studio_compatible_graph",
    "graph",
    "get_graph"
]
