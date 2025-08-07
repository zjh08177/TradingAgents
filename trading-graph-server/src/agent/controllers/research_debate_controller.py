"""
Research Debate Controller Node - Always parallel execution
Controls multi-round bull/bear debate flow
"""
from typing import Dict
from ..utils.agent_states import AgentState
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

def create_research_debate_controller(config: Dict):
    """
    Controls bull/bear debate flow (always parallel)
    
    Features:
    - Manages debate rounds (current_round tracking)
    - Tracks debate history
    
    Args:
        config: Configuration dict containing max_research_debate_rounds
        
    Returns:
        Async controller node function
    """
    
    async def controller_node(state: AgentState) -> AgentState:
        logger.info("🎯 RESEARCH DEBATE CONTROLLER: Managing debate")
        
        # Initialize or get debate state
        debate_state = state.get("research_debate_state", {})
        
        # Initialize fields with defaults - start at round 1 consistently
        if "current_round" not in debate_state:
            debate_state["current_round"] = 1
        if "max_rounds" not in debate_state:
            debate_state["max_rounds"] = config.get("max_research_debate_rounds", 3)
        if "debate_history" not in debate_state:
            debate_state["debate_history"] = []
        if "consensus_reached" not in debate_state:
            debate_state["consensus_reached"] = False
        
        current_round = debate_state["current_round"]
        max_rounds = debate_state["max_rounds"]
        
        logger.info(f"📊 Starting Round {current_round}/{max_rounds}")
        logger.info("⚡ Bull and Bear researchers will execute concurrently")
        
        # Log debate status
        if current_round == 1:
            logger.info("🔄 Starting new research debate cycle")
        else:
            logger.info(f"🔄 Continuing debate - Previous rounds: {current_round - 1}")
            if debate_state.get("debate_history"):
                logger.info(f"📚 Debate history: {len(debate_state['debate_history'])} rounds recorded")
        
        # Increment round for NEXT execution (after this round completes)
        debate_state["current_round"] = current_round + 1
        
        return {"research_debate_state": debate_state}
    
    return controller_node