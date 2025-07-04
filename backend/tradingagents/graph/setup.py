# TradingAgents/graph/setup.py

from typing import Dict, Any, List, Set, Tuple
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage
import logging
import hashlib
import json

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import Toolkit

from .conditional_logic import ConditionalLogic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolCallTracker:
    """Tracks tool calls per analyst to enforce limits and prevent duplicates."""
    
    def __init__(self):
        self.call_history = {}  # analyst_type -> {tool_name: [(params_hash, params_str)]}
        self.call_counts = {}   # analyst_type -> {tool_name: count}
        self.max_total_calls = 3  # Maximum total tool calls per analyst
        self.total_calls = {}  # analyst_type -> total_count
    
    def _hash_params(self, params: dict) -> str:
        """Create a hash of parameters for comparison."""
        # Sort keys for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()
    
    def can_call_tool(self, analyst_type: str, tool_name: str, params: dict) -> Tuple[bool, str]:
        """Check if a tool can be called with given parameters."""
        if analyst_type not in self.call_history:
            self.call_history[analyst_type] = {}
            self.call_counts[analyst_type] = {}
            self.total_calls[analyst_type] = 0
        
        # Check total call limit for this analyst
        if self.total_calls[analyst_type] >= self.max_total_calls:
            return False, f"Analyst {analyst_type} has reached maximum total tool calls ({self.max_total_calls})"
        
        # Initialize tool tracking if first time
        if tool_name not in self.call_history[analyst_type]:
            self.call_history[analyst_type][tool_name] = []
            self.call_counts[analyst_type][tool_name] = 0
        
        # Check for duplicate parameters
        param_hash = self._hash_params(params)
        param_str = json.dumps(params, sort_keys=True)
        
        for existing_hash, existing_params in self.call_history[analyst_type][tool_name]:
            if param_hash == existing_hash:
                return False, f"Tool {tool_name} already called with identical parameters: {existing_params}"
        
        return True, "OK"
    
    def record_tool_call(self, analyst_type: str, tool_name: str, params: dict):
        """Record a successful tool call."""
        if analyst_type not in self.call_history:
            self.call_history[analyst_type] = {}
            self.call_counts[analyst_type] = {}
            self.total_calls[analyst_type] = 0
        
        if tool_name not in self.call_history[analyst_type]:
            self.call_history[analyst_type][tool_name] = []
            self.call_counts[analyst_type][tool_name] = 0
        
        param_hash = self._hash_params(params)
        param_str = json.dumps(params, sort_keys=True)
        
        self.call_history[analyst_type][tool_name].append((param_hash, param_str))
        self.call_counts[analyst_type][tool_name] += 1
        self.total_calls[analyst_type] += 1
        
        logger.info(f"🔧 Recorded tool call: {analyst_type}/{tool_name} (total calls: {self.total_calls[analyst_type]})")


