"""Unified Agent module for LangGraph server integration."""

import asyncio
import logging
from datetime import date
from typing import Dict, Any

from .default_config import DEFAULT_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
        TradingAgentsGraph = trading_graph_module.TradingAgentsGraph
        
        # Create graph instance with simplified signature
        trading_graph_instance = TradingAgentsGraph(
            config=DEFAULT_CONFIG,
            selected_analysts=["market", "social", "news", "fundamentals"]
        )
        
        return trading_graph_instance.graph
        
    except Exception as e:
        logger.error(f"Failed to create graph: {e}")
        raise

# For LangGraph Studio compatibility
# Create a lazy graph wrapper to defer creation until needed
class LazyGraph:
    """Lazy-loading graph wrapper to avoid import-time errors."""
    def __init__(self):
        self._graph = None
    
    def __getattr__(self, name):
        if self._graph is None:
            self._graph = create_studio_compatible_graph()
        return getattr(self._graph, name)
    
    def __call__(self, *args, **kwargs):
        if self._graph is None:
            self._graph = create_studio_compatible_graph()
        return self._graph(*args, **kwargs)

# Create the lazy graph instance
graph = LazyGraph()

def get_graph():
    """Get the actual graph instance (forces creation if needed)."""
    if isinstance(graph, LazyGraph) and graph._graph is None:
        graph._graph = create_studio_compatible_graph()
    return graph._graph if isinstance(graph, LazyGraph) else graph

__all__ = [
    "run_trading_analysis",
    "create_studio_compatible_graph",
    "graph",
    "get_graph"
]
