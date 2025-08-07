"""
Bear Researcher Node - Always parallel execution
Provides bearish investment perspective
"""
from langchain_core.messages import AIMessage
import asyncio
import json
import logging
import time
from ..utils.connection_retry import safe_llm_invoke
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter
from ..utils.safe_state_access import create_safe_state_wrapper
from ..prompts.enhanced_prompts_v4 import get_enhanced_prompt
from ..default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

def create_bear_researcher(llm, memory):
    async def bear_node(state) -> dict:
        # CRITICAL FIX: Use safe state wrapper to prevent KeyError
        safe_state = create_safe_state_wrapper(state)
        
        # Get state data using safe access
        investment_debate_state = safe_state.get("investment_debate_state", {"count": 0, "history": ""})
        market_research_report = safe_state.get("market_report", "")
        sentiment_report = safe_state.get("sentiment_report", "")
        news_report = safe_state.get("news_report", "")
        fundamentals_report = safe_state.get("fundamentals_report", "")

        # Get debate history context using safe access
        research_debate_state = safe_state.get("research_debate_state", {})
        debate_history = research_debate_state.get("debate_history", [])
        current_round = research_debate_state.get("current_round", 1)
        judge_feedback = research_debate_state.get("judge_feedback", "")
        
        logger.info(f"🐻 BEAR RESEARCHER: Round {current_round}")
        start_time = time.time()

        # Get past memories
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Build comprehensive debate context from ALL previous rounds
        debate_context = ""
        if debate_history and current_round > 1:
            # Build full debate history summary
            debate_context += "\n\n📚 COMPLETE DEBATE HISTORY:\n"
            for round_data in debate_history:
                round_num = round_data.get("round", "")
                debate_context += f"\n--- ROUND {round_num} ---\n"
                
                # Include bull's argument from this round
                bull_arg = round_data.get("bull", "")
                if bull_arg and bull_arg != "NO ARGUMENT":
                    # Truncate to key points if too long
                    if len(bull_arg) > 500:
                        bull_arg = bull_arg[:500] + "...[truncated]"
                    debate_context += f"🐂 BULL: {bull_arg}\n"
                
                # Include judge's feedback and score
                judge_feedback = round_data.get("judge", "")
                quality_score = round_data.get("quality_score", 0)
                if judge_feedback:
                    # Extract key judge points
                    if "Quality Score:" in judge_feedback:
                        score_line = [line for line in judge_feedback.split('\n') if "Quality Score:" in line]
                        if score_line:
                            debate_context += f"⚖️ JUDGE: {score_line[0]}\n"
                    if "Key areas of" in judge_feedback:
                        key_areas = judge_feedback[judge_feedback.find("Key areas of"):]
                        key_areas = key_areas.split('\n')[0]
                        debate_context += f"   {key_areas}\n"
                    
            # Get the most recent bull argument for direct response
            last_round = debate_history[-1] if debate_history else {}
            previous_bull = last_round.get("bull", "")
            if previous_bull and previous_bull != "NO ARGUMENT":
                debate_context += f"\n\n🐂 MOST RECENT BULL ARGUMENT (RESPOND DIRECTLY):\n{previous_bull}"
            
            # Include latest judge guidance
            round_feedback = last_round.get("judge", "")
            if round_feedback and "NEXT ROUND FOCUS:" in round_feedback:
                focus_start = round_feedback.find("NEXT ROUND FOCUS:")
                focus_end = round_feedback.find("\n", focus_start + 20)
                if focus_end == -1:
                    focus_areas = round_feedback[focus_start:]
                else:
                    focus_areas = round_feedback[focus_start:focus_end]
                debate_context += f"\n\n⚖️ JUDGE'S SPECIFIC REQUIREMENTS:\n{focus_areas}"

        # Get company ticker
        ticker = safe_state.get("company_of_interest", "")
        
        # Adjust prompt based on round
        round_instruction = ""
        if current_round == 1:
            round_instruction = "This is the opening round. Present your strongest bearish case."
        elif current_round == research_debate_state.get("max_rounds", 3):
            round_instruction = "This is the FINAL ROUND. Make your closing argument and address any remaining concerns."
        else:
            round_instruction = f"This is round {current_round}. Build on your previous arguments and address the bull's concerns."
        
        # Use enhanced V4 prompt if enabled
        if DEFAULT_CONFIG.get("enhanced_prompts_enabled", True):
            enhanced_prompt = get_enhanced_prompt("bear", ticker)
            if enhanced_prompt:
                # Add research data to enhanced prompt
                prompt = f"""{enhanced_prompt}

ROUND {current_round} CONTEXT:
{round_instruction}

RESEARCH DATA:
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}
- Past Lessons: {past_memory_str}
{debate_context}"""
            else:
                # Fallback to original prompt
                prompt = f"""As the Bear Researcher, provide a compelling bearish case highlighting:
- Risk factors and potential threats
- Negative market trends and headwinds
- Concerning fundamentals or competitive disadvantages
- Pessimistic sentiment or market vulnerabilities

{round_instruction}

Research Data:
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}
- Past Lessons: {past_memory_str}
{debate_context}

Present your bearish perspective with careful analysis and risk-focused reasoning. If this is not the first round, make sure to address the bull's concerns and strengthen your position."""
        else:
            # Original prompt
            prompt = f"""As the Bear Researcher, provide a compelling bearish case highlighting:
- Risk factors and potential threats
- Negative market trends and headwinds
- Concerning fundamentals or competitive disadvantages
- Pessimistic sentiment or market vulnerabilities

{round_instruction}

Research Data:
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}
- Past Lessons: {past_memory_str}
{debate_context}

Present your bearish perspective with careful analysis and risk-focused reasoning. If this is not the first round, make sure to address the bull's concerns and strengthen your position."""

        messages = [{"role": "user", "content": prompt}]
        # CE2: Use safe_llm_invoke to handle connection errors
        result = await safe_llm_invoke(llm, messages)
        
        # Update state - APPEND to history instead of overwriting
        existing_history = investment_debate_state.get("bear_history", "")
        new_history = f"{existing_history}\n{result.content}" if existing_history else result.content
        
        new_state = investment_debate_state.copy()
        new_state.update({
            "bear_history": new_history,
            "current_response": f"Bear: {result.content}",
            "count": investment_debate_state.get("count", 0) + 1
        })
        
        # Log completion time
        elapsed_time = time.time() - start_time
        logger.info(f"🐻✅ Bear argument completed in {elapsed_time:.1f}s")
        
        return {"investment_debate_state": new_state}

    return bear_node
