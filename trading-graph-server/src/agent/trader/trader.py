import asyncio
import json
import logging
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.token_limiter import get_token_limiter

logger = logging.getLogger(__name__)

def create_trader(llm, memory):
    async def trader_node(state) -> dict:
        # Get required information
        company_name = state.get("company_of_interest", "")
        investment_plan = state.get("investment_plan", "")
        risk_assessment = state.get("risk_debate_state", {}).get("judge_decision", "")
        
        # Generate final trading decision
        prompt = f"""
        You are a professional trader. Based on the investment plan and risk assessment, 
        make a final trading decision for {company_name}.
        
        Investment Plan: {investment_plan}
        Risk Assessment: {risk_assessment}
        
        Provide a clear decision: BUY, SELL, or HOLD with brief reasoning.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await safe_llm_invoke(llm, messages)
        
        final_decision = response.content if hasattr(response, 'content') else str(response)
        
        # Save to memory
        memory.save_memory(f"Trading decision for {company_name}: {final_decision[:100]}...")
        
        return {
            "final_trade_decision": final_decision,
            "trader_investment_plan": investment_plan
        }
    
    return trader_node
