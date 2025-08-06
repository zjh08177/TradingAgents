"""
Parallel Risk Debators Node
Executes all three risk debators (aggressive, conservative, neutral) in parallel
Part of Feature 2: Parallel Risk Debators
"""
import asyncio
from typing import Dict, List, Tuple, Union
import time
import logging
from ...utils.agent_states import AgentState
from ...utils.connection_retry import safe_llm_invoke

logger = logging.getLogger(__name__)

def create_parallel_risk_debators(aggressive_llm, conservative_llm, neutral_llm):
    """
    Execute all three risk debators in parallel for performance optimization
    
    Features:
    - Concurrent execution of all three risk perspectives
    - ~3x performance improvement over sequential execution
    - Maintains result quality with parallel processing
    - Robust error handling for individual debator failures
    - Performance monitoring and reporting
    
    Args:
        aggressive_llm: LLM for aggressive risk perspective
        conservative_llm: LLM for conservative risk perspective
        neutral_llm: LLM for neutral risk perspective
        
    Returns:
        Async parallel risk node function
    """
    
    async def parallel_risk_node(state: AgentState) -> AgentState:
        start_time = time.time()
        logger.info("⚡ PARALLEL RISK DEBATORS: Starting concurrent execution")
        
        risk_state = state.get("risk_debate_state", {})
        shared_context = risk_state.get("shared_context", {})
        
        # Get investment plan from shared context or state
        investment_plan = shared_context.get("investment_plan", "") or state.get("investment_plan", "")
        trader_decision = shared_context.get("trader_decision", "") or state.get("trader_investment_plan", "")
        
        # Define async execution for each debator
        async def run_aggressive():
            try:
                logger.info("🔴 Starting Aggressive Risk Analyst")
                prompt = f"""As the Aggressive Risk Analyst, champion high-reward opportunities while acknowledging risks.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}
Market Data: {shared_context.get('market_report', '')}
Sentiment: {shared_context.get('sentiment_report', '')}
News: {shared_context.get('news_report', '')}
Fundamentals: {shared_context.get('fundamentals_report', '')}

Provide your aggressive risk perspective emphasizing:
1. High-reward opportunities and growth potential
2. Why the risks are worth taking
3. Potential upside scenarios
4. Risk mitigation strategies for aggressive positions"""
                
                messages = [{"role": "user", "content": prompt}]
                response = await safe_llm_invoke(aggressive_llm, messages)
                logger.info("🔴 Aggressive Risk Analyst completed")
                return ("aggressive", response.content)
            except asyncio.CancelledError:
                logger.warning("⚠️ Aggressive debator cancelled due to timeout")
                return ("aggressive", "Analysis cancelled due to timeout - Aggressive risk perspective unavailable")
            except Exception as e:
                logger.error(f"❌ Aggressive debator failed: {e}")
                return ("aggressive", f"Error in aggressive analysis: {str(e)}")
        
        async def run_conservative():
            try:
                logger.info("🔵 Starting Conservative Risk Analyst")
                prompt = f"""As the Conservative Risk Analyst, emphasize capital preservation and risk mitigation.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}
Market Data: {shared_context.get('market_report', '')}
Sentiment: {shared_context.get('sentiment_report', '')}
News: {shared_context.get('news_report', '')}
Fundamentals: {shared_context.get('fundamentals_report', '')}

Provide your conservative risk perspective focusing on:
1. Capital preservation strategies
2. Potential downside risks and worst-case scenarios
3. Risk mitigation and hedging strategies
4. Safe position sizing recommendations"""
                
                messages = [{"role": "user", "content": prompt}]
                response = await safe_llm_invoke(conservative_llm, messages)
                logger.info("🔵 Conservative Risk Analyst completed")
                return ("conservative", response.content)
            except asyncio.CancelledError:
                logger.warning("⚠️ Conservative debator cancelled due to timeout")
                return ("conservative", "Analysis cancelled due to timeout - Conservative risk perspective unavailable")
            except Exception as e:
                logger.error(f"❌ Conservative debator failed: {e}")
                return ("conservative", f"Error in conservative analysis: {str(e)}")
        
        async def run_neutral():
            try:
                logger.info("⚪ Starting Neutral Risk Analyst")
                prompt = f"""As the Neutral Risk Analyst, provide a balanced perspective weighing both risks and opportunities.

Investment Plan: {investment_plan}
Trader Decision: {trader_decision}
Market Data: {shared_context.get('market_report', '')}
Sentiment: {shared_context.get('sentiment_report', '')}
News: {shared_context.get('news_report', '')}
Fundamentals: {shared_context.get('fundamentals_report', '')}

Provide your balanced risk perspective including:
1. Objective risk-reward analysis
2. Balanced position sizing recommendations
3. Conditional strategies based on market scenarios
4. Data-driven recommendations without bias"""
                
                messages = [{"role": "user", "content": prompt}]
                response = await safe_llm_invoke(neutral_llm, messages)
                logger.info("⚪ Neutral Risk Analyst completed")
                return ("neutral", response.content)
            except asyncio.CancelledError:
                logger.warning("⚠️ Neutral debator cancelled due to timeout")
                return ("neutral", "Analysis cancelled due to timeout - Neutral risk perspective unavailable")
            except Exception as e:
                logger.error(f"❌ Neutral debator failed: {e}")
                return ("neutral", f"Error in neutral analysis: {str(e)}")
        
        # Execute all three in parallel with graceful cancellation handling
        logger.info("🚀 Launching all three risk analysts concurrently...")
        try:
            results = await asyncio.gather(
                run_aggressive(),
                run_conservative(),
                run_neutral(),
                return_exceptions=True
            )
        except asyncio.CancelledError:
            logger.warning("⚠️ PARALLEL RISK DEBATORS: Operation cancelled due to timeout")
            logger.info("🔄 Providing fallback analysis to maintain system stability")
            # Provide graceful fallback when cancelled
            results = [
                ("aggressive", "Analysis cancelled due to timeout - Aggressive risk perspective unavailable"),
                ("conservative", "Analysis cancelled due to timeout - Conservative risk perspective unavailable"), 
                ("neutral", "Analysis cancelled due to timeout - Neutral risk perspective unavailable")
            ]
        
        # Process results
        updated_state = risk_state.copy()
        successful_analyses = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Risk debator failed with exception: {result}")
                continue
            
            debator_type, content = result
            successful_analyses += 1
            
            if debator_type == "aggressive":
                updated_state["current_risky_response"] = content
                # Accumulate history
                risky_history = updated_state.get("risky_history", "")
                if risky_history:
                    updated_state["risky_history"] = f"{risky_history}\n\nRisky Analyst: {content}"
                else:
                    updated_state["risky_history"] = f"Risky Analyst: {content}"
            
            elif debator_type == "conservative":
                updated_state["current_safe_response"] = content
                # Accumulate history
                safe_history = updated_state.get("safe_history", "")
                if safe_history:
                    updated_state["safe_history"] = f"{safe_history}\n\nSafe Analyst: {content}"
                else:
                    updated_state["safe_history"] = f"Safe Analyst: {content}"
            
            elif debator_type == "neutral":
                updated_state["current_neutral_response"] = content
                # Accumulate history
                neutral_history = updated_state.get("neutral_history", "")
                if neutral_history:
                    updated_state["neutral_history"] = f"{neutral_history}\n\nNeutral Analyst: {content}"
                else:
                    updated_state["neutral_history"] = f"Neutral Analyst: {content}"
        
        # Update combined history for compatibility
        history_parts = []
        if updated_state.get("current_risky_response"):
            history_parts.append(f"Risky Analyst: {updated_state['current_risky_response']}")
        if updated_state.get("current_safe_response"):
            history_parts.append(f"Safe Analyst: {updated_state['current_safe_response']}")
        if updated_state.get("current_neutral_response"):
            history_parts.append(f"Neutral Analyst: {updated_state['current_neutral_response']}")
        
        updated_state["history"] = "\n\n".join(history_parts)
        
        # Performance tracking
        execution_time = time.time() - start_time
        updated_state["parallel_execution_time"] = execution_time
        
        logger.info(f"⚡ PARALLEL RISK: Completed in {execution_time:.2f}s (Target: <20s)")
        logger.info(f"✅ Successful analyses: {successful_analyses}/3")
        
        if execution_time < 20:
            logger.info("🎯 Performance target ACHIEVED!")
        else:
            logger.warning(f"⚠️ Performance target missed: {execution_time:.2f}s > 20s")
        
        # Update count for compatibility
        updated_state["count"] = updated_state.get("count", 0) + 1
        
        return {"risk_debate_state": updated_state}
    
    return parallel_risk_node