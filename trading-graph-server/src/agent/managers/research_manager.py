"""
Unified Research Manager with Judge Logic - FIXED VERSION
Handles debate evaluation, consensus checking, and final investment planning
FIXES: Flexible consensus detection, circuit breaker for infinite loops
"""
import asyncio
import json
import logging
import time
from typing import Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from ..utils.connection_retry import safe_llm_invoke
from ..utils.agent_states import AgentState
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter
from ..utils.safe_state_access import create_safe_state_wrapper, get_safe_format_vars

logger = logging.getLogger(__name__)

class ResearchCircuitBreaker:
    """Circuit breaker to prevent infinite debate loops"""
    def __init__(self, max_attempts: int = 5):
        self.attempts = {}
        self.max_attempts = max_attempts
    
    def check_loop(self, state_id: str) -> bool:
        """Check if we've exceeded max attempts for this state"""
        self.attempts[state_id] = self.attempts.get(state_id, 0) + 1
        
        if self.attempts[state_id] >= self.max_attempts:
            logger.warning(f"⚠️ Circuit breaker: Forcing consensus after {self.max_attempts} attempts")
            return True
        return False
    
    def reset(self, state_id: str):
        """Reset counter for a state"""
        if state_id in self.attempts:
            del self.attempts[state_id]

# Global circuit breaker instance
circuit_breaker = ResearchCircuitBreaker()

