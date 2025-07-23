from langchain_core.messages import AIMessage
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

def create_bear_researcher(llm, memory):
    async def bear_node(state) -> dict:
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

        prompt = f"""As the Bear Researcher, provide a compelling bearish case highlighting:
- Risk factors and potential threats
- Negative market trends and headwinds
- Concerning fundamentals or competitive disadvantages
- Pessimistic sentiment or market vulnerabilities

Research Data:
- Market Report: {market_research_report}
- Sentiment Report: {sentiment_report}
- News Report: {news_report}
- Fundamentals Report: {fundamentals_report}
- Past Lessons: {past_memory_str}

Present your bearish perspective with careful analysis and risk-focused reasoning."""

        messages = [{"role": "user", "content": prompt}]
        result = await llm.ainvoke(messages)
        
        # Update state
        new_state = investment_debate_state.copy()
        new_state.update({
            "bear_history": result.content,
            "current_response": f"Bear: {result.content}",
            "count": investment_debate_state.get("count", 0) + 1
        })
        
        return {"investment_debate_state": new_state}

    return bear_node
