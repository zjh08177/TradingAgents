"""
Bear Researcher Node - Always parallel execution
Provides bearish investment perspective
"""
from langchain_core.messages import AIMessage
import asyncio
import json
import logging
import time
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)

def create_bear_researcher(llm, memory):
    async def bear_node(state) -> dict:
        # Get state data
        investment_debate_state = state.get("investment_debate_state", {"count": 0, "history": ""})
        market_research_report = state.get("market_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")

        # Get debate history context
        research_debate_state = state.get("research_debate_state", {})
        debate_history = research_debate_state.get("debate_history", [])
        current_round = research_debate_state.get("current_round", 1)
        judge_feedback = research_debate_state.get("judge_feedback", "")
        
        logger.info(f"🐻 BEAR RESEARCHER: Round {current_round}")
        start_time = time.time()

        # Get past memories
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Build debate context
        debate_context = ""
        if debate_history and current_round > 1:
            # Get the most recent bull argument from previous round
            last_round = debate_history[-1] if debate_history else {}
            previous_bull = last_round.get("bull", "")
            if previous_bull:
                debate_context += f"\n\n🐂 PREVIOUS BULL ARGUMENT TO ADDRESS:\n{previous_bull}"
            
            # Include judge feedback if available
            round_feedback = last_round.get("judge", "")
            if round_feedback and "NEXT ROUND FOCUS:" in round_feedback:
                # Extract specific focus areas from judge
                focus_start = round_feedback.find("NEXT ROUND FOCUS:")
                focus_end = round_feedback.find("\n", focus_start + 20)
                if focus_end == -1:
                    focus_areas = round_feedback[focus_start:]
                else:
                    focus_areas = round_feedback[focus_start:focus_end]
                debate_context += f"\n\n⚖️ JUDGE GUIDANCE:\n{focus_areas}"

        # Adjust prompt based on round
        round_instruction = ""
        if current_round == 1:
            round_instruction = "This is the opening round. Present your strongest bearish case."
        elif current_round == research_debate_state.get("max_rounds", 3):
            round_instruction = "This is the FINAL ROUND. Make your closing argument and address any remaining concerns."
        else:
            round_instruction = f"This is round {current_round}. Build on your previous arguments and address the bull's concerns."

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
        
        # Update state
        new_state = investment_debate_state.copy()
        new_state.update({
            "bear_history": result.content,
            "current_response": f"Bear: {result.content}",
            "count": investment_debate_state.get("count", 0) + 1
        })
        
        # Log completion time
        elapsed_time = time.time() - start_time
        logger.info(f"🐻✅ Bear argument completed in {elapsed_time:.1f}s")
        
        return {"investment_debate_state": new_state}

    return bear_node
