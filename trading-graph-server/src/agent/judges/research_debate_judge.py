"""
Research Debate Judge Node
Evaluates bull/bear arguments and determines consensus
Part of Feature 1: Multi-Round Bull/Bear Research Debate
"""
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ..utils.agent_states import AgentState
from ..utils.connection_retry import safe_llm_invoke
import logging

logger = logging.getLogger(__name__)

def create_research_debate_judge(llm):
    """
    Evaluates bull/bear arguments and determines consensus
    
    Features:
    - Analyzes quality of bull and bear arguments
    - Checks for data support and evidence
    - Determines if consensus has been reached
    - Provides feedback for next round focus
    - Updates debate history with round results
    
    Args:
        llm: Language model for evaluation
        
    Returns:
        Async judge node function
    """
    
    async def judge_node(state: AgentState) -> AgentState:
        logger.info("⚖️ RESEARCH DEBATE JUDGE: Evaluating arguments")
        
        debate_state = state.get("research_debate_state", {})
        investment_state = state.get("investment_debate_state", {})
        
        # Get current round arguments
        bull_argument = investment_state.get("bull_history", "")
        bear_argument = investment_state.get("bear_history", "")
        current_round = debate_state.get("current_round", 1)
        
        # Extract only the latest arguments if multiple rounds
        if "\n" in bull_argument:
            # Get the last argument from history
            bull_parts = bull_argument.split("\n")
            bull_argument = bull_parts[-1] if bull_parts else bull_argument
        if "\n" in bear_argument:
            bear_parts = bear_argument.split("\n")
            bear_argument = bear_parts[-1] if bear_parts else bear_argument
        
        logger.info(f"📊 Evaluating Round {current_round} arguments")
        
        # Create evaluation prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Research Debate Judge evaluating investment arguments.

Your role is to:
1. Assess the quality and completeness of both bull and bear arguments
2. Check if arguments are well-supported with data and evidence
3. Determine if sufficient analysis has been done for a decision
4. Identify any critical gaps that need addressing

Evaluation criteria:
- Data Support: Are claims backed by specific metrics, numbers, or evidence?
- Completeness: Have all major investment factors been addressed?
- Balance: Are both bullish and bearish perspectives thoroughly explored?
- Actionability: Is there enough information to make an informed decision?

Response format:
CONSENSUS REACHED: Yes/No
KEY UNRESOLVED POINTS: [List any critical gaps]
NEXT ROUND FOCUS: [Specific areas to explore if consensus not reached]
QUALITY SCORE: [1-10 rating of argument quality]
JUDGE SUMMARY: [Brief evaluation summary]"""),
            ("user", f"""Round {current_round} Arguments:

BULL ARGUMENT:
{bull_argument}

BEAR ARGUMENT:
{bear_argument}

Evaluate these arguments and determine if consensus has been reached for making an investment decision.""")
        ])
        
        # Get judge evaluation
        messages = [
            {"role": "system", "content": prompt.format_messages()[0].content},
            {"role": "user", "content": prompt.format_messages()[1].content}
        ]
        
        response = await safe_llm_invoke(llm, messages)
        judge_content = response.content
        
        # Parse response to determine consensus
        content_lower = judge_content.lower()
        consensus_reached = "consensus reached: yes" in content_lower
        
        # Extract quality score if present
        quality_score = 5  # default
        if "quality score:" in content_lower:
            try:
                score_text = content_lower.split("quality score:")[1].split("\n")[0]
                quality_score = int(''.join(filter(str.isdigit, score_text)))
            except:
                pass
        
        # Update debate state
        debate_state["consensus_reached"] = consensus_reached
        debate_state["judge_feedback"] = judge_content
        debate_state["last_quality_score"] = quality_score
        
        # Add to debate history
        if "debate_history" not in debate_state:
            debate_state["debate_history"] = []
            
        debate_state["debate_history"].append({
            "round": current_round,
            "bull": bull_argument,
            "bear": bear_argument,
            "judge": judge_content,
            "consensus": consensus_reached,
            "quality_score": quality_score
        })
        
        # Log decision
        logger.info(f"⚖️ Judge Decision: Consensus={'✅' if consensus_reached else '❌'} | Quality: {quality_score}/10")
        
        if consensus_reached:
            logger.info("✅ Consensus reached - proceeding to research manager")
        else:
            logger.info(f"🔄 No consensus - continuing debate (Round {current_round + 1})")
            
        return {"research_debate_state": debate_state}
    
    return judge_node