import asyncio
import json
from ..utils.connection_retry import safe_llm_invoke
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter
from ..utils.safe_state_access import create_safe_state_wrapper
from ..utils.news_filter import filter_news_for_llm


def create_neutral_debator(llm):
    async def neutral_node(state) -> dict:
        # 🚨 RUNTIME VERIFICATION: Confirm neutral debator version is running
        import logging
        logger = logging.getLogger(__name__)
        logger.critical("🔥🔥🔥 RUNTIME VERIFICATION: neutral_debator.py VERSION ACTIVE 🔥🔥🔥")
        logger.critical(f"🔥 TOKEN REDUCTION ENABLED: MAX_RISK_RESPONSE_TOKENS=2000 limit is ACTIVE")
        logger.critical(f"🔥 Code version timestamp: 2025-01-14 - Neutral with token limits")
        
        # CRITICAL FIX: Use safe state wrapper to prevent KeyError
        safe_state = create_safe_state_wrapper(state)
        
        # Safe access to risk_debate_state
        risk_debate_state = safe_state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

        # CRITICAL FIX: Safe access to all report fields using safe state wrapper
        market_research_report = safe_state.get("market_report", "")
        sentiment_report = safe_state.get("sentiment_report", "")
        news_report = safe_state.get("news_report", "")
        fundamentals_report = safe_state.get("fundamentals_report", "")

        # Apply token optimization to news report (balanced view, minimal articles)
        filtered_news = filter_news_for_llm(news_report, max_articles=8)

        trader_decision = safe_state.get("trader_investment_plan", "")

        prompt = f"""As the Neutral Risk Analyst, your role is to provide a balanced perspective, weighing both the potential benefits and risks of the trader's decision or plan. You prioritize a well-rounded approach, evaluating the upsides and downsides while factoring in broader market trends, potential economic shifts, and diversification strategies.Here is the trader's decision:

{trader_decision}

Your task is to challenge both the Risky and Safe Analysts, pointing out where each perspective may be overly optimistic or overly cautious. Use insights from the following data sources to support a moderate, sustainable strategy to adjust the trader's decision:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {filtered_news}
Company Fundamentals Report: {fundamentals_report}

Here is the current conversation history: {history}
Here is the last response from the risky analyst: {current_risky_response}
Here is the last response from the safe analyst: {current_safe_response}

Provide a balanced perspective that considers both risk and opportunity.
"""

        # Async LLM invocation with connection retry protection
        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(llm, messages)

        # CRITICAL: Apply token limiting to prevent massive debate responses
        raw_content = response.content
        MAX_RISK_RESPONSE_TOKENS = 2000  # ~500 words max for risk analysis
        MAX_RISK_RESPONSE_CHARS = MAX_RISK_RESPONSE_TOKENS * 4
        
        # 🚨 RUNTIME VERIFICATION: Log token limiting behavior
        logger.critical(f"🔥🔥🔥 NEUTRAL RISK TOKEN LIMIT VERIFICATION 🔥🔥🔥")
        logger.critical(f"🔥 Response length before truncation: {len(raw_content)} chars")
        logger.critical(f"🔥 MAX_RISK_RESPONSE_CHARS limit: {MAX_RISK_RESPONSE_CHARS}")
        
        if len(raw_content) > MAX_RISK_RESPONSE_CHARS:
            logger.critical(f"🔥 TRUNCATING NEUTRAL RESPONSE: {len(raw_content)} > {MAX_RISK_RESPONSE_CHARS}")
            from ..utils.minimalist_logging import minimalist_log
            minimalist_log("TOKEN_OPT", f"Neutral analyst truncating from {len(raw_content)} to {MAX_RISK_RESPONSE_CHARS} chars")
            # Keep first part of analysis
            truncated_content = raw_content[:MAX_RISK_RESPONSE_CHARS] + "\n\n[Analysis truncated for token optimization]"
            raw_content = truncated_content
            logger.critical(f"✅ Neutral response truncated to: {len(raw_content)} chars")
        else:
            logger.critical(f"✅ No truncation needed for neutral: {len(raw_content)} ≤ {MAX_RISK_RESPONSE_CHARS}")

        argument = f"Neutral Analyst: {raw_content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral Analyst",
            "current_risky_response": risk_debate_state.get("current_risky_response", ""),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state.get("count", 0) + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
