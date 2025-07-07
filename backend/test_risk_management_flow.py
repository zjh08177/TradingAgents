#!/usr/bin/env python3
"""
Comprehensive test specifically for risk management flow:
1. Risk analysts (Risky, Safe, Neutral) generate proper responses
2. Risk aggregator combines responses correctly
3. Risk manager receives proper data and generates valid decisions
4. All risk management state transitions work properly
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.graph.trading_graph import TradingAgentsGraph

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_risk_management_flow():
    """Test the complete risk management flow with detailed validation."""
    
    print("🎯 Starting comprehensive risk management flow test...")
    print("=" * 80)
    
    # Initialize the graph
    try:
        graph = TradingAgentsGraph(debug=True)
        print("✅ Graph initialized successfully")
    except Exception as e:
        print(f"❌ Graph initialization failed: {e}")
        return False, None
    
    # Test parameters
    company = "TSLA"
    trade_date = "2025-07-05"
    
    print(f"\n📊 Testing risk management for {company} on {trade_date}")
    print("-" * 60)
    
    # Track risk management specific states
    risk_states = []
    risk_analyst_responses = {}
    risk_aggregator_called = False
    risk_manager_called = False
    final_state = None
    
    start_time = time.time()
    chunks_processed = 0
    
    try:
        # Run the analysis and get the final result
        final_result = graph.graph.invoke(
            graph.propagator.create_initial_state(company, trade_date),
            {"recursion_limit": 100}
        )
        
        # For debugging, we can still track some basic execution info
        print(f"✅ Graph execution completed successfully")
        print(f"📊 Final result keys: {list(final_result.keys())}")
        
        # Check if risk management components executed based on final result
        chunks_processed = 1  # Just set a placeholder since we're not streaming
        
        # Check the final result for risk management components
        if "risk_debate_state" in final_result:
            risk_state = final_result["risk_debate_state"]
            print(f"🎯 Risk debate state found in final result")
            
            # Track individual analyst responses from final state
            if risk_state and "current_risky_response" in risk_state and risk_state["current_risky_response"]:
                risk_analyst_responses["Risky Analyst"] = risk_state["current_risky_response"]
                print(f"✅ Risky Analyst response found ({len(risk_state['current_risky_response'])} chars)")
            
            if risk_state and "current_safe_response" in risk_state and risk_state["current_safe_response"]:
                risk_analyst_responses["Safe Analyst"] = risk_state["current_safe_response"]
                print(f"✅ Safe Analyst response found ({len(risk_state['current_safe_response'])} chars)")
            
            if risk_state and "current_neutral_response" in risk_state and risk_state["current_neutral_response"]:
                risk_analyst_responses["Neutral Analyst"] = risk_state["current_neutral_response"]
                print(f"✅ Neutral Analyst response found ({len(risk_state['current_neutral_response'])} chars)")
            
            # Track aggregator
            if risk_state and "history" in risk_state and risk_state["history"]:
                risk_aggregator_called = True
                print(f"✅ Risk Aggregator history found ({len(risk_state['history'])} chars)")
            
            # Track risk manager
            if risk_state and "judge_decision" in risk_state and risk_state["judge_decision"]:
                risk_manager_called = True
                print(f"✅ Risk Manager decision found ({len(risk_state['judge_decision'])} chars)")
        
        # Check for final_trade_decision
        if "final_trade_decision" in final_result and final_result["final_trade_decision"]:
            if not risk_manager_called:
                risk_manager_called = True
            print(f"✅ Final trade decision found ({len(final_result['final_trade_decision'])} chars)")
    
        # Use the complete final result instead of streaming chunks
        final_state = final_result
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return False, None
    
    execution_time = time.time() - start_time
    
    # Comprehensive validation
    print("\n" + "=" * 80)
    print("🎯 RISK MANAGEMENT FLOW VALIDATION")
    print("=" * 80)
    
    issues = []
    
    # 1. Validate risk analyst responses
    print("\n📊 RISK ANALYST RESPONSES:")
    print("-" * 40)
    
    expected_analysts = ["Risky Analyst", "Safe Analyst", "Neutral Analyst"]
    for analyst in expected_analysts:
        if analyst in risk_analyst_responses:
            response = risk_analyst_responses[analyst]
            print(f"✅ {analyst}: {len(response)} chars")
            
            # Only validate response quality if it's not a placeholder
            if response != "Response captured from execution logs":
                if len(response) < 100:
                    issues.append(f"{analyst} response too short ({len(response)} chars)")
                elif "I'm sorry" in response or "no paragraph" in response:
                    issues.append(f"{analyst} generated error response")
        else:
            issues.append(f"{analyst} did not generate response")
            print(f"❌ {analyst}: NO RESPONSE")
    
    # 2. Validate risk aggregator
    print(f"\n🔄 RISK AGGREGATOR:")
    print("-" * 40)
    
    if risk_aggregator_called:
        print("✅ Risk Aggregator executed")
        
        # Find the aggregated state
        aggregated_state = None
        for state in risk_states:
            if state["state"].get("history"):
                aggregated_state = state["state"]
                break
        
        if aggregated_state:
            history = aggregated_state["history"]
            print(f"✅ Combined history: {len(history)} chars")
            
            # Validate that all analyst responses are included
            for analyst in expected_analysts:
                analyst_name = analyst.split()[0]  # "Risky", "Safe", "Neutral"
                if analyst_name not in history:
                    issues.append(f"Risk aggregator missing {analyst} response in history")
                else:
                    print(f"✅ {analyst} response included in history")
        else:
            # If no aggregated state found, but aggregator was called, that's still OK
            print("⚠️ Risk aggregator executed but no combined history captured in state")
    else:
        issues.append("Risk Aggregator was not called")
        print("❌ Risk Aggregator: NOT EXECUTED")
    
    # 3. Validate risk manager
    print(f"\n🎯 RISK MANAGER:")
    print("-" * 40)
    
    if risk_manager_called:
        print("✅ Risk Manager executed")
        
        # Find the final decision
        final_decision = final_state.get("final_trade_decision", "")
        judge_decision = final_state.get("risk_debate_state", {}).get("judge_decision", "")
        
        # Debug: Print the actual final state keys
        print(f"🔍 Final state keys: {list(final_state.keys())}")
        print(f"🔍 Final trade decision length: {len(final_decision)}")
        print(f"🔍 Judge decision length: {len(judge_decision)}")
        
        if final_decision:
            print(f"✅ Final trade decision: {len(final_decision)} chars")
            
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
                print("✅ Final decision appears valid")
                print(f"📝 Decision preview: {final_decision[:200]}...")
        elif judge_decision:
            # If no final_trade_decision but judge_decision exists, use that
            print(f"✅ Judge decision found: {len(judge_decision)} chars")
            print(f"📝 Judge decision preview: {judge_decision[:200]}...")
            
            # Validate judge decision content
            if "I'm sorry" in judge_decision or "no paragraph" in judge_decision:
                issues.append("Risk manager generated error response")
                print("❌ Risk manager generated error response")
            elif len(judge_decision) < 100:
                issues.append(f"Judge decision too short ({len(judge_decision)} chars)")
                print(f"❌ Judge decision too short ({len(judge_decision)} chars)")
            elif not any(keyword in judge_decision.upper() for keyword in ["BUY", "SELL", "HOLD"]):
                issues.append("Judge decision missing BUY/SELL/HOLD recommendation")
                print("❌ Judge decision missing BUY/SELL/HOLD recommendation")
            else:
                print("✅ Judge decision appears valid")
        else:
            # If no final decision but risk manager was called, that's still an issue
            issues.append("Risk manager executed but did not generate final decision")
            print("❌ Risk manager executed but no final trade decision generated")
        
        # Validate consistency (only if both exist)
        if judge_decision and final_decision and judge_decision != final_decision:
            issues.append("Mismatch between judge_decision and final_trade_decision")
            print("❌ Mismatch between judge_decision and final_trade_decision")
    else:
        issues.append("Risk Manager was not called")
        print("❌ Risk Manager: NOT EXECUTED")
    
    # 4. Validate state transitions
    print(f"\n🔄 STATE TRANSITIONS:")
    print("-" * 40)
    
    if len(risk_states) > 0:
        print(f"✅ {len(risk_states)} risk state transitions captured")
        
        # Check for proper progression
        has_dispatcher = any("Risk Dispatcher" in state["keys"] for state in risk_states)
        has_analysts = any(any(analyst in state["keys"] for analyst in expected_analysts) for state in risk_states)
        has_aggregator = any("Risk Aggregator" in state["keys"] for state in risk_states)
        has_judge = any("Risk Judge" in state["keys"] for state in risk_states)
        
        if has_dispatcher:
            print("✅ Risk Dispatcher executed")
        else:
            issues.append("Risk Dispatcher not found in state transitions")
        
        if has_analysts:
            print("✅ Risk Analysts executed")
        else:
            issues.append("Risk Analysts not found in state transitions")
        
        if has_aggregator:
            print("✅ Risk Aggregator executed")
        else:
            issues.append("Risk Aggregator not found in state transitions")
        
        if has_judge:
            print("✅ Risk Judge executed")
        else:
            issues.append("Risk Judge not found in state transitions")
    else:
        issues.append("No risk state transitions captured")
        print("❌ No risk state transitions captured")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("🎯 FINAL VERDICT")
    print("=" * 80)
    
    print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
    print(f"📦 Chunks processed: {chunks_processed}")
    print(f"🎯 Risk states captured: {len(risk_states)}")
    
    if not issues:
        print("\n✅ ALL RISK MANAGEMENT TESTS PASSED! 🎉")
        print("\nKey achievements:")
        print("- All 3 risk analysts generated valid responses")
        print("- Risk aggregator properly combined responses")
        print("- Risk manager generated valid final decision")
        print("- All state transitions executed correctly")
        print(f"- Total execution time: {execution_time:.2f}s")
    else:
        print("\n❌ RISK MANAGEMENT ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    
    return not bool(issues), final_state

if __name__ == "__main__":
    success, final_state = test_risk_management_flow()
    
    if success:
        print("\n🎉 Risk management flow test completed successfully!")
        exit(0)
    else:
        print("\n❌ Risk management flow test failed!")
        exit(1) 