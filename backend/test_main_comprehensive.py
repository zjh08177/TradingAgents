#!/usr/bin/env python
"""
Comprehensive test for main.py - Tests all agents, parallel execution, and continuous logging
"""
import time
import json
import threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import sys

# Import trading components
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG


class TestLogger:
    """Enhanced logger for tracking agent execution"""
    def __init__(self):
        self.agent_times = defaultdict(list)
        self.parallel_executions = []
        self.current_agents = set()
        self.lock = threading.Lock()
        self.log_file = f"test_results/main_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        Path("test_results").mkdir(exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Also write to file
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def track_agent_start(self, agent_name):
        """Track when an agent starts"""
        with self.lock:
            start_time = time.time()
            self.agent_times[agent_name].append({'start': start_time})
            self.current_agents.add(agent_name)
            
            # Check for parallel execution
            if len(self.current_agents) > 1:
                parallel_agents = list(self.current_agents)
                self.parallel_executions.append({
                    'agents': parallel_agents,
                    'time': start_time
                })
                self.log(f"🔄 PARALLEL EXECUTION DETECTED: {parallel_agents}", "PARALLEL")
    
    def track_agent_end(self, agent_name):
        """Track when an agent ends"""
        with self.lock:
            if agent_name in self.current_agents:
                self.current_agents.remove(agent_name)
                if self.agent_times[agent_name]:
                    self.agent_times[agent_name][-1]['end'] = time.time()
                    duration = self.agent_times[agent_name][-1]['end'] - self.agent_times[agent_name][-1]['start']
                    self.log(f"✅ Agent '{agent_name}' completed in {duration:.2f}s", "COMPLETE")
    
    def print_summary(self):
        """Print execution summary"""
        self.log("\n" + "="*80, "SUMMARY")
        self.log("EXECUTION SUMMARY", "SUMMARY")
        self.log("="*80, "SUMMARY")
        
        # Agent execution times
        self.log("\n📊 Agent Execution Times:", "SUMMARY")
        for agent, times in self.agent_times.items():
            for i, t in enumerate(times):
                if 'end' in t:
                    duration = t['end'] - t['start']
                    self.log(f"  - {agent} (run {i+1}): {duration:.2f}s", "SUMMARY")
                else:
                    self.log(f"  - {agent} (run {i+1}): INCOMPLETE", "SUMMARY")
        
        # Parallel executions
        self.log(f"\n🔄 Parallel Executions Detected: {len(self.parallel_executions)}", "SUMMARY")
        for i, parallel in enumerate(self.parallel_executions):
            self.log(f"  - Instance {i+1}: {parallel['agents']}", "SUMMARY")
        
        self.log(f"\n📁 Full log saved to: {self.log_file}", "SUMMARY")


