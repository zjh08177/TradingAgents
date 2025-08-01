"""
Unified Research Manager with Judge Logic - Always parallel debate
Handles debate evaluation, consensus checking, and final investment planning
"""
import asyncio
import json
import logging
import time
from typing import Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from agent.utils.connection_retry import safe_llm_invoke
from ..utils.agent_states import AgentState
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)

def create_research_manager(llm, memory, config: Dict = None):
    """
    Unified Research Manager that handles both judging and final summarization
    
    Features:
    - Evaluates debate quality and consensus (judge functionality)
    - Manages multi-round flow or proceeds to final summary
    - Combines analyst reports with debate outcome
    """
    config = config or {}
    
    async def research_manager_node(state: AgentState) -> AgentState:
        logger.info("🔬 RESEARCH MANAGER: Processing debate and analysis")
        
        debate_state = state.get("research_debate_state", {})
        investment_state = state.get("investment_debate_state", {})
        
        current_round = debate_state.get("current_round", 1)
        max_rounds = debate_state.get("max_rounds", 1)
        
        # Get arguments from the current round
        bull_argument = investment_state.get("bull_history", "")
        bear_argument = investment_state.get("bear_history", "")
        
        # Extract only the latest arguments if multiple rounds
        if "\n" in bull_argument:
            bull_parts = bull_argument.split("\n")
            bull_argument = bull_parts[-1] if bull_parts else bull_argument
        if "\n" in bear_argument:
            bear_parts = bear_argument.split("\n")
            bear_argument = bear_parts[-1] if bear_parts else bear_argument
        
        # Check if arguments are present
        bull_ready = len(bull_argument.strip()) > 100
        bear_ready = len(bear_argument.strip()) > 100
        
        # Evaluate the debate quality (judge functionality)
        consensus_reached = False
        judge_feedback = ""
        quality_score = 5  # default
        
        if bull_ready or bear_ready:
            # Perform judge evaluation
            judge_prompt = ChatPromptTemplate.from_messages([
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
{bull_argument if bull_ready else "NO BULL ARGUMENT RECEIVED"}

BEAR ARGUMENT:
{bear_argument if bear_ready else "NO BEAR ARGUMENT RECEIVED"}

Evaluate these arguments and determine if consensus has been reached for making an investment decision.""")
            ])
            
            # Get judge evaluation
            messages = [
                {"role": "system", "content": judge_prompt.format_messages()[0].content},
                {"role": "user", "content": judge_prompt.format_messages()[1].content}
            ]
            
            response = await safe_llm_invoke(llm, messages)
            judge_content = response.content
            judge_feedback = judge_content
            
            # Parse response to determine consensus
            content_lower = judge_content.lower()
            consensus_reached = "consensus reached: yes" in content_lower
            
            # Extract quality score if present
            if "quality score:" in content_lower:
                try:
                    score_text = content_lower.split("quality score:")[1].split("\n")[0]
                    quality_score = int(''.join(filter(str.isdigit, score_text)))
                except:
                    pass
            
            # Update debate state with judge results
            debate_state["consensus_reached"] = consensus_reached
            debate_state["judge_feedback"] = judge_content
            debate_state["last_quality_score"] = quality_score
            
            # Add to debate history
            if "debate_history" not in debate_state:
                debate_state["debate_history"] = []
                
            debate_state["debate_history"].append({
                "round": current_round,
                "bull": bull_argument if bull_ready else "NO ARGUMENT",
                "bear": bear_argument if bear_ready else "NO ARGUMENT",
                "judge": judge_content,
                "consensus": consensus_reached,
                "quality_score": quality_score
            })
            
            logger.info(f"⚖️ Judge Decision: Consensus={'✅' if consensus_reached else '❌'} | Quality: {quality_score}/10")
        
        # Decide next action based on consensus and rounds
        if consensus_reached or current_round >= max_rounds:
            # Proceed to generate investment plan
            logger.info("📊 Generating final investment plan...")
            
            # Get all analyst reports
            market_research_report = state.get("market_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            sentiment_report = state.get("sentiment_report", "")
            
            # Combine all information
            combined_analysis = f"""
ANALYST REPORTS:
================
Market Analysis: {market_research_report}

News Analysis: {news_report}

Fundamentals Analysis: {fundamentals_report}

Sentiment Analysis: {sentiment_report}

DEBATE OUTCOME:
===============
Total Rounds: {current_round}
Final Quality Score: {quality_score}/10
Consensus Reached: {'Yes' if consensus_reached else 'No (max rounds reached)'}

BULL POSITION:
{bull_argument if bull_ready else "No argument provided"}

BEAR POSITION:
{bear_argument if bear_ready else "No argument provided"}

JUDGE EVALUATION:
{judge_feedback}
"""
            
            # Generate investment plan
            plan_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are the Research Manager creating a final investment recommendation.

Based on the comprehensive analysis and debate outcome, provide:
1. Clear investment recommendation (BUY/SELL/HOLD)
2. Confidence level (HIGH/MEDIUM/LOW)
3. Key supporting points from both analysis and debate
4. Risk factors to monitor
5. Suggested position sizing based on confidence

Format your response as a structured investment plan."""),
                ("user", f"""Create investment plan based on this analysis:

{combined_analysis}

Provide a clear, actionable investment recommendation.""")
            ])
            
            messages = [
                {"role": "system", "content": plan_prompt.format_messages()[0].content},
                {"role": "user", "content": plan_prompt.format_messages()[1].content}
            ]
            
            response = await safe_llm_invoke(llm, messages)
            investment_plan = response.content
            
            # Save to memory
            memory.save_memory(f"Investment plan generated after {current_round} rounds: {investment_plan[:200]}...")
            
            # Update state with final plan
            logger.info("✅ Investment plan complete - proceeding to risk management")
            
            return {
                "investment_plan": investment_plan,
                "research_debate_state": debate_state
            }
        else:
            # Continue debate - no investment plan yet
            logger.info(f"🔄 No consensus - continuing debate (Round {current_round + 1})")
            
            # Don't generate investment plan - let controller handle next round
            return {
                "research_debate_state": debate_state
            }
    
    return research_manager_node