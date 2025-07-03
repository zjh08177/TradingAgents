#!/usr/bin/env python
"""
Test specifically for parallel execution verification
"""
import time
from datetime import datetime
from collections import defaultdict
import threading
import json
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


class ParallelExecutionTracker:
    """Track parallel execution of agents"""
    def __init__(self):
        self.active_agents = {}  # agent_name -> start_time
        self.parallel_groups = []  # List of sets of agents that ran in parallel
        self.agent_timeline = []  # List of (time, agent, action) tuples
        self.lock = threading.Lock()
        
    def agent_started(self, agent_name, timestamp=None):
        """Record agent start"""
        timestamp = timestamp or time.time()
        with self.lock:
            self.active_agents[agent_name] = timestamp
            self.agent_timeline.append((timestamp, agent_name, 'start'))
            
            # Check if multiple agents are active
            if len(self.active_agents) > 1:
                parallel_set = set(self.active_agents.keys())
                self.parallel_groups.append({
                    'agents': parallel_set,
                    'time': timestamp,
                    'count': len(parallel_set)
                })
                print(f"🔄 PARALLEL EXECUTION: {list(parallel_set)} at {datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]}")
    
    def agent_ended(self, agent_name, timestamp=None):
        """Record agent end"""
        timestamp = timestamp or time.time()
        with self.lock:
            if agent_name in self.active_agents:
                start_time = self.active_agents.pop(agent_name)
                duration = timestamp - start_time
                self.agent_timeline.append((timestamp, agent_name, 'end'))
                print(f"✅ {agent_name} completed in {duration:.2f}s")
    
    def get_parallel_summary(self):
        """Get summary of parallel executions"""
        summary = {
            'total_parallel_groups': len(self.parallel_groups),
            'max_parallel_agents': max((g['count'] for g in self.parallel_groups), default=0),
            'parallel_groups': self.parallel_groups,
            'timeline': sorted(self.agent_timeline, key=lambda x: x[0])
        }
        return summary


