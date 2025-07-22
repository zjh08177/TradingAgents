"""
Trading Agents - Multi-Agent Trading Analysis Framework

A sophisticated trading analysis system using LangGraph to orchestrate
multiple AI agents for comprehensive market analysis and decision making.
"""

__version__ = "1.0.0"
__author__ = "Trading Agents Team"

from .graph.trading_graph import TradingAgentsGraph
from .default_config import DEFAULT_CONFIG

__all__ = [
    "TradingAgentsGraph",
    "DEFAULT_CONFIG"
] 