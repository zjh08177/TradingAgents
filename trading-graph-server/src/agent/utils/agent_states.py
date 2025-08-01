from typing import Annotated, Sequence
from datetime import date, timedelta, datetime
from typing_extensions import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# TASK 5.2: Import optimized state management
from .state_optimizer import (
    create_optimized_message_reducer,
    create_optimized_report_reducer, 
    create_optimized_debate_reducer,
    get_state_manager
)

# TASK 5.2: Memory-optimized reducers (40% memory reduction target)
optimized_message_reducer = create_optimized_message_reducer()
optimized_report_reducer = create_optimized_report_reducer()
optimized_debate_reducer = create_optimized_debate_reducer()

# Simple reducer that always takes the latest value
def update_value(left, right):
    return right if right is not None else left

# TASK 5.2: Legacy reducers kept for backward compatibility but optimized
def merge_debate_state(left, right):
    """TASK 5.2: Optimized debate state merger with memory efficiency."""
    return optimized_debate_reducer(left, right)

def merge_risk_debate_state(left, right):
    """TASK 5.2: Optimized risk debate state merger with memory efficiency."""
    return optimized_debate_reducer(left, right)


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
    """
    TASK 5.2: Memory-optimized multi-agent system state with atomic updates
    Target: 40% memory reduction through optimized reducers and state validation
    """
    
    # Basic information
    company_of_interest: Annotated[str, update_value]
    trade_date: Annotated[str, update_value]
    
    # TASK 5.2: Optimized analyst message channels with memory efficiency
    market_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    social_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    news_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    fundamentals_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    
    # TASK 5.2: Optimized reports with conflict resolution and validation
    market_report: Annotated[Optional[str], optimized_report_reducer]
    sentiment_report: Annotated[Optional[str], optimized_report_reducer]
    news_report: Annotated[Optional[str], optimized_report_reducer]
    fundamentals_report: Annotated[Optional[str], optimized_report_reducer]
    
    # TASK 5.2: Optimized debate states with atomic updates and memory efficiency
    investment_debate_state: Annotated[Optional[InvestDebateState], merge_debate_state]
    risk_debate_state: Annotated[Optional[RiskDebateState], merge_risk_debate_state]
    
    # Research debate state for multi-round bull/bear research debates
    research_debate_state: Annotated[Optional[dict], update_value]
    
    # Investment and trading plans
    investment_plan: Annotated[Optional[str], update_value]
    trader_investment_plan: Annotated[Optional[str], update_value]
    final_trade_decision: Annotated[Optional[str], update_value]
    
    # TASK 7.5.2: Add aggregation ready flag and report readiness tracking
    aggregation_ready: Annotated[Optional[bool], update_value]
    report_readiness: Annotated[Optional[dict], update_value]
