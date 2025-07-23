from langchain_core.messages import AIMessage
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

def create_bull_researcher(llm, memory):
    async def bull_node(state) -> dict:
        # Get state data
        investment_debate_state = state.get("investment_debate_state", {"count": 0, "history": ""})
        market_research_report = state.get("market_report", "")
        sentiment_report = state.get("sentiment_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")

        # Get past memories
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        prompt = f"""As the Bull Researcher, provide a strong bullish case highlighting:
- Growth opportunities and potential catalysts
- Positive market trends and momentum
- Favorable fundamentals and competitive advantages
- Optimistic sentiment and market positioning

Research Data:
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}
- Past Lessons: {past_memory_str}

Present your bullish perspective with conviction and data-driven reasoning."""

        messages = [{"role": "user", "content": prompt}]
        result = await llm.ainvoke(messages)
        
        # Update state
        new_state = investment_debate_state.copy()
        new_state.update({
            "bull_history": result.content,
            "current_response": f"Bull: {result.content}",
            "count": investment_debate_state.get("count", 0) + 1
        })
        
        return {"investment_debate_state": new_state}

    return bull_node