class GraphSetup:
    """Handles the setup and configuration of the agent graph with parallel analyst execution."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        toolkit: Toolkit,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic
        
        # Initialize tool call tracker
        self.tool_tracker = ToolCallTracker()
        
        # Track report completions to prevent duplicates
        self.completed_reports = set()

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals"]
    ):
        """Set up and compile the agent workflow graph with parallel analyst execution."""
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        logger.info(f"🚀 Setting up parallel graph with analysts: {selected_analysts}")

        # Create main workflow
        workflow = StateGraph(AgentState)

        # Add dispatcher node
        logger.info("📋 Adding Dispatcher node")
        workflow.add_node("Dispatcher", self._create_dispatcher())

        # Add individual analyst and tool nodes for parallel execution
        for analyst_type in selected_analysts:
            logger.info(f"🔧 Adding {analyst_type} analyst nodes")
            
            # Create analyst and tool nodes
            if analyst_type == "market":
                analyst_node = create_market_analyst(self.quick_thinking_llm, self.toolkit)
                tool_node = self.tool_nodes["market"]
                message_key = "market_messages"
                report_key = "market_report"
            elif analyst_type == "social":
                analyst_node = create_social_media_analyst(self.quick_thinking_llm, self.toolkit)
                tool_node = self.tool_nodes["social"]
                message_key = "social_messages"
                report_key = "sentiment_report"
            elif analyst_type == "news":
                analyst_node = create_news_analyst(self.quick_thinking_llm, self.toolkit)
                tool_node = self.tool_nodes["news"]
                message_key = "news_messages"
                report_key = "news_report"
            elif analyst_type == "fundamentals":
                analyst_node = create_fundamentals_analyst(self.quick_thinking_llm, self.toolkit)
                tool_node = self.tool_nodes["fundamentals"]
                message_key = "fundamentals_messages"
                report_key = "fundamentals_report"
            else:
                raise ValueError(f"Unknown analyst type: {analyst_type}")

            # Wrap nodes for specific message channels
            wrapped_analyst = self._wrap_analyst_for_channel(
                analyst_node, message_key, report_key, analyst_type
            )
            wrapped_tool_node = self._wrap_tool_node_for_channel(
                tool_node, message_key, analyst_type
            )
            
            # Add nodes to main workflow
            workflow.add_node(f"{analyst_type}_analyst", wrapped_analyst)
            workflow.add_node(f"{analyst_type}_tools", wrapped_tool_node)

        # Add aggregator node
        logger.info("📊 Adding Aggregator node")
        workflow.add_node("Aggregator", self._create_aggregator())

        # Create researcher and manager nodes
        bull_researcher_node = create_bull_researcher(
            self.quick_thinking_llm, self.bull_memory
        )
        bear_researcher_node = create_bear_researcher(
            self.quick_thinking_llm, self.bear_memory
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes - wrapped for parallel execution
        risky_analyst_node = create_risky_debator(self.quick_thinking_llm)
        neutral_analyst_node = create_neutral_debator(self.quick_thinking_llm)
        safe_analyst_node = create_safe_debator(self.quick_thinking_llm)
        risk_manager_node = create_risk_manager(
            self.deep_thinking_llm, self.risk_manager_memory
        )

        # Wrap risk analysts for parallel execution
        wrapped_risky_analyst = self._wrap_risk_analyst_for_channel(risky_analyst_node, "risky")
        wrapped_safe_analyst = self._wrap_risk_analyst_for_channel(safe_analyst_node, "safe") 
        wrapped_neutral_analyst = self._wrap_risk_analyst_for_channel(neutral_analyst_node, "neutral")

        # Add remaining nodes
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        
        # Add Risk Dispatcher and Aggregator for parallel risk execution
        workflow.add_node("Risk Dispatcher", self._create_risk_dispatcher())
        workflow.add_node("Risky Analyst", wrapped_risky_analyst)
        workflow.add_node("Safe Analyst", wrapped_safe_analyst)
        workflow.add_node("Neutral Analyst", wrapped_neutral_analyst)
        workflow.add_node("Risk Aggregator", self._create_risk_aggregator())
        workflow.add_node("Risk Judge", risk_manager_node)

        # Define edges for parallel execution
        logger.info("🔗 Setting up graph edges for parallel execution")
        
        # Start with dispatcher
        workflow.add_edge(START, "Dispatcher")
        
        # From dispatcher, go to all analysts in parallel
        for analyst_type in selected_analysts:
            workflow.add_edge("Dispatcher", f"{analyst_type}_analyst")
        
        # Set up analyst -> tools -> completion routing
        for analyst_type in selected_analysts:
            # Define conditional logic for each analyst
            def create_analyst_conditional(atype):
                def should_continue_analyst(state: AgentState) -> str:
                    message_key = f"{atype}_messages"
                    report_key_map = {
                        "market": "market_report",
                        "social": "sentiment_report", 
                        "news": "news_report",
                        "fundamentals": "fundamentals_report"
                    }
                    report_key = report_key_map.get(atype, f"{atype}_report")
                    
                    messages = state.get(message_key, [])
                    report = state.get(report_key, "")
                    
                    # If report exists or too many messages, go to aggregator
                    if report or len(messages) > 6:
                        return "aggregator"
                    
                    if not messages:
                        return "aggregator"
                    
                    last_message = messages[-1]
                    
                    # Check for tool calls
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        # Check if we've already hit the tool call limit
                        total_calls = self.tool_tracker.total_calls.get(atype, 0)
                        if total_calls >= self.tool_tracker.max_total_calls:
                            logger.warning(f"  - Decision: AGGREGATOR (tool call limit reached: {total_calls})")
                            return "aggregator"
                        return "tools"
                    
                    return "aggregator"
                return should_continue_analyst
            
            # Define conditional logic for tools
            def create_tool_conditional(atype):
                def should_continue_after_tools(state: AgentState) -> str:
                    message_key = f"{atype}_messages"
                    messages = state.get(message_key, [])
                    
                    # Check total tool calls
                    total_calls = self.tool_tracker.total_calls.get(atype, 0)
                    if total_calls >= self.tool_tracker.max_total_calls:
                        return "aggregator"
                    
                    # If we have enough messages, likely complete
                    if len(messages) >= 6:
                        return "aggregator"
                    
                    # Otherwise, go back to analyst
                    return "analyst"
                return should_continue_after_tools
            
            # Add conditional edges for each analyst
            workflow.add_conditional_edges(
                f"{analyst_type}_analyst",
                create_analyst_conditional(analyst_type),
                {
                    "tools": f"{analyst_type}_tools",
                    "aggregator": "Aggregator"
                }
            )
            
            # Add conditional edges for tools
            workflow.add_conditional_edges(
                f"{analyst_type}_tools",
                create_tool_conditional(analyst_type),
                {
                    "analyst": f"{analyst_type}_analyst",
                    "aggregator": "Aggregator"
                }
            )

        # Aggregator continues to Bull Researcher
        workflow.add_edge("Aggregator", "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risk Dispatcher")
        
        # Parallel risk analyst execution
        workflow.add_edge("Risk Dispatcher", "Risky Analyst")
        workflow.add_edge("Risk Dispatcher", "Safe Analyst")
        workflow.add_edge("Risk Dispatcher", "Neutral Analyst")
        
        # All risk analysts go to aggregator
        workflow.add_edge("Risky Analyst", "Risk Aggregator")
        workflow.add_edge("Safe Analyst", "Risk Aggregator")
        workflow.add_edge("Neutral Analyst", "Risk Aggregator")
        
        # Aggregator goes to Risk Judge for final decision
        workflow.add_edge("Risk Aggregator", "Risk Judge")
        workflow.add_edge("Risk Judge", END)

        # Compile and return
        logger.info("✅ Graph setup complete, compiling...")
        return workflow.compile()

    def _create_dispatcher(self):
        """Create dispatcher node that initializes message channels for each analyst."""
        
        def dispatch(state: AgentState) -> dict:
            logger.info("=" * 80)
            logger.info("📋 NODE EXECUTING: DISPATCHER")
            logger.info("=" * 80)
            
            company = state.get("company_of_interest", "Unknown")
            date = state.get("trade_date", "Unknown")
            
            logger.info(f"📋 Dispatcher: Starting parallel analysis for {company} on {date}")
            
            # Initialize message channels with initial messages
            initial_message = f"Analyze {company} on {date}"
            
            update = {
                "market_messages": [HumanMessage(content=initial_message)],
                "social_messages": [HumanMessage(content=initial_message)],
                "news_messages": [HumanMessage(content=initial_message)],
                "fundamentals_messages": [HumanMessage(content=initial_message)]
            }
            
            logger.info("📋 Dispatcher: Initialized all analyst message channels")
            logger.info("📋 Dispatcher: Starting Market, Social, News, and Fundamentals analysts in parallel")
            logger.info("✅ DISPATCHER COMPLETE")
            
            return update
        
        return dispatch

    def _wrap_analyst_for_channel(self, analyst_node, message_key: str, report_key: str, analyst_type: str):
        """Wrap an analyst node to work with a specific message channel."""
        
        def wrapped_analyst(state: AgentState) -> dict:
            logger.info("-" * 60)
            logger.info(f"🧠 NODE EXECUTING: {analyst_type.upper()} ANALYST")
            logger.info("-" * 60)
            
            # Check if report already exists - prevent duplicate completion
            existing_report = state.get(report_key, "")
            if existing_report:
                logger.info(f"🧠 {analyst_type} analyst: ✅ REPORT ALREADY EXISTS - skipping")
                # Check if this report was already marked as completed
                report_id = f"{analyst_type}_report_completed"
                if report_id not in self.completed_reports:
                    self.completed_reports.add(report_id)
                    logger.info(f"🧠 {analyst_type} analyst: First time seeing completed report, allowing one update")
                else:
                    logger.info(f"🧠 {analyst_type} analyst: Report already marked as completed, skipping all updates")
                    return {}
                return {message_key: state.get(message_key, [])}
            
            # Get the analyst's messages
            messages = state.get(message_key, [])
            logger.info(f"🧠 {analyst_type} analyst: Processing {len(messages)} messages")
            
            # Create a temporary state with the analyst's messages
            temp_state = state.copy()
            temp_state["messages"] = messages
            
            try:
                # Run the original analyst
                logger.info(f"🧠 {analyst_type} analyst: Invoking LLM...")
                result = analyst_node(temp_state)
                logger.info(f"🧠 {analyst_type} analyst: LLM response received")
                
                # Extract the updated messages
                updated_messages = result.get("messages", messages)
                logger.info(f"🧠 {analyst_type} analyst: Updated from {len(messages)} to {len(updated_messages)} messages")
                
                # Check if this is a final response
                report = ""
                if updated_messages:
                    last_message = updated_messages[-1]
                    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
                    has_content = hasattr(last_message, 'content') and last_message.content
                    
                    # Count tool messages
                    tool_result_count = sum(1 for msg in updated_messages 
                                          if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool')
                    
                    # Generate report if no tool calls and has content
                    if has_content and not has_tool_calls:
                        content = str(last_message.content)
                        # Only consider it a report if it has substantial content
                        if len(content) > 200 or (tool_result_count > 0 and len(content) > 50):
                            report = content
                            logger.info(f"🧠 {analyst_type} analyst: ✅ FINAL REPORT GENERATED ({len(content)} chars)")
                
                # Return updates
                update = {message_key: updated_messages}
                if report:
                    update[report_key] = report
                    # Mark this report as completed
                    self.completed_reports.add(f"{analyst_type}_report_completed")
                    logger.info(f"🧠 {analyst_type} analyst: ✅ SETTING {report_key}")
                
                logger.info(f"✅ {analyst_type.upper()} ANALYST COMPLETE")
                return update
                
            except Exception as e:
                logger.error(f"❌ {analyst_type} analyst error: {str(e)}")
                raise
        
        return wrapped_analyst

    def _wrap_tool_node_for_channel(self, tool_node, message_key: str, analyst_type: str):
        """Wrap a tool node to work with a specific message channel with tool call limits."""
        
        def wrapped_tool_node(state: AgentState) -> dict:
            logger.info("-" * 60)
            logger.info(f"🔧 NODE EXECUTING: {analyst_type.upper()} TOOLS")
            logger.info("-" * 60)
            
            # Get the analyst's messages
            messages = state.get(message_key, [])
            logger.info(f"🔧 {analyst_type} tools: Processing {len(messages)} messages")
            
            if not messages:
                logger.error(f"❌ {analyst_type} tools: No messages found")
                return {message_key: messages}
            
            last_msg = messages[-1]
            logger.info(f"🔧 {analyst_type} tools: Last message type: {type(last_msg).__name__}")
            
            if not (hasattr(last_msg, 'tool_calls') and last_msg.tool_calls):
                logger.error(f"❌ {analyst_type} tools: No tool calls found")
                return {message_key: messages}
            
            logger.info(f"🔧 {analyst_type} tools: Found {len(last_msg.tool_calls)} tool calls")
            
            # Process each tool call
            updated_messages = list(messages)
            tools_executed = 0
            
            for i, tool_call in enumerate(last_msg.tool_calls):
                try:
                    # Get tool call details
                    if hasattr(tool_call, 'name'):
                        tool_name = tool_call.name
                        tool_args = tool_call.args if hasattr(tool_call, 'args') else {}
                        tool_call_id = tool_call.id if hasattr(tool_call, 'id') else 'unknown'
                    else:
                        logger.error(f"❌ {analyst_type} tools: Unknown tool call format")
                        continue
                    
                    # Check if the tool can be called
                    can_call, reason = self.tool_tracker.can_call_tool(analyst_type, tool_name, tool_args)
                    if not can_call:
                        logger.warning(f"🔧 {analyst_type} tools: SKIPPING - {reason}")
                        continue
                    
                    logger.info(f"🔧 {analyst_type} tools: [{i+1}/{len(last_msg.tool_calls)}] Executing {tool_name}")
                    
                    # Find and execute the tool
                    tool_result = None
                    for tool_func in tool_node.tools_by_name.values():
                        if tool_func.name == tool_name:
                            tool_result = tool_func.invoke(tool_args)
                            break
                    
                    if tool_result is None:
                        logger.error(f"❌ {analyst_type} tools: Tool {tool_name} not found")
                        tool_result = f"Error: Tool {tool_name} not found"
                    
                    # Create ToolMessage
                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id
                    )
                    
                    updated_messages.append(tool_message)
                    logger.info(f"🔧 {analyst_type} tools: ✅ Added ToolMessage for {tool_name}")
                    
                    # Record the tool call
                    self.tool_tracker.record_tool_call(analyst_type, tool_name, tool_args)
                    tools_executed += 1
                    
                except Exception as e:
                    logger.error(f"❌ {analyst_type} tools: Error executing {tool_name}: {str(e)}")
            
            logger.info(f"🔧 {analyst_type} tools: Executed {tools_executed} tools")
            logger.info(f"🔧 {analyst_type} tools: Total calls for {analyst_type}: {self.tool_tracker.total_calls.get(analyst_type, 0)}")
            
            # Return updates
            update = {message_key: updated_messages}
            logger.info(f"✅ {analyst_type.upper()} TOOLS COMPLETE")
            return update
        
        return wrapped_tool_node

    def _create_aggregator(self):
        """Create aggregator node that validates all analyst reports are complete."""
        
        def aggregate(state: AgentState) -> dict:
            logger.info("=" * 80)
            logger.info("📊 NODE EXECUTING: AGGREGATOR")
            logger.info("=" * 80)
            
            # Check that all expected reports are present
            reports = {
                "market_report": state.get("market_report", ""),
                "sentiment_report": state.get("sentiment_report", ""),
                "news_report": state.get("news_report", ""),
                "fundamentals_report": state.get("fundamentals_report", "")
            }
            
            logger.info("📊 Aggregator: Checking report status:")
            for report_name, report_content in reports.items():
                status = "✅ PRESENT" if report_content.strip() else "❌ MISSING"
                length = len(report_content) if report_content else 0
                logger.info(f"  - {report_name}: {status} ({length} chars)")
            
            completed_reports = [name for name, report in reports.items() if report.strip()]
            missing_reports = [name for name, report in reports.items() if not report.strip()]
            
            logger.info(f"📊 Aggregator: ✅ Completed reports: {completed_reports}")
            if missing_reports:
                logger.warning(f"📊 Aggregator: ❌ Missing reports: {missing_reports}")
            
            # Initialize debate states
            initial_investment_debate = {
                "bull_history": "",
                "bear_history": "",
                "history": "",
                "current_response": "",
                "judge_decision": "",
                "count": 0
            }
            
            initial_risk_debate = {
                "risky_history": "",
                "safe_history": "",
                "neutral_history": "",
                "history": "",
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
                "count": 0
            }
            
            logger.info("📊 Aggregator: Marking analysis phase as complete")
            logger.info("✅ AGGREGATOR COMPLETE")
            
            return {
                "analysis_complete": True,
                "investment_debate_state": initial_investment_debate,
                "risk_debate_state": initial_risk_debate
            }
        
        return aggregate

    def _wrap_risk_analyst_for_channel(self, risk_analyst_node, analyst_type: str):
        """Wrap a risk analyst node to work with risk debate state."""
        
        def wrapped_risk_analyst(state: AgentState) -> dict:
            logger.info("-" * 60)
            logger.info(f"⚡ NODE EXECUTING: {analyst_type.upper()} RISK ANALYST")
            logger.info("-" * 60)
            
            try:
                # Run the original risk analyst
                logger.info(f"⚡ {analyst_type} risk analyst: Invoking LLM...")
                result = risk_analyst_node(state)
                logger.info(f"⚡ {analyst_type} risk analyst: LLM response received")
                
                # Extract the risk debate state update
                risk_debate_state = result.get("risk_debate_state", state.get("risk_debate_state", {}))
                
                # Update the appropriate response field
                response_key = f"current_{analyst_type}_response"
                if response_key in risk_debate_state:
                    logger.info(f"⚡ {analyst_type} risk analyst: ✅ Analysis complete")
                    logger.info(f"⚡ {analyst_type} risk analyst: Response length: {len(risk_debate_state[response_key])} chars")
                
                logger.info(f"✅ {analyst_type.upper()} RISK ANALYST COMPLETE")
                return {"risk_debate_state": risk_debate_state}
                
            except Exception as e:
                logger.error(f"❌ {analyst_type} risk analyst error: {str(e)}")
                raise
        
        return wrapped_risk_analyst

    def _create_risk_dispatcher(self):
        """Create risk dispatcher node that initializes risk analysis phase."""
        
        def dispatch_risk(state: AgentState) -> dict:
            logger.info("=" * 80)
            logger.info("⚡ NODE EXECUTING: RISK DISPATCHER")
            logger.info("=" * 80)
            
            # Initialize risk debate state if not present
            risk_debate_state = state.get("risk_debate_state", {})
            
            # Ensure all required fields are initialized
            initial_risk_debate = {
                "risky_history": risk_debate_state.get("risky_history", ""),
                "safe_history": risk_debate_state.get("safe_history", ""),
                "neutral_history": risk_debate_state.get("neutral_history", ""),
                "history": risk_debate_state.get("history", ""),
                "latest_speaker": "",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "judge_decision": "",
                "count": 0
            }
            
            logger.info("⚡ Risk Dispatcher: Initializing parallel risk analysis")
            logger.info("⚡ Risk Dispatcher: Starting Risky, Safe, and Neutral analysts in parallel")
            logger.info("✅ RISK DISPATCHER COMPLETE")
            
            return {"risk_debate_state": initial_risk_debate}
        
        return dispatch_risk

    def _create_risk_aggregator(self):
        """Create risk aggregator node that collects all risk analyses."""
        
        def aggregate_risk(state: AgentState) -> dict:
            logger.info("=" * 80)
            logger.info("⚡ NODE EXECUTING: RISK AGGREGATOR")
            logger.info("=" * 80)
            
            risk_debate_state = state.get("risk_debate_state", {})
            
            # Check that all risk analyses are complete
            risky_response = risk_debate_state.get("current_risky_response", "")
            safe_response = risk_debate_state.get("current_safe_response", "")
            neutral_response = risk_debate_state.get("current_neutral_response", "")
            
            logger.info("⚡ Risk Aggregator: Checking risk analysis status:")
            logger.info(f"  - Risky analysis: {'✅ COMPLETE' if risky_response else '❌ MISSING'} ({len(risky_response)} chars)")
            logger.info(f"  - Safe analysis: {'✅ COMPLETE' if safe_response else '❌ MISSING'} ({len(safe_response)} chars)")
            logger.info(f"  - Neutral analysis: {'✅ COMPLETE' if neutral_response else '❌ MISSING'} ({len(neutral_response)} chars)")
            
            # Combine all responses for Risk Judge input
            combined_history = ""
            if risky_response:
                combined_history += f"Risky Analyst: {risky_response}\n\n"
            if safe_response:
                combined_history += f"Safe Analyst: {safe_response}\n\n"
            if neutral_response:
                combined_history += f"Neutral Analyst: {neutral_response}\n\n"
            
            # Update risk debate state with combined history
            updated_risk_state = risk_debate_state.copy()
            updated_risk_state["history"] = combined_history
            updated_risk_state["count"] = 1  # Mark as ready for judgment
            
            logger.info("⚡ Risk Aggregator: Risk analyses aggregated for final judgment")
            logger.info("✅ RISK AGGREGATOR COMPLETE")
            
            return {"risk_debate_state": updated_risk_state}
        
        return aggregate_risk
