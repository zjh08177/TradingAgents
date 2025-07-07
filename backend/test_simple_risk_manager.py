#!/usr/bin/env python3

import sys
import os
import time
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.managers.risk_manager import create_risk_manager
from tradingagents.agents.utils.memory import FinancialSituationMemory
from langchain_openai import ChatOpenAI
from tradingagents.default_config import DEFAULT_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_risk_manager_directly():
    """Test the risk manager node directly with mock data."""
    print("🎯 Testing Risk Manager directly...")
    
    # Initialize LLM and memory
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    memory = FinancialSituationMemory("test_risk_memory", DEFAULT_CONFIG)
    
    # Create risk manager
    risk_manager_node = create_risk_manager(llm, memory)
    
    # Create mock state with all required data
    mock_state = {
        "company_of_interest": "TSLA",
        "market_report": "Mock market analysis report with technical indicators showing bullish signals. RSI at 45, MACD positive crossover, price above 50-day SMA.",
        "news_report": "Mock news report about Tesla's strong Q2 deliveries and energy storage deployment. Positive momentum in EV market.",
        "fundamentals_report": "Mock fundamentals showing Tesla with P/E of 180, strong revenue growth, but high valuation concerns.",
        "sentiment_report": "Mock social sentiment showing mixed reactions - positive on deliveries, negative on political controversies.",
        "investment_plan": "Mock trader plan suggesting a cautious BUY position with 5% allocation due to mixed signals.",
        "risk_debate_state": {
            "history": """**Risky Analyst**: I recommend AGGRESSIVE BUY. Tesla's delivery numbers are strong and the EV market is expanding rapidly. This is a growth opportunity.

**Safe Analyst**: I recommend HOLD or REDUCE position. The P/E ratio of 180 is extremely high and political risks with Musk are concerning.

**Neutral Analyst**: I recommend MODERATE BUY with risk management. Tesla has strong fundamentals but high valuation requires careful position sizing.""",
            "count": 1
        }
    }
    
    print("🔍 Input state keys:", list(mock_state.keys()))
    print("🔍 Market report length:", len(mock_state["market_report"]))
    print("🔍 News report length:", len(mock_state["news_report"]))
    print("🔍 Fundamentals report length:", len(mock_state["fundamentals_report"]))
    print("🔍 Sentiment report length:", len(mock_state["sentiment_report"]))
    print("🔍 Investment plan length:", len(mock_state["investment_plan"]))
    print("🔍 Risk history length:", len(mock_state["risk_debate_state"]["history"]))
    
    try:
        # Execute risk manager
        print("\n🚀 Executing risk manager...")
        result = risk_manager_node(mock_state)
        
        print("\n📊 RESULT ANALYSIS:")
        print("=" * 50)
        print("🔍 Result keys:", list(result.keys()))
        
        # Check final_trade_decision
        final_decision = result.get("final_trade_decision", "")
        print(f"🔍 Final trade decision length: {len(final_decision)}")
        
        if final_decision:
            print("✅ Final trade decision found!")
            print(f"📝 Preview: {final_decision[:300]}...")
            
            # Validate content
            if "I'm sorry" in final_decision or "no paragraph" in final_decision:
                print("❌ Error response detected!")
                return False
            elif any(keyword in final_decision.upper() for keyword in ["BUY", "SELL", "HOLD"]):
                print("✅ Valid decision with recommendation!")
                return True
            else:
                print("⚠️ Decision found but no clear BUY/SELL/HOLD recommendation")
                return False
        else:
            print("❌ No final trade decision found!")
            
            # Check risk_debate_state
            risk_state = result.get("risk_debate_state", {})
            judge_decision = risk_state.get("judge_decision", "")
            print(f"🔍 Judge decision length: {len(judge_decision)}")
            
            if judge_decision:
                print("✅ Judge decision found in risk_debate_state!")
                print(f"📝 Preview: {judge_decision[:300]}...")
                return True
            else:
                print("❌ No judge decision found either!")
                return False
                
    except Exception as e:
        print(f"❌ Error executing risk manager: {e}")
        return False

if __name__ == "__main__":
    success = test_risk_manager_directly()
    
    if success:
        print("\n🎉 Risk manager direct test PASSED!")
        exit(0)
    else:
        print("\n❌ Risk manager direct test FAILED!")
        exit(1) 