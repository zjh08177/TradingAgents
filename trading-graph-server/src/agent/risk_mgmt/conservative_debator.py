from langchain_core.messages import AIMessage
import asyncio
import json
from ..utils.connection_retry import safe_llm_invoke
from ..utils.agent_prompt_enhancer import enhance_agent_prompt
from ..utils.prompt_compressor import get_prompt_compressor, compress_prompt
from ..utils.token_limiter import get_token_limiter
from ..utils.safe_state_access import create_safe_state_wrapper
from ..utils.news_filter import filter_news_for_llm


def create_safe_debator(llm):
    async def safe_node(state) -> dict:
        # 🚨 RUNTIME VERIFICATION: Confirm conservative debator version is running
        import logging
        logger = logging.getLogger(__name__)
        logger.critical("🔥🔥🔥 RUNTIME VERIFICATION: conservative_debator.py VERSION ACTIVE 🔥🔥🔥")
        logger.critical(f"🔥 TOKEN REDUCTION ENABLED: MAX_RISK_RESPONSE_TOKENS=2000 limit is ACTIVE")
        logger.critical(f"🔥 Code version timestamp: 2025-01-14 - Conservative with token limits")
        
        # CRITICAL FIX: Use safe state wrapper to prevent KeyError
        safe_state = create_safe_state_wrapper(state)
        
        # Safe access to risk_debate_state
        risk_debate_state = safe_state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        # CRITICAL FIX: Safe access to all report fields using safe state wrapper
        market_research_report = safe_state.get("market_report", "")
        sentiment_report = safe_state.get("sentiment_report", "")
        news_report = safe_state.get("news_report", "")
        fundamentals_report = safe_state.get("fundamentals_report", "")

        # Apply token optimization to news report (conservative risk focus)
        filtered_news = filter_news_for_llm(news_report, max_articles=10)

        trader_decision = safe_state.get("trader_investment_plan", "")

        prompt = f"""As the Safe/Conservative Risk Analyst, your primary objective is to protect assets, minimize volatility, and ensure steady, reliable growth. You prioritize stability, security, and risk mitigation, carefully assessing potential losses, economic downturns, and market volatility. When evaluating the trader's decision or plan, critically examine high-risk elements, pointing out where the decision may expose the firm to undue risk and where more cautious alternatives could secure long-term gains. Here is the trader's decision:

{trader_decision}

Your task is to actively counter the arguments of the Risky and Neutral Analysts, highlighting where their views may overlook potential threats or fail to prioritize sustainability. Respond directly to their points, drawing from the following data sources to build a convincing case for a low-risk approach adjustment to the trader's decision:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {filtered_news}
Company Fundamentals Report: {fundamentals_report}

Here is the current conversation history: {history}
Here is the last response from the risky analyst: {current_risky_response}
Here is the last response from the neutral analyst: {current_neutral_response}

Provide a conservative perspective that emphasizes risk mitigation and stability.
"""

        # Async LLM invocation with connection retry protection
        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(llm, messages)

        # CRITICAL: Apply token limiting to prevent massive debate responses
        raw_content = response.content
        MAX_RISK_RESPONSE_TOKENS = 2000  # ~500 words max for risk analysis
        MAX_RISK_RESPONSE_CHARS = MAX_RISK_RESPONSE_TOKENS * 4
        
        # 🚨 RUNTIME VERIFICATION: Log token limiting behavior
        logger.critical(f"🔥🔥🔥 CONSERVATIVE RISK TOKEN LIMIT VERIFICATION 🔥🔥🔥")
        logger.critical(f"🔥 Response length before truncation: {len(raw_content)} chars")
        logger.critical(f"🔥 MAX_RISK_RESPONSE_CHARS limit: {MAX_RISK_RESPONSE_CHARS}")
        
        if len(raw_content) > MAX_RISK_RESPONSE_CHARS:
            logger.critical(f"🔥 TRUNCATING CONSERVATIVE RESPONSE: {len(raw_content)} > {MAX_RISK_RESPONSE_CHARS}")
            from ..utils.minimalist_logging import minimalist_log
            minimalist_log("TOKEN_OPT", f"Conservative analyst truncating from {len(raw_content)} to {MAX_RISK_RESPONSE_CHARS} chars")
            # Keep first part of analysis
            truncated_content = raw_content[:MAX_RISK_RESPONSE_CHARS] + "\n\n[Analysis truncated for token optimization]"
            raw_content = truncated_content
            logger.critical(f"✅ Conservative response truncated to: {len(raw_content)} chars")
        else:
            logger.critical(f"✅ No truncation needed for conservative: {len(raw_content)} ≤ {MAX_RISK_RESPONSE_CHARS}")

        argument = f"Safe Analyst: {raw_content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe Analyst",
            "current_risky_response": risk_debate_state.get("current_risky_response", ""),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state.get("count", 0) + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
