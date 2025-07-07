import time
import json
import logging

logger = logging.getLogger(__name__)

def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:
        logger.info("🎯 Risk Manager: Starting final decision process")
        
        # Extract basic information
        company_name = state["company_of_interest"]
        
        # Get risk debate state
        risk_debate_state = state.get("risk_debate_state", {})
        history = risk_debate_state.get("history", "")
        
        # Extract all reports with validation
        market_research_report = state.get("market_report", "")
        news_report = state.get("news_report", "")
        fundamentals_report = state.get("fundamentals_report", "")  # FIX: was incorrectly assigned to news_report
        sentiment_report = state.get("sentiment_report", "")
        trader_plan = state.get("investment_plan", "")
        
        # Validate required data
        logger.info("🎯 Risk Manager: Validating input data...")
        logger.info(f"🎯 Risk Manager: market_report length: {len(market_research_report)}")
        logger.info(f"🎯 Risk Manager: news_report length: {len(news_report)}")
        logger.info(f"🎯 Risk Manager: fundamentals_report length: {len(fundamentals_report)}")
        logger.info(f"🎯 Risk Manager: sentiment_report length: {len(sentiment_report)}")
        logger.info(f"🎯 Risk Manager: investment_plan length: {len(trader_plan)}")
        logger.info(f"🎯 Risk Manager: risk_debate_history length: {len(history)}")
        
        missing_data = []
        
        if not market_research_report:
            missing_data.append("market_report")
        if not news_report:
            missing_data.append("news_report")
        if not fundamentals_report:
            missing_data.append("fundamentals_report")
        if not sentiment_report:
            missing_data.append("sentiment_report")
        if not trader_plan:
            missing_data.append("investment_plan")
        if not history:
            missing_data.append("risk_analyst_debate")
            
        if missing_data:
            logger.warning(f"🎯 Risk Manager: Missing data: {missing_data}")
            # Create a fallback response
            fallback_response = f"""**Risk Management Decision: HOLD**

**Reason**: Insufficient data available for comprehensive risk analysis.

**Missing Information**: {', '.join(missing_data)}

**Recommendation**: Wait for complete analysis before making investment decisions. The following data is required:
- Market analysis and technical indicators
- News and world events impact
- Company fundamentals assessment  
- Social sentiment analysis
- Risk team debate and perspectives

**Action**: Hold current position until all required analysis is complete."""
            
            logger.info("🎯 Risk Manager: Generated fallback decision due to missing data")
            
            new_risk_debate_state = risk_debate_state.copy()
            new_risk_debate_state.update({
                "judge_decision": fallback_response,
                "latest_speaker": "Judge",
                "count": risk_debate_state.get("count", 0) + 1
            })
            
            return {
                "risk_debate_state": new_risk_debate_state,
                "final_trade_decision": fallback_response,
            }
        
        # All data is present, proceed with normal analysis
        logger.info("🎯 Risk Manager: All required data present, proceeding with analysis")
        
        # Prepare current situation summary
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        
        # Get past memories
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
        
        # Original simple prompt
        prompt = f"""You are a risk management judge. You need to evaluate the debate between three risk analysts (Risky, Neutral, Safe/Conservative) and decide on the best course of action for the trader.

Company: {company_name}

Trader's original plan: {trader_plan}

Risk analysts debate:
{history}

Market research report: {market_research_report}

News report: {news_report}

Fundamentals report: {fundamentals_report}

Sentiment report: {sentiment_report}

Past lessons learned:
{past_memory_str}

Based on the above information, make a final decision on whether to BUY, SELL, or HOLD the stock. Provide detailed reasoning for your decision."""

        logger.info("🎯 Risk Manager: Invoking LLM for final decision...")
        logger.info(f"🎯 Risk Manager: Prompt length: {len(prompt)} chars")
        logger.info(f"🎯 Risk Manager: Prompt preview: {prompt[:500]}...")
        logger.info(f"🎯 Risk Manager: Full prompt sections:")
        logger.info(f"🎯 Risk Manager: - Company: {company_name}")
        logger.info(f"🎯 Risk Manager: - Trader plan preview: {trader_plan[:100]}...")
        logger.info(f"🎯 Risk Manager: - Risk debate preview: {history[:100]}...")
        logger.info(f"🎯 Risk Manager: - Market report preview: {market_research_report[:100]}...")
        logger.info(f"🎯 Risk Manager: - News report preview: {news_report[:100]}...")
        logger.info(f"🎯 Risk Manager: - Fundamentals report preview: {fundamentals_report[:100]}...")
        logger.info(f"🎯 Risk Manager: - Sentiment report preview: {sentiment_report[:100]}...")
        response = llm.invoke(prompt)
        logger.info(f"🎯 Risk Manager: Decision received ({len(response.content)} chars)")
        logger.info(f"🎯 Risk Manager: Decision preview: {response.content[:200]}...")

        # Update risk debate state
        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state.get("history", ""),
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state.get("current_risky_response", ""),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "count": risk_debate_state.get("count", 0) + 1,
        }
        
        logger.info("🎯 Risk Manager: Final decision complete")
        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
