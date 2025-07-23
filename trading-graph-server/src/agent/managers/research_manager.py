import asyncio
import json
import logging

logger = logging.getLogger(__name__)

def create_research_manager(llm, memory):
    async def research_manager_node(state) -> dict:
        # Get all analyst reports
        market_research_report = state.get("market_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")
        sentiment_report = state.get("sentiment_report", "")
        
        # Combine reports
        combined_reports = f"""
        Market Analysis: {market_research_report}
        
        News Analysis: {news_report}
        
        Fundamentals Analysis: {fundamentals_report}
        
        Sentiment Analysis: {sentiment_report}
        """
        
        # Generate investment plan
        prompt = f"""
        Based on the comprehensive analysis provided, create a detailed investment plan.
        
        Analysis Reports:
        {combined_reports}
        
        Provide a clear investment recommendation with key supporting points.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await llm.ainvoke(messages)
        
        investment_plan = response.content if hasattr(response, 'content') else str(response)
        
        # Save to memory
        memory.save_memory(f"Investment plan generated: {investment_plan[:200]}...")
        
        return {
            "investment_plan": investment_plan
        }
    
    return research_manager_node