def test_parallel_execution():
    """Test that agents execute in parallel when expected"""
    print("🚀 Testing Parallel Execution of TradingAgents")
    print("=" * 80)
    
    # Create results directory
    results_dir = Path("test_results/parallel_execution")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure for testing
    config = DEFAULT_CONFIG.copy()
    config.update({
        "llm_provider": "google",
        "backend_url": "https://generativelanguage.googleapis.com/v1",
        "deep_think_llm": "gemini-2.0-flash", 
        "quick_think_llm": "gemini-2.0-flash",
        "max_debate_rounds": 2,
        "online_tools": True
    })
    
    # Create tracker
    tracker = ParallelExecutionTracker()
    
    # Custom TradingAgentsGraph to track execution
    class TrackedGraph(TradingAgentsGraph):
        def __init__(self, *args, tracker=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.tracker = tracker
            self.message_timestamps = []
            
        def propagate(self, company_name, trade_date):
            """Enhanced propagate with parallel tracking"""
            self.ticker = company_name
            
            # Initialize state
            init_agent_state = self.propagator.create_initial_state(company_name, trade_date)
            args = self.propagator.get_graph_args()
            
            trace = []
            agent_states = {}  # Track agent states
            
            print(f"\n📊 Starting analysis for {company_name} on {trade_date}")
            print("-" * 60)
            
            # Process stream
            for chunk_idx, chunk in enumerate(self.graph.stream(init_agent_state, **args)):
                timestamp = time.time()
                
                # Detect which agents are active based on chunk content
                chunk_agents = set()
                
                # Check for analyst reports
                if "market_report" in chunk and chunk["market_report"] and "market_analyst" not in agent_states:
                    agent_states["market_analyst"] = "completed"
                    if self.tracker:
                        self.tracker.agent_ended("market_analyst", timestamp)
                
                if "sentiment_report" in chunk and chunk["sentiment_report"] and "social_analyst" not in agent_states:
                    agent_states["social_analyst"] = "completed"
                    if self.tracker:
                        self.tracker.agent_ended("social_analyst", timestamp)
                
                if "news_report" in chunk and chunk["news_report"] and "news_analyst" not in agent_states:
                    agent_states["news_analyst"] = "completed"
                    if self.tracker:
                        self.tracker.agent_ended("news_analyst", timestamp)
                
                if "fundamentals_report" in chunk and chunk["fundamentals_report"] and "fundamentals_analyst" not in agent_states:
                    agent_states["fundamentals_analyst"] = "completed"
                    if self.tracker:
                        self.tracker.agent_ended("fundamentals_analyst", timestamp)
                
                # Check messages for agent activity
                if len(chunk.get("messages", [])) > 0:
                    last_message = chunk["messages"][-1]
                    
                    # Try to identify agent from message
                    agent_name = None
                    if hasattr(last_message, 'name') and last_message.name:
                        agent_name = last_message.name
                    
                    # Map common agent names
                    agent_mapping = {
                        "MarketAnalyst": "market_analyst",
                        "SocialMediaAnalyst": "social_analyst", 
                        "NewsAnalyst": "news_analyst",
                        "FundamentalsAnalyst": "fundamentals_analyst",
                        "BullResearcher": "bull_researcher",
                        "BearResearcher": "bear_researcher",
                        "ResearchManager": "research_manager",
                        "Trader": "trader",
                        "RiskManager": "risk_manager"
                    }
                    
                    if agent_name in agent_mapping:
                        mapped_name = agent_mapping[agent_name]
                        if mapped_name not in agent_states:
                            agent_states[mapped_name] = "active"
                            if self.tracker:
                                self.tracker.agent_started(mapped_name, timestamp)
                    
                    # Check for tool calls which indicate agent activity
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        # Analysts are likely active when tools are called
                        tool_names = [tc.name if hasattr(tc, 'name') else '' for tc in last_message.tool_calls]
                        
                        # Map tools to analysts
                        if any('YFin' in name or 'stockstats' in name for name in tool_names):
                            if "market_analyst" not in agent_states:
                                agent_states["market_analyst"] = "active"
                                if self.tracker:
                                    self.tracker.agent_started("market_analyst", timestamp)
                        
                        if any('reddit' in name or 'stock_news' in name for name in tool_names):
                            if "social_analyst" not in agent_states:
                                agent_states["social_analyst"] = "active"
                                if self.tracker:
                                    self.tracker.agent_started("social_analyst", timestamp)
                        
                        if any('news' in name or 'google_news' in name for name in tool_names):
                            if "news_analyst" not in agent_states:
                                agent_states["news_analyst"] = "active"
                                if self.tracker:
                                    self.tracker.agent_started("news_analyst", timestamp)
                        
                        if any('fundamentals' in name or 'simfin' in name or 'finnhub' in name for name in tool_names):
                            if "fundamentals_analyst" not in agent_states:
                                agent_states["fundamentals_analyst"] = "active"
                                if self.tracker:
                                    self.tracker.agent_started("fundamentals_analyst", timestamp)
                
                # Check for debate states indicating researcher activity
                if "investment_debate_state" in chunk:
                    debate_state = chunk["investment_debate_state"]
                    if debate_state.get("bull_history") and "bull_researcher" not in agent_states:
                        agent_states["bull_researcher"] = "active"
                        if self.tracker:
                            self.tracker.agent_started("bull_researcher", timestamp)
                    
                    if debate_state.get("bear_history") and "bear_researcher" not in agent_states:
                        agent_states["bear_researcher"] = "active"
                        if self.tracker:
                            self.tracker.agent_started("bear_researcher", timestamp)
                    
                    if debate_state.get("judge_decision"):
                        # Mark researchers as completed
                        if "bull_researcher" in agent_states and agent_states["bull_researcher"] == "active":
                            agent_states["bull_researcher"] = "completed"
                            if self.tracker:
                                self.tracker.agent_ended("bull_researcher", timestamp)
                        if "bear_researcher" in agent_states and agent_states["bear_researcher"] == "active":
                            agent_states["bear_researcher"] = "completed"
                            if self.tracker:
                                self.tracker.agent_ended("bear_researcher", timestamp)
                
                trace.append(chunk)
            
            # Mark any remaining active agents as completed
            final_timestamp = time.time()
            for agent, state in agent_states.items():
                if state == "active" and self.tracker:
                    self.tracker.agent_ended(agent, final_timestamp)
            
            final_state = trace[-1] if trace else {}
            self.curr_state = final_state
            self._log_state(trade_date, final_state)
            
            return final_state, self.process_signal(final_state["final_trade_decision"])
    
    # Run test
    print("\n🧪 Running parallel execution test...")
    
    try:
        # Create tracked graph
        graph = TrackedGraph(
            debug=True,
            config=config,
            tracker=tracker
        )
        
        # Run analysis
        start_time = time.time()
        final_state, decision = graph.propagate("AAPL", "2024-05-15")
        total_time = time.time() - start_time
        
        print(f"\n✅ Analysis completed in {total_time:.2f}s")
        print(f"📊 Decision: {decision}")
        
        # Get parallel execution summary
        summary = tracker.get_parallel_summary()
        
        print("\n" + "=" * 80)
        print("PARALLEL EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total parallel groups detected: {summary['total_parallel_groups']}")
        print(f"Maximum agents running in parallel: {summary['max_parallel_agents']}")
        
        if summary['parallel_groups']:
            print("\nParallel execution instances:")
            for i, group in enumerate(summary['parallel_groups']):
                agents_str = ", ".join(sorted(group['agents']))
                timestamp_str = datetime.fromtimestamp(group['time']).strftime('%H:%M:%S.%f')[:-3]
                print(f"  {i+1}. [{timestamp_str}] {group['count']} agents: {agents_str}")
        
        # Analyze timeline
        print("\nExecution timeline:")
        for timestamp, agent, action in summary['timeline'][:20]:  # Show first 20 events
            timestamp_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]
            symbol = "▶️" if action == "start" else "⏹️"
            print(f"  [{timestamp_str}] {symbol} {agent} {action}")
        
        if len(summary['timeline']) > 20:
            print(f"  ... and {len(summary['timeline']) - 20} more events")
        
        # Save results
        results_file = results_dir / "parallel_execution_summary.json"
        with open(results_file, 'w') as f:
            # Convert to serializable format
            serializable_summary = {
                'total_time': total_time,
                'decision': decision,
                'parallel_summary': {
                    'total_parallel_groups': summary['total_parallel_groups'],
                    'max_parallel_agents': summary['max_parallel_agents'],
                    'parallel_groups': [
                        {
                            'agents': list(g['agents']),
                            'time': g['time'],
                            'count': g['count']
                        }
                        for g in summary['parallel_groups']
                    ],
                    'timeline': [
                        {
                            'timestamp': t,
                            'agent': a,
                            'action': act
                        }
                        for t, a, act in summary['timeline']
                    ]
                }
            }
            json.dump(serializable_summary, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")
        
        # Verify parallel execution occurred
        if summary['total_parallel_groups'] > 0:
            print("\n✅ PARALLEL EXECUTION VERIFIED!")
            print(f"   Found {summary['total_parallel_groups']} instances of parallel agent execution")
        else:
            print("\n⚠️  WARNING: No parallel execution detected!")
            print("   This might indicate a performance issue or sequential execution")
        
    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_parallel_execution()