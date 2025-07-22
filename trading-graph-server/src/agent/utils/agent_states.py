from typing import Annotated, Sequence
from datetime import date, timedelta, datetime
from typing_extensions import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Simple reducer that always takes the latest value
def update_value(left, right):
    return right if right is not None else left


# Debate state reducer that can handle concurrent updates
def merge_debate_state(left, right):
    """Merge debate states from multiple agents safely."""
    if left is None:
        return right
    if right is None:
        return left
    
    # Create a merged state
    merged = left.copy() if isinstance(left, dict) else {}
    
    # Update with right values, preserving existing data
    for key, value in right.items():
        if key == "count":
            # For count, take the maximum to ensure proper sequencing
            merged[key] = max(merged.get(key, 0), value)
        elif key in ["bull_history", "bear_history", "history"]:
            # For history fields, merge intelligently
            existing = merged.get(key, "")
            if value and value not in existing:
                merged[key] = existing + "\n" + value if existing else value
            elif value:
                merged[key] = value
        else:
            # For other fields, take the latest non-empty value
            if value:
                merged[key] = value
            elif key not in merged:
                merged[key] = ""
    
    return merged


# Risk debate state reducer
def merge_risk_debate_state(left, right):
    """Merge risk debate states from multiple agents safely."""
    if left is None:
        return right
    if right is None:
        return left
    
    # Create a merged state
    merged = left.copy() if isinstance(left, dict) else {}
    
    # Update with right values
    for key, value in right.items():
        if key == "count":
            # For count, take the maximum
            merged[key] = max(merged.get(key, 0), value)
        elif value:  # Only update if value is not empty
            merged[key] = value
        elif key not in merged:
            merged[key] = ""
    
    return merged


# Researcher team state
class InvestDebateState(TypedDict):
    bull_history: Annotated[str, update_value]
    bear_history: Annotated[str, update_value]
    history: Annotated[str, update_value]
    current_response: Annotated[str, update_value]
    judge_decision: Annotated[str, update_value]
    count: Annotated[int, update_value]


# Risk management team state
class RiskDebateState(TypedDict):
    risky_history: Annotated[str, update_value]
    safe_history: Annotated[str, update_value]
    neutral_history: Annotated[str, update_value]
    history: Annotated[str, update_value]
    latest_speaker: Annotated[str, update_value]
    current_risky_response: Annotated[str, update_value]
    current_safe_response: Annotated[str, update_value]
    current_neutral_response: Annotated[str, update_value]
    judge_decision: Annotated[str, update_value]
    count: Annotated[int, update_value]


class AgentState(TypedDict):
    """Represents the state of our multi-agent system with separate message channels."""
    
    # Basic information
    company_of_interest: Annotated[str, update_value]
    trade_date: Annotated[str, update_value]
    
    # Analyst message channels
    market_messages: Annotated[Sequence[BaseMessage], add_messages]
    social_messages: Annotated[Sequence[BaseMessage], add_messages]
    news_messages: Annotated[Sequence[BaseMessage], add_messages]
    fundamentals_messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Reports from analysts (using update_value to handle concurrent updates)
    market_report: Annotated[Optional[str], update_value]
    sentiment_report: Annotated[Optional[str], update_value]
    news_report: Annotated[Optional[str], update_value]
    fundamentals_report: Annotated[Optional[str], update_value]
    
    # Debate states (using custom reducers to prevent concurrent update errors)
    investment_debate_state: Annotated[Optional[InvestDebateState], merge_debate_state]
    risk_debate_state: Annotated[Optional[RiskDebateState], merge_risk_debate_state]
    
    # Investment and trading plans
    investment_plan: Annotated[Optional[str], update_value]
    trader_investment_plan: Annotated[Optional[str], update_value]
    final_trade_decision: Annotated[Optional[str], update_value]
