"""Unified Agent module for LangGraph server integration."""

import os
import sys
from typing import TypedDict, Dict, Any
from datetime import datetime
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

# Add the src directory to the Python path so we can import tradingagents
src_dir = os.path.dirname(os.path.abspath(__file__))
src_parent = os.path.dirname(src_dir)
if src_parent not in sys.path:
    sys.path.insert(0, src_parent)

# Import from local agent modules
from .utils.agent_utils import Toolkit, create_msg_delete
from .utils.agent_states import AgentState, InvestDebateState, RiskDebateState
from .utils.memory import FinancialSituationMemory

from .analysts.fundamentals_analyst import create_fundamentals_analyst
from .analysts.market_analyst import create_market_analyst
from .analysts.news_analyst import create_news_analyst
from .analysts.social_media_analyst import create_social_media_analyst

from .researchers.bear_researcher import create_bear_researcher
from .researchers.bull_researcher import create_bull_researcher

from .risk_mgmt.aggresive_debator import create_risky_debator
from .risk_mgmt.conservative_debator import create_safe_debator
from .risk_mgmt.neutral_debator import create_neutral_debator

from .managers.research_manager import create_research_manager
from .managers.risk_manager import create_risk_manager

from .trader.trader import create_trader

# Import remaining dependencies from local modules
from .default_config import DEFAULT_CONFIG


class LangGraphServerState(TypedDict):
    """State compatible with LangGraph server API."""
    # Input fields
    ticker: str
    analysis_date: str
    company_of_interest: str
    trade_date: str
    
    # Output fields
    fundamentals_report: str
    market_analysis_report: str
    news_sentiment_report: str
    social_media_report: str
    research_report: str
    risk_assessment: str
    trading_recommendation: str
    confidence_score: float


def convert_to_agent_state(server_state: LangGraphServerState) -> Dict[str, Any]:
    """Convert LangGraph server state to internal AgentState format."""
    company = server_state.get("company_of_interest", "") or server_state.get("ticker", "")
    trade_date = server_state.get("trade_date", "") or server_state.get("analysis_date", "")
    
    if not trade_date:
        trade_date = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "company_of_interest": company,
        "trade_date": trade_date,
        # Initialize empty message channels
        "market_messages": [],
        "social_messages": [],
        "news_messages": [],
        "fundamentals_messages": [],
        # Initialize empty reports
        "market_report": "",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        # Initialize debate states
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0
        },
        "risk_debate_state": {
            "risky_history": "",
            "safe_history": "",
            "neutral_history": "",
            "history": "",
            "latest_speaker": "",
            "current_risky_response": "",
            "current_safe_response": "",
            "current_neutral_response": "",
            "judge_decision": "",
            "count": 0
        },
        # Initialize other fields
        "investment_plan": "",
        "trader_investment_plan": "",
        "final_trade_decision": ""
    }


def convert_from_agent_state(agent_state: Dict[str, Any], original_state: LangGraphServerState) -> LangGraphServerState:
    """Convert internal AgentState back to LangGraph server state format."""
    result = original_state.copy()
    result.update({
        "fundamentals_report": agent_state.get("fundamentals_report", ""),
        "market_analysis_report": agent_state.get("market_report", ""),
        "news_sentiment_report": agent_state.get("news_report", ""),
        "social_media_report": agent_state.get("sentiment_report", ""),
        "research_report": agent_state.get("investment_plan", ""),
        "risk_assessment": agent_state.get("risk_debate_state", {}).get("judge_decision", ""),
        "trading_recommendation": agent_state.get("final_trade_decision", ""),
        "confidence_score": 7.5  # Default confidence
    })
    return result


async def run_trading_analysis(state: LangGraphServerState, config: RunnableConfig) -> LangGraphServerState:
    """Main entry point for LangGraph server - runs the complete trading analysis."""
    try:
        # Import TradingAgentsGraph locally to avoid circular imports
        import importlib
        trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
        TradingAgentsGraph = trading_graph_module.TradingAgentsGraph
        
        # Convert to internal state format
        agent_state = convert_to_agent_state(state)
        
        # Create trading graph instance
        trading_graph_instance = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            debug=False,
            config=DEFAULT_CONFIG
        )
        
        # Run the analysis using the internal graph
        final_state = trading_graph_instance.graph.invoke(agent_state)
        
        # Convert back to server state format
        result = convert_from_agent_state(final_state, state)
        
        return result
        
    except Exception as e:
        error_msg = f"Trading analysis error: {str(e)}"
        
        # Return error state
        result = state.copy()
        result.update({
            "fundamentals_report": error_msg,
            "market_analysis_report": error_msg,
            "news_sentiment_report": error_msg,
            "social_media_report": error_msg,
            "research_report": error_msg,
            "risk_assessment": error_msg,
            "trading_recommendation": error_msg,
            "confidence_score": 0.0
        })
        
        return result


# Create the original detailed graph directly for LangGraph Studio
def create_studio_compatible_graph():
    """Create the original TradingAgentsGraph for LangGraph Studio with all nodes visible."""
    # Import TradingAgentsGraph locally to avoid circular imports
    import importlib
    trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
    TradingAgentsGraph = trading_graph_module.TradingAgentsGraph
    
    # Create the original detailed graph instance
    trading_graph_instance = TradingAgentsGraph(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config=DEFAULT_CONFIG
    )
    
    # Return the original graph directly - it has all the detailed nodes
    return trading_graph_instance.graph

# Create the detailed graph for LangGraph Studio
graph = create_studio_compatible_graph()

# Export all the trading agent functions for compatibility
__all__ = [
    "FinancialSituationMemory",
    "Toolkit",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_research_manager",
    "create_fundamentals_analyst",
    "create_market_analyst",
    "create_neutral_debator",
    "create_news_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_social_media_analyst",
    "create_trader",
    "graph",
    "LangGraphServerState",
    "run_trading_analysis"
]
