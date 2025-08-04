#!/usr/bin/env python3
"""
Enhanced Agent States for Send API + Conditional Edges Architecture
Implements separate state keys for each analyst to prevent concurrent update conflicts
"""

from typing import Annotated, Sequence, Dict, Optional, List
from datetime import date, timedelta, datetime
from typing_extensions import TypedDict, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Import existing optimized reducers from agent_states to ensure compatibility
from .agent_states import (
    optimized_message_reducer,
    optimized_report_reducer,
    optimized_debate_reducer,
    update_value,
    merge_debate_state,
    merge_risk_debate_state,
    InvestDebateState,
    RiskDebateState
)

# Enhanced reducer for error tracking
def merge_errors(left: Optional[Dict[str, str]], right: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Merge error dictionaries, preserving all errors"""
    if not left and not right:
        return None
    if not left:
        return right
    if not right:
        return left
    return {**left, **right}

# Enhanced reducer for execution times
def merge_execution_times(left: Optional[Dict[str, float]], right: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
    """Merge execution time dictionaries"""
    if not left and not right:
        return None
    if not left:
        return right
    if not right:
        return left
    return {**left, **right}

# Using imported debate states from agent_states for compatibility

class EnhancedAnalystState(TypedDict):
    """
    Enhanced state schema for Send API + Conditional Edges parallel execution
    Uses separate keys for each analyst to prevent concurrent update conflicts
    Maintains backward compatibility with existing system
    """
    
    # ===== BASIC INFORMATION =====
    company_of_interest: Annotated[str, update_value]
    trade_date: Annotated[str, update_value]
    step: Annotated[Optional[str], update_value]
    
    # ===== INDIVIDUAL ANALYST REPORTS (Separate keys - no conflicts) =====
    market_report: Annotated[Optional[str], optimized_report_reducer]
    news_report: Annotated[Optional[str], optimized_report_reducer]
    sentiment_report: Annotated[Optional[str], optimized_report_reducer]  # Keep existing name for social
    fundamentals_report: Annotated[Optional[str], optimized_report_reducer]
    
    # ===== INDIVIDUAL ANALYST STATUS TRACKING =====
    market_analyst_status: Annotated[Optional[Literal["pending", "running", "completed", "error"]], update_value]
    news_analyst_status: Annotated[Optional[Literal["pending", "running", "completed", "error"]], update_value]
    social_analyst_status: Annotated[Optional[Literal["pending", "running", "completed", "error"]], update_value]
    fundamentals_analyst_status: Annotated[Optional[Literal["pending", "running", "completed", "error"]], update_value]
    
    # ===== INDIVIDUAL ANALYST MESSAGES (Tool execution history) =====
    market_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    news_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    social_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    fundamentals_messages: Annotated[Sequence[BaseMessage], optimized_message_reducer]
    
    # ===== TOOL EXECUTION TRACKING =====
    market_tool_calls: Annotated[Optional[int], update_value]
    news_tool_calls: Annotated[Optional[int], update_value]
    social_tool_calls: Annotated[Optional[int], update_value]
    fundamentals_tool_calls: Annotated[Optional[int], update_value]
    
    # ===== TIMING INFORMATION =====
    analyst_execution_times: Annotated[Optional[Dict[str, float]], merge_execution_times]
    parallel_start_time: Annotated[Optional[float], update_value]
    parallel_end_time: Annotated[Optional[float], update_value]
    total_parallel_time: Annotated[Optional[float], update_value]
    
    # ===== ERROR TRACKING =====
    analyst_errors: Annotated[Optional[Dict[str, str]], merge_errors]
    failed_analysts: Annotated[Optional[List[str]], update_value]
    
    # ===== AGGREGATION STATUS =====
    aggregation_status: Annotated[Optional[Literal["pending", "partial_success", "complete_failure", "minimal_success", "success"]], update_value]
    successful_analysts_count: Annotated[Optional[int], update_value]
    aggregation_ready: Annotated[Optional[bool], update_value]
    low_quality_reports: Annotated[Optional[bool], update_value]
    empty_reports: Annotated[Optional[List[str]], update_value]
    
    # ===== PERFORMANCE METRICS =====
    parallel_execution_metrics: Annotated[Optional[Dict[str, float]], update_value]
    speedup_factor: Annotated[Optional[float], update_value]
    send_api_enabled: Annotated[Optional[bool], update_value]
    
    # ===== EXISTING COMPATIBILITY FIELDS =====
    # These maintain compatibility with existing research and risk management
    investment_debate_state: Annotated[Optional[InvestDebateState], merge_debate_state]
    risk_debate_state: Annotated[Optional[RiskDebateState], merge_risk_debate_state]
    research_debate_state: Annotated[Optional[dict], update_value]
    
    # Investment and trading plans
    investment_plan: Annotated[Optional[str], update_value]
    trader_investment_plan: Annotated[Optional[str], update_value]
    final_trade_decision: Annotated[Optional[str], update_value]
    
    # Legacy compatibility
    report_readiness: Annotated[Optional[dict], update_value]
    parallel_execution_complete: Annotated[Optional[bool], update_value]
    
    # ===== BACKWARD COMPATIBILITY MAPPING =====
    # These are computed properties that map to the enhanced state
    # Handled by BackwardCompatibilityAdapter

class PerformanceMetrics(TypedDict):
    """Performance metrics for parallel analyst execution"""
    execution_time: float
    start_time: float
    end_time: float
    tool_calls_made: int
    memory_usage_mb: Optional[float]
    status: Literal["success", "error", "timeout", "partial"]
    error_message: Optional[str]

class AnalystExecutionResult(TypedDict):
    """Structured result from individual analyst execution"""
    analyst_name: str
    report: Optional[str]
    execution_metrics: PerformanceMetrics
    messages: List[BaseMessage]
    tool_results: Optional[List[Dict]]

class BackwardCompatibilityAdapter:
    """Ensures new enhanced state works with existing code"""
    
    @staticmethod
    def adapt_state_for_research_manager(state: EnhancedAnalystState) -> Dict:
        """Convert enhanced state to format expected by research manager"""
        return {
            "market_report": state.get("market_report", ""),
            "news_report": state.get("news_report", ""),
            "sentiment_report": state.get("sentiment_report", ""),  # Social reports use this key
            "fundamentals_report": state.get("fundamentals_report", ""),
            "low_quality_reports": state.get("low_quality_reports", False),
            "empty_reports": state.get("empty_reports", []),
            "aggregation_ready": state.get("aggregation_ready", False),
            # Legacy field mapping
            "aggregation_status": state.get("aggregation_status", "pending"),
            # CRITICAL FIX: Include investment_plan for router logic
            "investment_plan": state.get("investment_plan", None),
            "research_debate_state": state.get("research_debate_state", {}),
            "investment_debate_state": state.get("investment_debate_state", {})
        }
    
    @staticmethod
    def get_analyst_summary(state: EnhancedAnalystState) -> Dict[str, str]:
        """Get summary of analyst execution status"""
        return {
            "market": state.get("market_analyst_status", "pending"),
            "news": state.get("news_analyst_status", "pending"),
            "social": state.get("social_analyst_status", "pending"),
            "fundamentals": state.get("fundamentals_analyst_status", "pending")
        }
    
    @staticmethod
    def get_performance_summary(state: EnhancedAnalystState) -> Dict:
        """Get performance metrics summary"""
        execution_times = state.get("analyst_execution_times", {})
        return {
            "total_time": state.get("total_parallel_time", 0),
            "speedup_factor": state.get("speedup_factor", 1.0),
            "successful_analysts": state.get("successful_analysts_count", 0),
            "individual_times": execution_times,
            "parallel_efficiency": (
                1.0 - (max(execution_times.values()) - min(execution_times.values())) / max(execution_times.values()) 
                if execution_times and max(execution_times.values()) > 0 
                else 0.0
            )
        }

# Note: No type alias to avoid channel conflicts
# Use BackwardCompatibilityAdapter.adapt_state_for_research_manager() instead