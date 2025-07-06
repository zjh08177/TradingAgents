#!/usr/bin/env python3
"""
Simple test for main.py to verify basic functionality
"""
import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Simple Main.py Test")
print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 60)

try:
    # Import modules
    print("📦 Importing modules...")
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    print("✅ Modules imported successfully")
    
    # Create config
    print("\n🔧 Creating configuration...")
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "google"
    config["backend_url"] = "https://generativelanguage.googleapis.com/v1"
    config["deep_think_llm"] = "gemini-2.0-flash"
    config["quick_think_llm"] = "gemini-2.0-flash"
    config["max_debate_rounds"] = 1
    config["online_tools"] = True
    print("✅ Configuration created")
    
    # Initialize graph
    print("\n🔧 Initializing TradingAgentsGraph...")
    start_init = time.time()
    ta = TradingAgentsGraph(debug=True, config=config)
    print(f"✅ Graph initialized in {time.time() - start_init:.2f}s")
    
    # Run propagation
    print("\n🔄 Running propagation for NVDA on 2024-05-10...")
    print("⏳ This may take 30-60 seconds...")
    
    # Track messages during propagation
    message_count = 0
    agent_activity = []
    
    # Custom propagate to track activity
    init_agent_state = ta.propagator.create_initial_state("NVDA", "2024-05-10")
    args = ta.propagator.get_graph_args()
    
    print("\n📊 Streaming analysis...")
    start_prop = time.time()
    
    for chunk_idx, chunk in enumerate(ta.graph.stream(init_agent_state, **args)):
        # Log progress every 10 chunks
        if chunk_idx % 10 == 0:
            elapsed = time.time() - start_prop
            print(f"  ⏳ Processing chunk {chunk_idx} ({elapsed:.1f}s elapsed)")
        
        # Track messages
        if len(chunk.get("messages", [])) > 0:
            message_count += len(chunk["messages"])
            
        # Track completed reports
        reports = ['market_report', 'sentiment_report', 'news_report', 
                  'fundamentals_report', 'investment_plan', 'trader_investment_plan',
                  'final_trade_decision']
        
        for report in reports:
            if report in chunk and chunk[report]:
                agent_activity.append((time.time() - start_prop, report))
                print(f"  ✅ {report} completed at {time.time() - start_prop:.1f}s")
    
    prop_time = time.time() - start_prop
    print(f"\n✅ Propagation completed in {prop_time:.2f}s")
    print(f"📊 Total messages processed: {message_count}")
    
    # Process signal
    if hasattr(ta, 'curr_state') and ta.curr_state:
        decision = ta.process_signal(ta.curr_state.get("final_trade_decision", ""))
        print(f"📊 Final decision: {decision}")
        
        # Validate results
        print("\n🔍 Validating results:")
        for report in reports:
            if report in ta.curr_state and ta.curr_state[report]:
                print(f"  ✅ {report}: {len(str(ta.curr_state[report]))} chars")
            else:
                print(f"  ❌ {report}: Missing")
    
    print("\n✅ TEST PASSED - Main.py is working correctly")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 60)
print("Test completed successfully!")