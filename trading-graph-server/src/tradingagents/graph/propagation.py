# TradingAgents/graph/propagation.py

from typing import Dict, Any
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph with parallel analyst support."""
        return {
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            
            # Initialize empty message channels for each analyst
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
            "investment_debate_state": InvestDebateState({
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "current_response": "",
                "judge_decision": "",
                "count": 0
            }),
            "risk_debate_state": RiskDebateState({
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
                "count": 0,
            }),
            
            # Initialize other fields
            "investment_plan": "",
            "trader_investment_plan": "",
            "final_trade_decision": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for graph execution."""
        return {
            "config": {"recursion_limit": self.max_recur_limit}
        }
