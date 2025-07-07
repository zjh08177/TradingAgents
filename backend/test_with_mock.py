#!/usr/bin/env python3
"""
Test TradingAgents with Mock LLM (no API keys required)
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variable to use mock LLM
os.environ["USE_MOCK_LLM"] = "true"

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.utils.timing import timing_tracker
from tradingagents.utils.mock_llm import MockLLM

def test_analysis_with_mock():
    """Test the full analysis pipeline with mock LLM"""
    ticker = "AAPL"
    analysis_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing TradingAgents with Mock LLM")
    print(f"📊 Ticker: {ticker}")
    print(f"📅 Date: {analysis_date}")
    print(f"{'='*60}\n")
    
    try:
        # Start timing
        timing_tracker.start_total()
        
        # Create mock config
        config = {
            "llm_provider": "mock",
            "llm_model": "mock-gpt-4",
            "online_tools": False,  # Use offline tools
            "data_provider": "finnhub",
            "output_dir": "./test_output",
            "project_dir": os.path.dirname(os.path.abspath(__file__)),
            "api_port": 8000
        }
        
        # Initialize trading graph
        print("🔧 Initializing TradingAgents graph with mock LLM...")
        graph = TradingAgentsGraph(
            selected_analysts=["market", "social", "news", "fundamentals"],
            debug=True,
            config=config
        )
        
        # Override LLMs with mock versions
        graph.quick_thinking_llm = MockLLM("mock-gpt-4")
        graph.deep_thinking_llm = MockLLM("mock-gpt-4-deep")
        
        print("✅ Graph initialized successfully")
        
        # Run analysis
        print(f"\n🚀 Starting analysis for {ticker}...")
        final_state, processed_signal = graph.propagate(ticker, analysis_date)
        
        # End timing
        timing_tracker.end_total()
        timing_summary = timing_tracker.get_summary()
        
        # Display results
        print(f"\n{'='*60}")
        print("📊 ANALYSIS RESULTS")
        print(f"{'='*60}")
        
        # Check each report
        reports = {
            "Market Report": final_state.get("market_report"),
            "Sentiment Report": final_state.get("sentiment_report"),
            "News Report": final_state.get("news_report"),
            "Fundamentals Report": final_state.get("fundamentals_report"),
            "Investment Plan": final_state.get("investment_plan"),
            "Trader Plan": final_state.get("trader_investment_plan"),
            "Final Decision": final_state.get("final_trade_decision")
        }
        
        all_reports_generated = True
        for name, report in reports.items():
            if report:
                print(f"✅ {name}: Generated ({len(str(report))} chars)")
                # Print first 200 chars of each report
                print(f"   Preview: {str(report)[:200]}...")
            else:
                print(f"❌ {name}: Missing")
                all_reports_generated = False
        
        print(f"\n📈 Processed Signal: {processed_signal}")
        
        # Timing summary
        print(f"\n{'='*60}")
        print("⏱️ PERFORMANCE METRICS")
        print(f"{'='*60}")
        print(f"Total Duration: {timing_summary['total_duration']:.2f}s")
        print(f"Agent Count: {timing_summary['agent_count']}")
        print(f"Tool Calls: {timing_summary['tool_call_count']}")
        
        # Test results
        print(f"\n{'='*60}")
        print("🧪 TEST RESULTS")
        print(f"{'='*60}")
        
        if all_reports_generated and processed_signal:
            print("✅ ALL TESTS PASSED!")
            print("   - All agents executed successfully")
            print("   - All reports generated")
            print("   - Final signal produced")
            print("   - No API keys required!")
        else:
            print("❌ SOME TESTS FAILED")
            if not all_reports_generated:
                print("   - Some reports were not generated")
            if not processed_signal:
                print("   - No final signal produced")
        
        return final_state, processed_signal
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    # Run the test
    final_state, signal = test_analysis_with_mock()
    
    if final_state:
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Final Signal: {signal}")
    else:
        print(f"\n❌ Test failed!")
        sys.exit(1)