def create_research_manager(llm, memory, config: Dict = None):
    """
    Unified Research Manager with FIXED consensus logic
    
    Features:
    - Flexible consensus detection (not just exact string matching)
    - Circuit breaker to prevent infinite loops
    - Force consensus after quality debates
    - Better error handling
    """
    config = config or {}
    
    async def research_manager_node(state: AgentState) -> AgentState:
        logger.info("🔬 RESEARCH MANAGER: Processing debate and analysis")
        
        # CRITICAL FIX: Create safe state wrapper to prevent KeyError
        safe_state = create_safe_state_wrapper(state)
        
        # Get trace ID for circuit breaker
        trace_id = safe_state.get("trace_id", "default")
        
        debate_state = safe_state.get("research_debate_state", {})
        investment_state = safe_state.get("investment_debate_state", {})
        
        current_round = debate_state.get("current_round", 1)
        max_rounds = config.get("max_research_debate_rounds", 3)  # Standardized config key
        
        # CRITICAL FIX: The controller increments BEFORE researchers execute
        # So current_round is the NEXT round, not the round that just executed
        executed_round = current_round - 1 if current_round > 1 else 1
        
        # VALIDATION: Ensure round values are sane
        if current_round < 1:
            logger.warning(f"⚠️ Invalid current_round={current_round}, resetting to 1")
            current_round = 1
            executed_round = 1
            debate_state["current_round"] = 1
        if max_rounds < 1:
            logger.warning(f"⚠️ Invalid max_rounds={max_rounds}, resetting to 3")
            max_rounds = 3
            debate_state["max_rounds"] = 3
        
        # VALIDATION: Log round progress clearly
        logger.info(f"🔢 ROUND VALIDATION: Controller_Round={current_round}, Executed_Round={executed_round}, Max={max_rounds}")
        
        # CRITICAL FIX: Check circuit breaker
        force_consensus = circuit_breaker.check_loop(trace_id)
        
        # SIMPLIFIED APPROACH: Get latest arguments from current round  
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
        bull_ready = len(bull_argument.strip()) > 50
        bear_ready = len(bear_argument.strip()) > 50
        
        # Add to debate history for tracking (without judging)
        if "debate_history" not in debate_state:
            debate_state["debate_history"] = []
        
        # Record this round's arguments using the ACTUAL executed round number
        debate_state["debate_history"].append({
            "round": executed_round,
            "bull": bull_argument if bull_ready else "NO ARGUMENT",
            "bear": bear_argument if bear_ready else "NO ARGUMENT"
        })
        
        logger.info(f"📝 Round {executed_round} recorded: Bull={'✅' if bull_ready else '❌'} Bear={'✅' if bear_ready else '❌'}")
        
        # SIMPLE TERMINATION: Check if we've completed enough rounds
        debate_should_end = False
        
        if executed_round >= max_rounds:
            logger.info(f"🔚 MAX ROUNDS REACHED: Ending debate at executed round {executed_round}/{max_rounds}")
            debate_should_end = True
        elif force_consensus:
            logger.warning(f"⚠️ Circuit breaker triggered: Forcing end after {executed_round} executed rounds")
            debate_should_end = True
        
        # Simple decision: continue or end
        if not debate_should_end:
            # Continue the debate - controller will handle round increment
            logger.info(f"📢 Continuing debate (Round {executed_round}/{max_rounds} completed)")
            logger.info(f"📢 Controller will advance to round {current_round} next")
            
            # Return state to continue debate - do NOT increment here (controller handles it)
            return {
                "research_debate_state": debate_state,
                "investment_debate_state": investment_state,
                # Signal to continue debate
                "continue_debate": True
            }
        
        # If we reach here, debate has ended - generate investment plan
        logger.info("📊 Debate completed - generating final investment plan from final statements...")
        
        # Reset circuit breaker for this trace
        circuit_breaker.reset(trace_id)
        
        # Get all analyst reports using safe state access
        market_research_report = safe_state.get("market_report", "")
        news_report = safe_state.get("news_report", "")
        fundamentals_report = safe_state.get("fundamentals_report", "")
        sentiment_report = safe_state.get("sentiment_report", "")
        
        # Check report quality
        reports_quality = {
            "market": bool(market_research_report and len(market_research_report) > 100),
            "news": bool(news_report and len(news_report) > 100),
            "fundamentals": bool(fundamentals_report and len(fundamentals_report) > 100),
            "sentiment": bool(sentiment_report and len(sentiment_report) > 100)
        }
        
        valid_reports = sum(reports_quality.values())
        if valid_reports < 2:
            logger.warning(f"⚠️ Low quality reports detected: Only {valid_reports}/4 reports are valid")
            logger.warning(f"Report quality: {reports_quality}")
        
        # Create investment plan using final bull/bear statements
        system_prompt = """You are a senior investment strategist creating a final investment recommendation.
Synthesize the bull and bear arguments along with all analyst reports into a clear, actionable investment plan.
Use the final statements from both sides to make your recommendation."""

        # Format user prompt with final statements
        bull_text = bull_argument if bull_ready else "No final bull argument provided"
        bear_text = bear_argument if bear_ready else "No final bear argument provided"
        
        user_prompt = f"""Based on all the analysis and final debate statements, create a comprehensive investment plan.

ANALYST REPORTS:
Market Analysis: {market_research_report}
News Analysis: {news_report}
Fundamentals Analysis: {fundamentals_report}
Sentiment Analysis: {sentiment_report}

FINAL DEBATE POSITIONS:
=======================
Total Debate Rounds Completed: {executed_round}

FINAL BULL ARGUMENT:
{bull_text}

FINAL BEAR ARGUMENT:
{bear_text}

Create a detailed investment plan that includes:
1. Investment Recommendation: BUY/SELL/HOLD with confidence level
2. Position Sizing: Recommended allocation percentage
3. Entry Strategy: Specific price levels or conditions
4. Risk Management: Stop loss levels and risk mitigation
5. Time Horizon: Short-term (days), medium-term (weeks), or long-term (months)
6. Key Catalysts: What could drive the investment thesis
7. Major Risks: What could invalidate the thesis
8. Synthesis: How the bull/bear arguments influenced your final decision

Be specific and actionable. Consider both bull and bear perspectives in your recommendation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await safe_llm_invoke(llm, messages)
        investment_plan = response.content
        
        # Validate that we actually got a plan
        if not investment_plan or len(investment_plan) < 100:
            logger.error("❌ Investment plan generation failed - using fallback")
            investment_plan = f"""
INVESTMENT RECOMMENDATION: HOLD

Due to incomplete analysis, we recommend a HOLD position with the following considerations:
- Limited data availability prevents a strong directional recommendation
- Risk management suggests avoiding new positions without complete information
- Monitor for better data availability before making investment decisions

Position Sizing: 0% (no new position)
Risk Level: High (due to information uncertainty)
Time Horizon: Re-evaluate when more data is available
"""
        
        # Save to memory
        memory.save_memory(f"Investment plan generated after {executed_round} rounds: {investment_plan[:200]}...")
        
        # Update state with final plan
        logger.info("✅ Investment plan complete - proceeding to risk management")
        
        return {
            "investment_plan": investment_plan,
            "research_debate_state": debate_state
        }
    
    return research_manager_node