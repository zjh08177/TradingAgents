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

def test_risk_manager_isolated():
    """Test the risk manager in isolation with mock data."""
    print("🎯 Testing Risk Manager in isolation...")
    
    # Initialize LLM and memory
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    memory = FinancialSituationMemory("test_risk_memory", DEFAULT_CONFIG)
    
    # Create the risk manager
    risk_manager = create_risk_manager(llm, memory)
    
    # Create mock state with all required data
    mock_state = {
        "company_of_interest": "TSLA",
        "trade_date": "2025-07-05",
        "market_report": "Market analysis shows TSLA is trading at $315.35 with strong technical indicators. RSI is at 65, MACD is bullish, and the stock is above its 50-day moving average. Volume is above average indicating strong interest.",
        "news_report": "Recent news shows Tesla delivered 384,000 vehicles in Q2 2025, marking strong growth. However, there are concerns about increased competition from Chinese EV manufacturers and regulatory scrutiny over FSD technology.",
        "fundamentals_report": "Tesla's fundamentals show P/E ratio of 162.31, indicating high valuation. The company has strong cash position of $37B and positive free cash flow. However, the high valuation multiples suggest premium pricing.",
        "sentiment_report": "Social media sentiment is mixed with 58% positive mentions on Reddit. There's excitement about robotaxi launch but concerns about political controversies involving Elon Musk.",
        "investment_plan": "Based on analysis, Tesla shows strong fundamentals but high valuation. The company has growth potential in autonomous driving and energy storage, but faces competition and regulatory challenges.",
        "risk_debate_state": {
            "risky_history": "Risky analyst argues for aggressive position due to growth potential in robotaxi and energy storage segments.",
            "safe_history": "Safe analyst recommends caution due to high valuation and increasing competition from Chinese manufacturers.",
            "neutral_history": "Neutral analyst suggests balanced approach, acknowledging both growth potential and risks.",
            "history": "Combined debate between three risk analysts shows mixed perspectives on Tesla's risk profile. Key concerns include valuation, competition, and regulatory risks.",
            "latest_speaker": "Neutral Analyst",
            "current_risky_response": "Strong buy recommendation based on innovation and market leadership",
            "current_safe_response": "Hold recommendation due to valuation concerns and market risks",
            "current_neutral_response": "Moderate buy with position sizing to manage risk",
            "count": 3
        }
    }
    
    print("📊 Mock state created with all required fields")
    print(f"  - market_report: {len(mock_state['market_report'])} chars")
    print(f"  - news_report: {len(mock_state['news_report'])} chars")
    print(f"  - fundamentals_report: {len(mock_state['fundamentals_report'])} chars")
    print(f"  - sentiment_report: {len(mock_state['sentiment_report'])} chars")
    print(f"  - investment_plan: {len(mock_state['investment_plan'])} chars")
    print(f"  - risk_debate_history: {len(mock_state['risk_debate_state']['history'])} chars")
    
    # Execute the risk manager
    print("\n🎯 Executing risk manager...")
    start_time = time.time()
    
    try:
        result = risk_manager(mock_state)
        execution_time = time.time() - start_time
        
        print(f"✅ Risk manager executed successfully in {execution_time:.2f}s")
        print(f"📊 Result keys: {list(result.keys())}")
        
        # Validate the result
        issues = []
        
        # Check for final_trade_decision
        if "final_trade_decision" in result:
            final_decision = result["final_trade_decision"]
            print(f"✅ Final trade decision: {len(final_decision)} chars")
            print(f"📝 Decision preview: {final_decision[:200]}...")
            
            # Validate decision content
            if "I'm sorry" in final_decision or "no paragraph" in final_decision:
                issues.append("Risk manager generated error response")
                print("❌ Risk manager generated error response")
            elif len(final_decision) < 100:
                issues.append(f"Final decision too short ({len(final_decision)} chars)")
                print(f"❌ Final decision too short ({len(final_decision)} chars)")
            elif not any(keyword in final_decision.upper() for keyword in ["BUY", "SELL", "HOLD"]):
                issues.append("Final decision missing BUY/SELL/HOLD recommendation")
                print("❌ Final decision missing BUY/SELL/HOLD recommendation")
            else:
                print("✅ Final decision appears valid and contains trading recommendation")
        else:
            issues.append("No final_trade_decision in result")
            print("❌ No final_trade_decision in result")
        
        # Check for risk_debate_state
        if "risk_debate_state" in result:
            risk_state = result["risk_debate_state"]
            print(f"✅ Risk debate state: {len(str(risk_state))} chars")
            
            if "judge_decision" in risk_state:
                judge_decision = risk_state["judge_decision"]
                print(f"✅ Judge decision: {len(judge_decision)} chars")
                print(f"📝 Judge decision preview: {judge_decision[:200]}...")
            else:
                issues.append("No judge_decision in risk_debate_state")
                print("❌ No judge_decision in risk_debate_state")
        else:
            issues.append("No risk_debate_state in result")
            print("❌ No risk_debate_state in result")
        
        # Final verdict
        if not issues:
            print("\n✅ ALL TESTS PASSED! 🎉")
            print("Risk manager is working correctly:")
            print("- Generates valid final trade decision")
            print("- Contains proper BUY/SELL/HOLD recommendation")
            print("- Updates risk debate state correctly")
            print("- Handles all input data properly")
            return True
        else:
            print("\n❌ ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
            return False
            
    except Exception as e:
        print(f"❌ Risk manager execution failed: {e}")
        return False

if __name__ == "__main__":
    success = test_risk_manager_isolated()
    
    if success:
        print("\n🎉 Risk manager isolated test completed successfully!")
        print("The risk manager component is working correctly.")
        print("The issue with the full system test is likely related to state management or streaming.")
        exit(0)
    else:
        print("\n❌ Risk manager isolated test failed!")
        exit(1) 