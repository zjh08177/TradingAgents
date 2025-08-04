import asyncio
import json
from ..utils.connection_retry import safe_llm_invoke
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter
from ..utils.safe_state_access import create_safe_state_wrapper


def create_risky_debator(llm):
    async def risky_node(state) -> dict:
        # CRITICAL FIX: Use safe state wrapper to prevent KeyError
        safe_state = create_safe_state_wrapper(state)
        
        # Safe access to risk_debate_state
        risk_debate_state = safe_state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        # CRITICAL FIX: Safe access to all report fields using safe state wrapper
        market_research_report = safe_state.get("market_report", "")
        sentiment_report = safe_state.get("sentiment_report", "")
        news_report = safe_state.get("news_report", "")
        fundamentals_report = safe_state.get("fundamentals_report", "")

        trader_decision = safe_state.get("trader_investment_plan", "")

        prompt = f"""As the Risky Risk Analyst, your role is to actively champion high-reward, high-risk opportunities, emphasizing bold strategies and competitive advantages. When evaluating the trader's decision or plan, focus intently on the potential upside, growth potential, and innovative benefits—even when these come with elevated risk. Use the provided market data and sentiment analysis to strengthen your arguments and challenge the opposing views. Specifically, respond directly to each point made by the conservative and neutral analysts, countering with data-driven rebuttals and persuasive reasoning. Highlight where their caution might miss critical opportunities or where their assumptions may be overly conservative. Here is the trader's decision:

{trader_decision}

Your task is to create a compelling case for the trader's decision by questioning and critiquing the conservative and neutral stances to demonstrate why your high-reward perspective offers the best path forward. Incorporate insights from the following sources into your arguments:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}

Here is the current conversation history: {history}
Here is the last response from the safe analyst: {current_safe_response}
Here is the last response from the neutral analyst: {current_neutral_response}

Provide a compelling high-risk, high-reward perspective that challenges their conservative approaches.
"""

        # Async LLM invocation with connection retry protection
        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(llm, messages)

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky Analyst",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state.get("count", 0) + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
