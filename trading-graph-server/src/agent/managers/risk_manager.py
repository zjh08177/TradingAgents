import asyncio
import json
import logging

logger = logging.getLogger(__name__)

def create_risk_manager(llm, memory):
    async def risk_manager_node(state) -> dict:
        logger.info("🎯 Risk Manager: Starting final decision process")
        
        # Extract information (simplified - no validation needed)
        company_name = state.get("company_of_interest", "")
        risk_debate_state = state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        
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
        response = await llm.ainvoke(messages)
        
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
        }

    return risk_manager_node
