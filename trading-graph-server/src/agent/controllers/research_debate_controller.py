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
        
        # Initialize fields with defaults
        if "current_round" not in debate_state:
            debate_state["current_round"] = 0
        if "max_rounds" not in debate_state:
            debate_state["max_rounds"] = config.get("max_research_debate_rounds", 1)
        if "debate_history" not in debate_state:
            debate_state["debate_history"] = []
        if "consensus_reached" not in debate_state:
            debate_state["consensus_reached"] = False
        
        current_round = debate_state["current_round"]
        max_rounds = debate_state["max_rounds"]
        
        # Increment round for this execution
        debate_state["current_round"] = current_round + 1
        
        logger.info(f"📊 Starting Round {debate_state['current_round']}/{max_rounds}")
        logger.info("⚡ Bull and Bear researchers will execute concurrently")
        
        # Log debate status
        if current_round == 0:
            logger.info("🔄 Starting new research debate cycle")
        else:
            logger.info(f"🔄 Continuing debate - Previous rounds: {current_round}")
            if debate_state.get("debate_history"):
                logger.info(f"📚 Debate history: {len(debate_state['debate_history'])} rounds recorded")
        
        return {"research_debate_state": debate_state}
    
    return controller_node