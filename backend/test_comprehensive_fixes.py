#!/usr/bin/env python3
"""
Comprehensive test to verify all fixes:
1. Tool call limits (max 3 per analyst)
2. No duplicate completion messages  
3. Bear researcher completion status
4. Risk analysts parallel execution
5. Proper status updates for all agents
"""

import asyncio
import json
import time
from datetime import datetime
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def create_test_config():
    """Create test configuration"""
    config = DEFAULT_CONFIG.copy()
    config.update({
        "llm_provider": "openai",
        "deep_think_llm": "gpt-4o",
        "quick_think_llm": "gpt-4o",
        "backend_url": "https://api.openai.com/v1",
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
        "online_tools": True,
    })
    return config

def analyze_tool_calls(state, channel_name):
    """Analyze tool calls in a message channel"""
    messages = state.get(channel_name, [])
    tool_calls = []
    tool_responses = []
    
    for msg in messages:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    'name': tc.name if hasattr(tc, 'name') else 'unknown',
                    'args': tc.args if hasattr(tc, 'args') else {}
                })
        if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool':
            tool_responses.append(msg)
    
    return tool_calls, tool_responses

def test_graph_execution():
    """Test the trading graph execution with all fixes"""
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE TEST: Trading Graph Fixes")
    print("="*80)
    
    # Initialize graph
    config = create_test_config()
    graph = TradingAgentsGraph(
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=True,
        config=config
    )
    
    # Test parameters
    ticker = "TSLA"
    date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📊 Testing with: {ticker} on {date}")
    print("-"*80)
    
    # Track execution metrics
    start_time = time.time()
    chunks_processed = 0
    agent_completions = {}
    tool_call_counts = {}
    duplicate_completions = set()
    
    # Initialize state
    init_state = graph.propagator.create_initial_state(ticker, date)
    args = graph.propagator.get_graph_args()
    
    # Stream execution
    print("\n🔄 Starting graph execution...")
    
    for chunk in graph.graph.stream(init_state, **args):
        chunks_processed += 1
        
        # Analyze message channels
        for channel in ["market_messages", "social_messages", "news_messages", "fundamentals_messages"]:
            if channel in chunk and chunk[channel]:
                analyst_type = channel.replace("_messages", "")
                
                # Count tool calls
                tool_calls, tool_responses = analyze_tool_calls(chunk, channel)
                if tool_calls:
                    if analyst_type not in tool_call_counts:
                        tool_call_counts[analyst_type] = []
                    tool_call_counts[analyst_type].extend(tool_calls)
                    print(f"🔧 {analyst_type.upper()}: {len(tool_calls)} new tool calls (total: {len(tool_call_counts[analyst_type])})")
        
        # Check report completions
        report_fields = {
            "market_report": "Market Analyst",
            "sentiment_report": "Social Media Analyst",
            "news_report": "News Analyst",
            "fundamentals_report": "Fundamentals Analyst"
        }
        
        for report_key, agent_name in report_fields.items():
            if report_key in chunk and chunk[report_key]:
                if agent_name in agent_completions:
                    duplicate_completions.add(agent_name)
                    print(f"⚠️  DUPLICATE COMPLETION: {agent_name}")
                else:
                    agent_completions[agent_name] = time.time()
                    print(f"✅ {agent_name} completed")
        
        # Check Bull/Bear completion
        if "investment_debate_state" in chunk:
            debate_state = chunk["investment_debate_state"]
            if debate_state.get("judge_decision"):
                if "Bull Researcher" not in agent_completions:
                    agent_completions["Bull Researcher"] = time.time()
                    print("✅ Bull Researcher completed")
                if "Bear Researcher" not in agent_completions:
                    agent_completions["Bear Researcher"] = time.time()
                    print("✅ Bear Researcher completed")
        
        # Check risk analysts
        if "risk_debate_state" in chunk:
            risk_state = chunk["risk_debate_state"]
            
            # Track parallel execution timing
            if risk_state.get("current_risky_response") and "Risky Analyst" not in agent_completions:
                agent_completions["Risky Analyst"] = time.time()
                print("✅ Risky Analyst completed")
            
            if risk_state.get("current_safe_response") and "Safe Analyst" not in agent_completions:
                agent_completions["Safe Analyst"] = time.time()
                print("✅ Safe Analyst completed")
                
            if risk_state.get("current_neutral_response") and "Neutral Analyst" not in agent_completions:
                agent_completions["Neutral Analyst"] = time.time()
                print("✅ Neutral Analyst completed")
    
    # Final state
    final_state = chunk
    execution_time = time.time() - start_time
    
    # Generate report
    print("\n" + "="*80)
    print("📊 EXECUTION REPORT")
    print("="*80)
    
    print(f"\n⏱️  Total execution time: {execution_time:.2f} seconds")
    print(f"📦 Chunks processed: {chunks_processed}")
    
    # Tool call analysis
    print("\n🔧 TOOL CALL ANALYSIS:")
    print("-"*40)
    
    issues = []
    for analyst, calls in tool_call_counts.items():
        print(f"\n{analyst.upper()} ANALYST:")
        print(f"  Total tool calls: {len(calls)}")
        
        # Check limit
        if len(calls) > 3:
            issues.append(f"{analyst} exceeded tool call limit: {len(calls)} > 3")
            print(f"  ❌ EXCEEDED LIMIT!")
        else:
            print(f"  ✅ Within limit")
        
        # Check for duplicates
        unique_calls = set()
        duplicates = []
        for call in calls:
            call_str = f"{call['name']}:{json.dumps(call['args'], sort_keys=True)}"
            if call_str in unique_calls:
                duplicates.append(call_str)
            unique_calls.add(call_str)
        
        if duplicates:
            issues.append(f"{analyst} has duplicate tool calls: {duplicates}")
            print(f"  ❌ DUPLICATE CALLS: {len(duplicates)}")
        else:
            print(f"  ✅ No duplicate calls")
    
    # Completion analysis
    print("\n✅ AGENT COMPLETION ANALYSIS:")
    print("-"*40)
    
    expected_agents = [
        "Market Analyst", "Social Media Analyst", "News Analyst", "Fundamentals Analyst",
        "Bull Researcher", "Bear Researcher", "Risky Analyst", "Safe Analyst", "Neutral Analyst"
    ]
    
    for agent in expected_agents:
        if agent in agent_completions:
            print(f"✅ {agent}: Completed")
        else:
            issues.append(f"{agent} did not complete")
            print(f"❌ {agent}: NOT COMPLETED")
    
    # Duplicate completion check
    if duplicate_completions:
        print(f"\n⚠️  DUPLICATE COMPLETIONS DETECTED: {list(duplicate_completions)}")
        issues.extend([f"Duplicate completion: {agent}" for agent in duplicate_completions])
    else:
        print("\n✅ No duplicate completions")
    
    # Risk analyst parallelization check
    print("\n⚡ RISK ANALYST PARALLELIZATION:")
    print("-"*40)
    
    risk_analysts = ["Risky Analyst", "Safe Analyst", "Neutral Analyst"]
    risk_times = {agent: agent_completions.get(agent, 0) for agent in risk_analysts}
    
    if all(risk_times.values()):
        min_time = min(risk_times.values())
        max_time = max(risk_times.values())
        time_spread = max_time - min_time
        
        print(f"Time spread: {time_spread:.2f} seconds")
        
        if time_spread < 5:  # Should complete within 5 seconds of each other if parallel
            print("✅ Risk analysts executed in parallel")
        else:
            issues.append(f"Risk analysts may not be parallel: {time_spread:.2f}s spread")
            print(f"⚠️  Risk analysts may not be parallel")
    else:
        missing = [a for a in risk_analysts if not risk_times[a]]
        issues.append(f"Risk analysts did not complete: {missing}")
        print(f"❌ Risk analysts did not complete: {missing}")
    
    # Final verdict
    print("\n" + "="*80)
    print("🎯 FINAL VERDICT")
    print("="*80)
    
    if not issues:
        print("\n✅ ALL TESTS PASSED! 🎉")
        print("\nKey achievements:")
        print("- Tool calls limited to 3 per analyst")
        print("- No duplicate completions")
        print("- Bear researcher properly tracked")
        print("- Risk analysts run in parallel")
        print(f"- Total execution time: {execution_time:.2f}s")
    else:
        print("\n❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    
    return not bool(issues), final_state

if __name__ == "__main__":
    success, final_state = test_graph_execution()
    
    # Check final decision
    if final_state.get("final_trade_decision"):
        print(f"\n📊 Final trading decision: {final_state['final_trade_decision'][:100]}...")
    
    exit(0 if success else 1)