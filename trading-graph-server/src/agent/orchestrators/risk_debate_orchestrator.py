"""
Risk Debate Orchestrator Node
Orchestrates parallel execution of risk debators
Part of Feature 2: Parallel Risk Debators
"""
import asyncio
from typing import Dict
import logging
from ..utils.agent_states import AgentState

logger = logging.getLogger(__name__)

def create_risk_debate_orchestrator():
    """
    Orchestrates parallel execution of risk debators
    
    Features:
    - Initializes risk debate state with parallel flags
    - Prepares shared context for all debators
    - Tracks execution timing for performance monitoring
    - Ensures all debators have same input data
    
    Returns:
        Async orchestrator node function
    """
    
    async def orchestrator_node(state: AgentState) -> AgentState:
        logger.info("🎭 RISK DEBATE ORCHESTRATOR: Starting parallel debate preparation")
        
        # Log optimization activation
        from ..utils.optimization_logger import optimization_tracker
        optimization_tracker.log_optimization_start("PARALLEL_RISK_EXECUTION", "3 debators will run concurrently")
        
        # Initialize risk debate state with parallel flags
        risk_state = state.get("risk_debate_state", {})
        
        # Mark this as parallel execution
        risk_state.update({
            "parallel_execution": True,
            "debate_start_time": asyncio.get_event_loop().time()
        })
        
        # Set up shared context for all debators
        # This ensures all three debators work with the same data
        shared_context = {
            "investment_plan": state.get("investment_plan", ""),
            "trader_decision": state.get("trader_investment_plan", ""),
            "market_report": state.get("market_report", ""),
            "sentiment_report": state.get("sentiment_report", ""),
            "news_report": state.get("news_report", ""),
            "fundamentals_report": state.get("fundamentals_report", "")
        }
        
        # Store shared context in risk state
        risk_state["shared_context"] = shared_context
        
        # Initialize response fields if not present
        if "current_risky_response" not in risk_state:
            risk_state["current_risky_response"] = ""
        if "current_safe_response" not in risk_state:
            risk_state["current_safe_response"] = ""
        if "current_neutral_response" not in risk_state:
            risk_state["current_neutral_response"] = ""
        
        # Log preparation details
        logger.info("📊 Prepared shared context for parallel debators")
        logger.info(f"   - Investment plan: {len(shared_context.get('investment_plan', ''))} chars")
        logger.info(f"   - Market data: {len(shared_context.get('market_report', ''))} chars")
        logger.info(f"   - Sentiment data: {len(shared_context.get('sentiment_report', ''))} chars")
        logger.info("🚀 Ready for parallel risk debate execution")
        
        return {"risk_debate_state": risk_state}
    
    return orchestrator_node