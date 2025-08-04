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
        max_rounds = config.get("max_debate_rounds", 3)  # Configurable max rounds
        
        # CRITICAL FIX: Check circuit breaker
        force_consensus = circuit_breaker.check_loop(trace_id)
        
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
            logger.info(f"⚖️ Evaluating debate quality (Round {current_round})")
            
            # Create judge prompt
            judge_prompt = f"""
As an impartial judge, evaluate the investment debate between the bull and bear analysts.

BULL ARGUMENT:
{bull_argument if bull_ready else "NO ARGUMENT PROVIDED"}

BEAR ARGUMENT:
{bear_argument if bear_ready else "NO ARGUMENT PROVIDED"}

Evaluate the debate on:
1. Quality of arguments (evidence, logic, specificity)
2. Whether both sides have presented comprehensive cases
3. If there's any convergence or agreement on key points

Provide your assessment including:
- Quality Score: X/10
- Whether consensus or convergence has been reached
- Key areas of agreement/disagreement
- Recommendation on whether to continue debate or proceed with investment planning

Be specific about whether the analysts have reached sufficient agreement or if their positions are well-developed enough to proceed.
"""
            
            messages = [{"role": "user", "content": judge_prompt}]
            response = await safe_llm_invoke(llm, messages)
            
            judge_content = response.content
            judge_feedback = judge_content
            
            # CRITICAL FIX: Flexible consensus detection
            content_lower = judge_content.lower()
            
            # Look for various consensus indicators
            consensus_indicators = [
                "consensus reached",
                "agreement found", 
                "both perspectives align",
                "converged on",
                "unanimous",
                "agreed",
                "sufficient agreement",
                "ready to proceed",
                "well-developed arguments",
                "comprehensive cases presented"
            ]
            
            consensus_reached = any(indicator in content_lower for indicator in consensus_indicators)
            
            # Also check for explicit "no consensus" indicators
            no_consensus_indicators = [
                "no consensus",
                "strongly disagree",
                "fundamental disagreement",
                "continue debate",
                "more discussion needed"
            ]
            
            if any(indicator in content_lower for indicator in no_consensus_indicators):
                consensus_reached = False
            
            # Extract quality score if present
            if "quality score:" in content_lower:
                try:
                    score_text = content_lower.split("quality score:")[1].split("\n")[0].strip()
                    # Extract number from text like "8/10" or "8"
                    import re
                    score_match = re.search(r'(\d+)', score_text)
                    if score_match:
                        quality_score = int(score_match.group(1))
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract quality score: {e}")
                    pass
            
            # CRITICAL FIX: Force consensus after quality debates
            force_consensus_threshold = config.get("force_consensus_threshold", 7)
            if current_round >= 2 and quality_score >= force_consensus_threshold:
                logger.info(f"🎯 Forcing consensus: Round {current_round}, Quality {quality_score}/10")
                consensus_reached = True
            
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
        
        # CRITICAL FIX: ALWAYS end debate if max rounds reached
        if current_round >= max_rounds:
            logger.warning(f"🔚 MAX ROUNDS REACHED: Ending debate at round {current_round}/{max_rounds}")
            consensus_reached = True  # Force end regardless of consensus
        elif force_consensus:
            logger.warning(f"⚠️ Circuit breaker triggered: Forcing consensus after {current_round} rounds")
            consensus_reached = True
        
        # Decide next action - ALWAYS end if max rounds reached
        if consensus_reached or current_round >= max_rounds:
            # Proceed to generate investment plan
            logger.info("📊 Generating final investment plan...")
            
            # Reset circuit breaker for this trace
            circuit_breaker.reset(trace_id)
            
            # CRITICAL FIX: Get all analyst reports using safe state access
            market_research_report = safe_state.get("market_report", "")
            news_report = safe_state.get("news_report", "")
            fundamentals_report = safe_state.get("fundamentals_report", "")
            sentiment_report = safe_state.get("sentiment_report", "")
            
            # Check if we have low quality reports and log warnings
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
            
            # CRITICAL FIX: Create investment plan prompt with direct formatting to prevent KeyError
            system_prompt = """You are a senior investment strategist creating a final investment recommendation.
You must synthesize all available information into a clear, actionable investment plan.

Even if some analyst reports are missing or incomplete, use the available information to make the best recommendation possible."""

            # Format user prompt directly with safe variables to prevent state access issues
            consensus_text = 'Yes' if consensus_reached else 'No (max rounds reached)'
            bull_text = bull_argument if bull_ready else "No argument provided"
            bear_text = bear_argument if bear_ready else "No argument provided"
            
            user_prompt = f"""Based on all the analysis and debate, create a comprehensive investment plan.

ANALYST REPORTS:
Market Analysis: {market_research_report}
News Analysis: {news_report}
Fundamentals Analysis: {fundamentals_report}
Sentiment Analysis: {sentiment_report}

DEBATE OUTCOME:
===============
Total Rounds: {current_round}
Final Quality Score: {quality_score}/10
Consensus Reached: {consensus_text}

BULL POSITION:
{bull_text}

BEAR POSITION:
{bear_text}

JUDGE'S FINAL ASSESSMENT:
{judge_feedback}

Create a detailed investment plan that includes:
1. Investment Recommendation: BUY/SELL/HOLD with confidence level
2. Position Sizing: Recommended allocation percentage
3. Entry Strategy: Specific price levels or conditions
4. Risk Management: Stop loss levels and risk mitigation
5. Time Horizon: Short-term (days), medium-term (weeks), or long-term (months)
6. Key Catalysts: What could drive the investment thesis
7. Major Risks: What could invalidate the thesis

Be specific and actionable. If data is limited, clearly state assumptions and increase caution in recommendations."""
            
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
            memory.save_memory(f"Investment plan generated after {current_round} rounds: {investment_plan[:200]}...")
            
            # Update state with final plan
            logger.info("✅ Investment plan complete - proceeding to risk management")
            
            return {
                "investment_plan": investment_plan,
                "research_debate_state": debate_state
            }
        else:
            # Should never reach here after our fix, but add safety
            logger.error(f"❌ CRITICAL ERROR: Reached else branch after max rounds fix!")
            logger.error(f"❌ Current round: {current_round}, Max rounds: {max_rounds}")
            logger.error(f"❌ Consensus: {consensus_reached}, Force consensus: {force_consensus}")
            
            # Force end the debate to prevent infinite loop
            logger.warning(f"🔚 SAFETY: Force ending debate and generating investment plan")
            
            investment_plan = f"""
EMERGENCY INVESTMENT RECOMMENDATION: HOLD

Due to debate termination at round {current_round}, we recommend a HOLD position:
- Debate exceeded maximum rounds without clear consensus
- Risk management suggests avoiding new positions without clear direction
- Re-evaluate when better information becomes available

Position Sizing: 0% (no new position)
Risk Level: High (due to unclear signals)
Time Horizon: Re-evaluate next trading session
"""
            
            return {
                "investment_plan": investment_plan,
                "research_debate_state": debate_state
            }
    
    return research_manager_node