def test_main_comprehensive():
    """Comprehensive test of main.py with enhanced logging"""
    logger = TestLogger()
    
    logger.log("🚀 Starting Comprehensive TradingAgents Main Test", "START")
    logger.log(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "START")
    logger.log("-" * 80)
    
    try:
        # Test configuration
        test_configs = [
            {
                "name": "Default Google Config",
                "ticker": "NVDA",
                "date": "2024-05-10",
                "config": {
                    "llm_provider": "google",
                    "backend_url": "https://generativelanguage.googleapis.com/v1",
                    "deep_think_llm": "gemini-2.0-flash",
                    "quick_think_llm": "gemini-2.0-flash",
                    "max_debate_rounds": 1,
                    "online_tools": True
                }
            },
            {
                "name": "Multiple Debate Rounds",
                "ticker": "AAPL",
                "date": "2024-05-15",
                "config": {
                    "llm_provider": "google",
                    "backend_url": "https://generativelanguage.googleapis.com/v1",
                    "deep_think_llm": "gemini-2.0-flash",
                    "quick_think_llm": "gemini-2.0-flash",
                    "max_debate_rounds": 3,
                    "online_tools": True
                }
            }
        ]
        
        # Test each configuration
        for test_idx, test_case in enumerate(test_configs):
            logger.log(f"\n{'='*80}", "TEST")
            logger.log(f"TEST CASE {test_idx + 1}: {test_case['name']}", "TEST")
            logger.log(f"Ticker: {test_case['ticker']}, Date: {test_case['date']}", "TEST")
            logger.log(f"Config: {json.dumps(test_case['config'], indent=2)}", "TEST")
            logger.log("="*80, "TEST")
            
            # Create custom config
            config = DEFAULT_CONFIG.copy()
            config.update(test_case['config'])
            
            # Initialize TradingAgentsGraph with debug mode
            logger.log("🔧 Initializing TradingAgentsGraph...", "INIT")
            start_time = time.time()
            
            # Create custom graph with message tracking
            class TrackedTradingAgentsGraph(TradingAgentsGraph):
                def __init__(self, *args, logger=None, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.logger = logger
                    self.message_count = 0
                    
                def propagate(self, company_name, trade_date):
                    """Enhanced propagate with detailed tracking"""
                    self.ticker = company_name
                    
                    # Initialize state
                    init_agent_state = self.propagator.create_initial_state(
                        company_name, trade_date
                    )
                    args = self.propagator.get_graph_args()
                    
                    if self.logger:
                        self.logger.log(f"📊 Initial state created for {company_name} on {trade_date}", "STATE")
                    
                    # Track execution with enhanced logging
                    trace = []
                    agent_stack = []
                    
                    for chunk_idx, chunk in enumerate(self.graph.stream(init_agent_state, **args)):
                        self.message_count += 1
                        
                        # Log chunk details
                        if self.logger:
                            chunk_keys = list(chunk.keys()) if chunk else []
                            self.logger.log(f"📦 Chunk {chunk_idx + 1}: Keys = {chunk_keys}", "CHUNK")
                        
                        # Track messages and agents
                        if len(chunk.get("messages", [])) > 0:
                            last_message = chunk["messages"][-1]
                            
                            # Extract agent information
                            agent_name = None
                            if hasattr(last_message, 'name'):
                                agent_name = last_message.name
                            elif hasattr(last_message, 'additional_kwargs'):
                                agent_name = last_message.additional_kwargs.get('name')
                            
                            if agent_name and self.logger:
                                self.logger.log(f"🤖 Agent Active: {agent_name}", "AGENT")
                                self.logger.track_agent_start(agent_name)
                                agent_stack.append(agent_name)
                            
                            # Track tool calls
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                for tool_call in last_message.tool_calls:
                                    if self.logger:
                                        tool_name = tool_call.name if hasattr(tool_call, 'name') else 'Unknown'
                                        self.logger.log(f"🔧 Tool Called: {tool_name}", "TOOL")
                            
                            # Log content preview
                            if hasattr(last_message, "content") and self.logger:
                                content_preview = str(last_message.content)[:200]
                                self.logger.log(f"💬 Content Preview: {content_preview}...", "CONTENT")
                        
                        # Track report completions
                        report_types = ['market_report', 'sentiment_report', 'news_report', 
                                      'fundamentals_report', 'investment_plan', 'trader_investment_plan',
                                      'final_trade_decision']
                        
                        for report in report_types:
                            if report in chunk and chunk[report]:
                                if self.logger:
                                    self.logger.log(f"📄 {report.upper()} COMPLETED", "REPORT")
                                    # Mark previous agents as complete
                                    while agent_stack:
                                        completed_agent = agent_stack.pop()
                                        self.logger.track_agent_end(completed_agent)
                        
                        trace.append(chunk)
                    
                    # Mark any remaining agents as complete
                    while agent_stack and self.logger:
                        completed_agent = agent_stack.pop()
                        self.logger.track_agent_end(completed_agent)
                    
                    final_state = trace[-1] if trace else {}
                    
                    # Store current state for reflection
                    self.curr_state = final_state
                    
                    # Log state
                    self._log_state(trade_date, final_state)
                    
                    if self.logger:
                        self.logger.log(f"📊 Total messages processed: {self.message_count}", "STATS")
                    
                    # Return decision and processed signal
                    return final_state, self.process_signal(final_state["final_trade_decision"])
            
            # Create tracked graph
            ta = TrackedTradingAgentsGraph(
                debug=True,
                config=config,
                logger=logger
            )
            
            init_time = time.time() - start_time
            logger.log(f"✅ Graph initialized in {init_time:.2f}s", "INIT")
            
            # Run propagation
            logger.log(f"\n🔄 Starting propagation for {test_case['ticker']}...", "PROPAGATE")
            prop_start = time.time()
            
            try:
                final_state, decision = ta.propagate(test_case['ticker'], test_case['date'])
                
                prop_time = time.time() - prop_start
                logger.log(f"\n✅ Propagation completed in {prop_time:.2f}s", "COMPLETE")
                logger.log(f"📊 Final Decision: {decision}", "RESULT")
                
                # Validate results
                logger.log("\n🔍 Validating Results:", "VALIDATE")
                required_fields = ['market_report', 'sentiment_report', 'news_report', 
                                 'fundamentals_report', 'investment_plan', 'final_trade_decision']
                
                missing_fields = []
                for field in required_fields:
                    if field not in final_state or not final_state[field]:
                        missing_fields.append(field)
                        logger.log(f"  ❌ Missing: {field}", "VALIDATE")
                    else:
                        logger.log(f"  ✅ Present: {field} ({len(str(final_state[field]))} chars)", "VALIDATE")
                
                if missing_fields:
                    logger.log(f"\n⚠️  WARNING: Missing fields: {missing_fields}", "WARNING")
                else:
                    logger.log("\n✅ All required fields present!", "SUCCESS")
                
                # Save results
                results_dir = Path(f"test_results/test_case_{test_idx + 1}")
                results_dir.mkdir(parents=True, exist_ok=True)
                
                with open(results_dir / "final_state.json", 'w') as f:
                    # Convert to serializable format
                    serializable_state = {
                        k: str(v) if v else None 
                        for k, v in final_state.items()
                    }
                    json.dump(serializable_state, f, indent=2)
                
                logger.log(f"\n📁 Results saved to: {results_dir}", "SAVE")
                
            except Exception as e:
                logger.log(f"\n❌ Error during propagation: {str(e)}", "ERROR")
                import traceback
                logger.log(f"Traceback:\n{traceback.format_exc()}", "ERROR")
                
        # Print summary
        logger.print_summary()
        
    except Exception as e:
        logger.log(f"\n💥 Fatal error: {str(e)}", "FATAL")
        import traceback
        logger.log(f"Traceback:\n{traceback.format_exc()}", "FATAL")
        logger.print_summary()
        sys.exit(1)


if __name__ == "__main__":
    test_main_comprehensive()