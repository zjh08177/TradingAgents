import asyncio
import json
import logging
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)

def create_risk_manager(llm, memory):
    async def risk_manager_node(state) -> dict:
        logger.info("🎯 Risk Manager: Evaluating risk analysis needs")
        
        # Extract information (simplified - no validation needed)
        company_name = state.get("company_of_interest", "")
        risk_debate_state = state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        
        # Check if we need risk analysis or already have it
        risk_analysis_needed = state.get("risk_analysis_needed", True)
        has_risk_analysis = len(history) > 100  # Check if we have substantial risk analysis
        
        if risk_analysis_needed and not has_risk_analysis:
            # First pass - we need risk analysis
            logger.info("🔍 Risk Manager: Risk analysis needed - routing to risk debate")
            return {
                "risk_analysis_needed": True
            }
        
        # We have risk analysis - make final decision
        logger.info("🎯 Risk Manager: Making final decision with risk analysis")
        
        # Get all reports
        market_research_report = state.get("market_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        sentiment_report = state.get("sentiment_report", "")
        trader_plan = state.get("trader_investment_plan", "") or state.get("investment_plan", "")
        
        # Prepare analysis
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        prompt = f"""As the Risk Manager, make a final trading decision for {company_name}.

**Research Reports:**
- Market Research: {market_research_report}
- Sentiment Analysis: {sentiment_report}
- News Analysis: {news_report}
- Fundamentals Analysis: {fundamentals_report}

**Trader's Recommendation:** {trader_plan}
**Risk Analysis Debate:** {history}
**Past Lessons:** {past_memory_str}

**Instructions:**
- Provide a clear decision: BUY, SELL, or HOLD
- Explain your reasoning
- End with: "**FINAL DECISION: [BUY/SELL/HOLD]**"

Make your decision now:"""

        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(llm, messages)
        
        logger.info(f"🎯 Risk Manager: Decision: {response.content[:100]}...")
        
        # Update state
        new_risk_debate_state = risk_debate_state.copy()
        new_risk_debate_state.update({
            "judge_decision": response.content,
            "latest_speaker": "Risk Manager",
            "count": risk_debate_state.get("count", 0) + 1
        })
        
        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
            "risk_analysis_needed": False  # Mark as complete
        }

    return risk_manager_node
