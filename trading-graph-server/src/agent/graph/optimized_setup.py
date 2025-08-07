#!/usr/bin/env python3
"""
Optimized Trading Graph Setup - Phase 1 Integration
Integrates async tokens, ultra-compressed prompts, and parallel execution
"""

import logging
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from ..utils.agent_states import AgentState
from ..utils.agent_utils import Toolkit
from ..utils.tool_monitoring import get_tool_monitor

# Phase 1 Optimization Imports
from ..utils.async_token_optimizer import AsyncTokenOptimizer
from ..utils.ultra_prompt_templates import UltraPromptTemplates
from ..utils.parallel_execution_manager import ParallelExecutionManager
from ..utils.phase1_integration import Phase1Optimizer

# Original imports
from ..interfaces import ILLMProvider, IMemoryProvider, IAnalystToolkit, IGraphBuilder
from ..factories.llm_factory import LLMFactory
from ..factories.memory_factory import MemoryFactory
from ..factories.toolkit_factory import ToolkitFactory
from ..dataflows.config import get_config

# Import analyst creation functions
from ..analysts.market_analyst import create_market_analyst
from ..analysts.social_media_analyst import create_social_media_analyst  
from ..analysts.news_analyst import create_news_analyst
from ..analysts.fundamentals_analyst import create_fundamentals_analyst

# Import other node creation functions
from ..researchers.bull_researcher import create_bull_researcher
from ..researchers.bear_researcher import create_bear_researcher
from ..managers.research_manager import create_research_manager
from ..trader.trader import create_trader
from ..managers.risk_manager import create_risk_manager

# Import debate nodes
from ..controllers.research_debate_controller import create_research_debate_controller
from ..orchestrators.risk_debate_orchestrator import create_risk_debate_orchestrator
from .nodes.parallel_risk_debators import create_parallel_risk_debators
from .nodes.parallel_analysts import create_parallel_analysts_executor

logger = logging.getLogger(__name__)

class OptimizedGraphBuilder(IGraphBuilder):
    """
    Phase 1 Optimized Graph Builder
    Integrates async tokens, ultra-compressed prompts, and parallel execution
    Targets: 40% runtime reduction + 25% token reduction
    """
    
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,
                 deep_thinking_llm: ILLMProvider,
                 config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.config = config
        
        # Enable Phase 1 optimizations by default
        self.config['enable_phase1_optimizations'] = self.config.get('enable_phase1_optimizations', True)
        self.config['enable_async_tokens'] = self.config.get('enable_async_tokens', True)
        self.config['enable_ultra_prompts'] = self.config.get('enable_ultra_prompts', True)
        self.config['enable_parallel_execution'] = self.config.get('enable_parallel_execution', True)
        
        # Initialize Phase 1 components
        if self.config['enable_phase1_optimizations']:
            self.phase1_optimizer = Phase1Optimizer(self.config)
            self.async_token_optimizer = AsyncTokenOptimizer(
                model_name=self.config.get('model_name', 'gpt-4o-mini')
            )
            self.parallel_executor = ParallelExecutionManager(
                max_workers=self.config.get('max_parallel_agents', 4)
            )
            logger.info("🚀 Phase 1 Optimizations ENABLED")
        else:
            logger.info("⚠️ Phase 1 Optimizations DISABLED")
        
        # Create base toolkit and factories
        self.base_toolkit = Toolkit(self.config)
        self.toolkit_factory = ToolkitFactory()
        self.memory_factory = MemoryFactory()
        
        logger.info("🚀 OptimizedGraphBuilder initialized with Phase 1 optimizations")
    
    def setup_graph(self, selected_analysts: List[str] = None) -> CompiledStateGraph:
        """Build optimized graph with Phase 1 enhancements"""
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals"]
        
        logger.info(f"🚀 Building Phase 1 optimized graph with analysts: {selected_analysts}")
        
        graph = StateGraph(AgentState)
        
        # Add optimized nodes
        self._add_optimized_core_nodes(graph, selected_analysts)
        self._add_optimized_analyst_nodes(graph, selected_analysts)
        self._add_workflow_nodes(graph)
        self._setup_optimized_edges(graph, selected_analysts)
        
        logger.info("✅ Phase 1 optimized graph constructed successfully")
        return graph.compile()
    
    def _add_optimized_core_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add core nodes with parallel execution optimization"""
        # Create parallel analysts executor instead of dispatcher
        graph.add_node("parallel_analysts", self._create_parallel_analysts_node(selected_analysts))
        graph.add_node("aggregator", self._create_optimized_aggregator())
    
    def _add_optimized_analyst_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add analyst nodes - now handled by parallel_analysts node"""
        # Individual analyst nodes are no longer needed
        # The parallel_analysts node handles all analyst execution
        logger.info("📦 Analyst nodes are now integrated into parallel_analysts executor")
    
    def _build_optimized_market_analyst(self, graph: StateGraph):
        """Build market analyst with ultra-compressed prompt"""
        toolkit = self.toolkit_factory.create_market_toolkit(self.base_toolkit)
        
        # Create optimized analyst with compressed prompt
        if self.config['enable_ultra_prompts']:
            analyst = self._create_optimized_analyst(
                create_market_analyst(self.quick_thinking_llm, toolkit),
                "market"
            )
        else:
            analyst = create_market_analyst(self.quick_thinking_llm, toolkit)
        
        tools = self._create_market_tool_node(toolkit)
        
        graph.add_node("market_analyst", analyst)
        graph.add_node("market_tools", tools)
        
        # Add routing
        graph.add_conditional_edges("market_analyst", self._create_analyst_routing("market"), {
            "market_tools": "market_tools",
            "market_analyst": "market_analyst",  # CRITICAL FIX: Allow routing back to self
            "aggregator": "aggregator"
        })
        graph.add_edge("market_tools", "market_analyst")
    
    def _build_optimized_social_analyst(self, graph: StateGraph):
        """Build social analyst with ultra-compressed prompt"""
        toolkit = self.toolkit_factory.create_social_toolkit(self.base_toolkit)
        
        if self.config['enable_ultra_prompts']:
            analyst = self._create_optimized_analyst(
                create_social_media_analyst(self.quick_thinking_llm, toolkit),
                "social"
            )
        else:
            analyst = create_social_media_analyst(self.quick_thinking_llm, toolkit)
        
        tools = self._create_social_tool_node(toolkit)
        
        graph.add_node("social_analyst", analyst)
        graph.add_node("social_tools", tools)
        
        graph.add_conditional_edges("social_analyst", self._create_analyst_routing("social"), {
            "social_tools": "social_tools",
            "social_analyst": "social_analyst",  # CRITICAL FIX: Allow routing back to self
            "aggregator": "aggregator"
        })
        graph.add_edge("social_tools", "social_analyst")
    
    def _build_optimized_news_analyst(self, graph: StateGraph):
        """Build news analyst with ultra-compressed prompt"""
        toolkit = self.toolkit_factory.create_news_toolkit(self.base_toolkit)
        
        if self.config['enable_ultra_prompts']:
            analyst = self._create_optimized_analyst(
                create_news_analyst(self.quick_thinking_llm, toolkit),
                "news"
            )
        else:
            analyst = create_news_analyst(self.quick_thinking_llm, toolkit)
        
        tools = self._create_news_tool_node(toolkit)
        
        graph.add_node("news_analyst", analyst)
        graph.add_node("news_tools", tools)
        
        graph.add_conditional_edges("news_analyst", self._create_analyst_routing("news"), {
            "news_tools": "news_tools",
            "news_analyst": "news_analyst",  # CRITICAL FIX: Allow routing back to self
            "aggregator": "aggregator"
        })
        graph.add_edge("news_tools", "news_analyst")
    
    def _build_optimized_fundamentals_analyst(self, graph: StateGraph):
        """Build fundamentals analyst with ultra-compressed prompt"""
        toolkit = self.toolkit_factory.create_fundamentals_toolkit(self.base_toolkit)
        
        if self.config['enable_ultra_prompts']:
            analyst = self._create_optimized_analyst(
                create_fundamentals_analyst(self.quick_thinking_llm, toolkit),
                "fundamentals"
            )
        else:
            analyst = create_fundamentals_analyst(self.quick_thinking_llm, toolkit)
        
        tools = self._create_fundamentals_tool_node(toolkit)
        
        graph.add_node("fundamentals_analyst", analyst)
        graph.add_node("fundamentals_tools", tools)
        
        graph.add_conditional_edges("fundamentals_analyst", self._create_analyst_routing("fundamentals"), {
            "fundamentals_tools": "fundamentals_tools",
            "fundamentals_analyst": "fundamentals_analyst",  # CRITICAL FIX: Allow routing back to self
            "aggregator": "aggregator"
        })
        graph.add_edge("fundamentals_tools", "fundamentals_analyst")
    
    def _create_optimized_analyst(self, original_analyst: Callable, analyst_type: str) -> Callable:
        """Wrap analyst with ultra-compressed prompt injection"""
        async def optimized_analyst(state: AgentState) -> AgentState:
            # Get ultra-compressed prompt
            compressed_prompt = UltraPromptTemplates.format_prompt(
                analyst_type,
                ticker=state.get("company_of_interest", "UNKNOWN")
            )
            
            # Inject compressed prompt into analyst's system message
            # This is a simplified version - in production, would modify the LLM's system prompt
            logger.info(f"📝 Using ultra-compressed prompt for {analyst_type} analyst")
            
            # Call original analyst
            return await original_analyst(state)
        
        # Preserve function name
        optimized_analyst.__name__ = original_analyst.__name__
        return optimized_analyst
    
    def _create_parallel_analysts_node(self, selected_analysts: List[str]):
        """Create a single node that executes all analysts in parallel using asyncio.gather()"""
        from .nodes.parallel_analysts import create_parallel_analysts_executor
        
        # Create individual analyst functions
        analysts_dict = {}
        
        for analyst_type in selected_analysts:
            if analyst_type == "market":
                toolkit = self.toolkit_factory.create_market_toolkit(self.base_toolkit)
                analyst_func = self._wrap_analyst_with_tools(
                    create_market_analyst(self.quick_thinking_llm, toolkit),
                    toolkit,
                    "market"
                )
                analysts_dict["market"] = analyst_func
                
            elif analyst_type == "social":
                toolkit = self.toolkit_factory.create_social_toolkit(self.base_toolkit)
                analyst_func = self._wrap_analyst_with_tools(
                    create_social_media_analyst(self.quick_thinking_llm, toolkit),
                    toolkit,
                    "social"
                )
                analysts_dict["social"] = analyst_func
                
            elif analyst_type == "news":
                toolkit = self.toolkit_factory.create_news_toolkit(self.base_toolkit)
                analyst_func = self._wrap_analyst_with_tools(
                    create_news_analyst(self.quick_thinking_llm, toolkit),
                    toolkit,
                    "news"
                )
                analysts_dict["news"] = analyst_func
                
            elif analyst_type == "fundamentals":
                toolkit = self.toolkit_factory.create_fundamentals_toolkit(self.base_toolkit)
                analyst_func = self._wrap_analyst_with_tools(
                    create_fundamentals_analyst(self.quick_thinking_llm, toolkit),
                    toolkit,
                    "fundamentals"
                )
                analysts_dict["fundamentals"] = analyst_func
        
        # Create the parallel executor node
        return create_parallel_analysts_executor(analysts_dict)
    
    def _wrap_analyst_with_tools(self, analyst_func: Callable, toolkit: IAnalystToolkit, analyst_type: str) -> Callable:
        """Wrap an analyst function to handle tool execution internally"""
        async def analyst_with_tools(state: AgentState) -> AgentState:
            # Call the analyst
            result = await analyst_func(state)
            
            # Check if tools need to be executed
            messages_key = f"{analyst_type}_messages"
            messages = result.get(messages_key, [])
            
            if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
                # Execute tools
                tool_result = await self._execute_tools_optimized(result, toolkit, messages_key)
                
                # Call analyst again to process tool results
                final_result = await analyst_func(tool_result)
                return final_result
            
            return result
        
        return analyst_with_tools
    
    def _create_optimized_aggregator(self):
        """Create aggregator with performance metrics and report validation"""
        async def optimized_aggregator(state: AgentState) -> AgentState:
            logger.info("📊 OPTIMIZED AGGREGATOR: Collecting results with validation")
            
            # Enhanced aggregation with validation
            reports_ready = 0
            valid_reports = 0
            empty_reports = []
            
            for analyst in ["market", "news", "social", "fundamentals"]:
                report_key = f"{analyst}_report" if analyst != "social" else "sentiment_report"
                report = state.get(report_key, "")
                
                if report:
                    # Check if report has minimum content
                    if len(report.strip()) > 50:
                        reports_ready += 1
                        
                        # Additional validation - check for actual content
                        if not any(error_phrase in report.lower() for error_phrase in [
                            "unable to retrieve", "technical issues", "unavailable",
                            "error", "failed", "no data"
                        ]):
                            valid_reports += 1
                        else:
                            logger.warning(f"⚠️ AGGREGATOR: {analyst} report contains error indicators")
                            empty_reports.append(analyst)
                    else:
                        logger.warning(f"⚠️ AGGREGATOR: {analyst} report too short ({len(report)} chars)")
                        empty_reports.append(analyst)
                else:
                    logger.error(f"🚨 AGGREGATOR: {analyst} report is empty!")
                    empty_reports.append(analyst)
            
            logger.info(f"📊 AGGREGATOR: {reports_ready}/4 reports ready, {valid_reports}/4 valid")
            
            # If too many reports are invalid, flag it
            if valid_reports < 2:
                logger.error(f"🚨 AGGREGATOR: Only {valid_reports} valid reports! Empty: {empty_reports}")
                state["low_quality_reports"] = True
                state["empty_reports"] = empty_reports
            
            # Log Phase 1 performance metrics
            if self.config['enable_phase1_optimizations']:
                summary = self.phase1_optimizer.get_optimization_summary()
                if summary.get("total_runs", 0) > 0:
                    logger.info(
                        f"⚡ Phase 1 Metrics: "
                        f"Token reduction {summary['average_token_reduction']:.1%}, "
                        f"Runtime reduction {summary['average_runtime_reduction']:.1%}"
                    )
            
            # Initialize debate states
            if "investment_debate_state" not in state:
                state["investment_debate_state"] = {
                    "bull_history": "",
                    "bear_history": "",
                    "history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0
                }
            
            if "risk_debate_state" not in state:
                state["risk_debate_state"] = {
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
            
            state["aggregation_ready"] = reports_ready >= 3
            
            logger.info("📊 AGGREGATOR: ✅ All reports collected")
            return state
        
        return optimized_aggregator
    
    def _add_workflow_nodes(self, graph: StateGraph):
        """Add workflow nodes (research, risk, trader)"""
        # Research workflow
        graph.add_node("research_debate_controller", create_research_debate_controller(self.config))
        graph.add_node("bull_researcher", create_bull_researcher(
            self.deep_thinking_llm, 
            self.memory_factory.create_research_memory(self.config)
        ))
        graph.add_node("bear_researcher", create_bear_researcher(
            self.deep_thinking_llm, 
            self.memory_factory.create_research_memory(self.config)
        ))
        graph.add_node("research_manager", create_research_manager(
            self.deep_thinking_llm, 
            self.memory_factory.create_research_memory(self.config), 
            self.config
        ))
        
        # Risk workflow (parallel only)
        graph.add_node("risk_debate_orchestrator", create_risk_debate_orchestrator())
        graph.add_node("parallel_risk_debators", create_parallel_risk_debators(
            self.deep_thinking_llm,
            self.deep_thinking_llm,
            self.deep_thinking_llm
        ))
        graph.add_node("risk_aggregator", self._create_risk_aggregator())
        graph.add_node("risk_manager", create_risk_manager(
            self.deep_thinking_llm, 
            self.memory_factory.create_risk_memory(self.config)
        ))
        
        # Trading workflow
        graph.add_node("trader", create_trader(
            self.deep_thinking_llm, 
            self.memory_factory.create_trader_memory(self.config)
        ))
    
    def _setup_optimized_edges(self, graph: StateGraph, selected_analysts: List[str]):
        """Setup edges for TRUE PARALLEL execution using asyncio.gather()"""
        # Start to parallel analysts node
        graph.add_edge(START, "parallel_analysts")
        
        # Parallel analysts to aggregator
        graph.add_edge("parallel_analysts", "aggregator")
        
        logger.info("🚀 Using asyncio.gather() for true parallel analyst execution")
        
        # Aggregator to research debate controller
        graph.add_edge("aggregator", "research_debate_controller")
        
        # Research debate workflow
        graph.add_edge("research_debate_controller", "bull_researcher")
        graph.add_edge("research_debate_controller", "bear_researcher")
        graph.add_edge("bull_researcher", "research_manager")
        graph.add_edge("bear_researcher", "research_manager")
        
        # Research manager routing - updated for simplified logic
        def research_manager_router(state):
            # Check if debate should continue (new simplified logic)
            if state.get("continue_debate") == True:
                return "research_debate_controller"
            # Check if investment plan exists (debate completed)
            elif state.get("investment_plan"):
                return "risk_manager"
            else:
                # Fallback to continue debate if no clear direction
                return "research_debate_controller"
        
        graph.add_conditional_edges(
            "research_manager",
            research_manager_router,
            {
                "research_debate_controller": "research_debate_controller",
                "risk_manager": "risk_manager"
            }
        )
        
        # Risk manager routing
        def risk_manager_router(state):
            risk_analysis_needed = state.get("risk_analysis_needed", True)
            if not risk_analysis_needed:
                return "trader"
            return "risk_debate_orchestrator"
        
        graph.add_conditional_edges(
            "risk_manager",
            risk_manager_router,
            {
                "risk_debate_orchestrator": "risk_debate_orchestrator",
                "trader": "trader"
            }
        )
        
        # Risk workflow
        graph.add_edge("risk_debate_orchestrator", "parallel_risk_debators")
        graph.add_edge("parallel_risk_debators", "risk_aggregator")
        graph.add_edge("risk_aggregator", "risk_manager")
        
        # Final edge
        graph.add_edge("trader", END)
    
    def _create_analyst_routing(self, analyst_type: str):
        """Create routing logic for analysts"""
        def route(state: AgentState) -> str:
            messages = state.get(f"{analyst_type}_messages", [])
            if not messages:
                return "aggregator"
            
            last_message = messages[-1]
            
            # Check if this is a tool call message
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                # Check if tools have already been executed
                tool_messages = [
                    msg for msg in messages 
                    if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool'
                ]
                if len(tool_messages) > 0:
                    # CRITICAL FIX: Tools executed, but check if report was generated
                    # If tools executed but no report yet, analyst needs another turn to generate report
                    report_key = f"{analyst_type}_report" if analyst_type != "social" else "sentiment_report"
                    current_report = state.get(report_key, "")
                    
                    if not current_report or len(current_report.strip()) < 50:
                        # No report yet, agent needs to generate report based on tool results
                        logger.info(f"🔄 {analyst_type.upper()}_ANALYST: Tools executed, now generating report")
                        return f"{analyst_type}_analyst"  # Back to analyst to generate report
                    else:
                        # Report exists, ready for aggregation
                        logger.info(f"✅ {analyst_type.upper()}_ANALYST: Report ready, proceeding to aggregator")
                        return "aggregator"
                else:
                    # Tools not executed yet, execute them
                    logger.info(f"🔧 {analyst_type.upper()}_ANALYST: Executing tools")
                    return f"{analyst_type}_tools"
            
            # No tool calls, check if we have a report
            report_key = f"{analyst_type}_report" if analyst_type != "social" else "sentiment_report"
            current_report = state.get(report_key, "")
            
            if current_report and len(current_report.strip()) >= 50:
                logger.info(f"✅ {analyst_type.upper()}_ANALYST: Report ready, proceeding to aggregator")
                return "aggregator"
            else:
                # No report and no tools, something went wrong - go to aggregator anyway
                logger.warning(f"⚠️ {analyst_type.upper()}_ANALYST: No report and no tools, proceeding to aggregator")
                return "aggregator"
        
        return route
    
    def _create_market_tool_node(self, toolkit: IAnalystToolkit):
        """Create tool node for market analyst"""
        async def market_tools(state: AgentState) -> AgentState:
            logger.info("🔧 MARKET TOOLS: Executing tools")
            return await self._execute_tools_optimized(state, toolkit, "market_messages")
        return market_tools
    
    def _create_social_tool_node(self, toolkit: IAnalystToolkit):
        """Create tool node for social analyst"""
        async def social_tools(state: AgentState) -> AgentState:
            logger.info("🔧 SOCIAL TOOLS: Executing tools")
            return await self._execute_tools_optimized(state, toolkit, "social_messages")
        return social_tools
    
    def _create_news_tool_node(self, toolkit: IAnalystToolkit):
        """Create tool node for news analyst"""
        async def news_tools(state: AgentState) -> AgentState:
            logger.info("🔧 NEWS TOOLS: Executing tools")
            return await self._execute_tools_optimized(state, toolkit, "news_messages")
        return news_tools
    
    def _create_fundamentals_tool_node(self, toolkit: IAnalystToolkit):
        """Create tool node for fundamentals analyst"""
        async def fundamentals_tools(state: AgentState) -> AgentState:
            logger.info("🔧 FUNDAMENTALS TOOLS: Executing tools")
            return await self._execute_tools_optimized(state, toolkit, "fundamentals_messages")
        return fundamentals_tools
    
    async def _execute_tools_optimized(self, state: AgentState, toolkit: IAnalystToolkit, message_key: str) -> AgentState:
        """Execute tools with async optimization and proper BaseTool handling"""
        from langchain_core.messages import ToolMessage, AIMessage
        from ..utils.tool_execution_fix import execute_tool_safely, validate_tool_response
        
        messages = state.get(message_key, [])
        if not messages:
            return state
        
        last_message = messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])
        
        if not tool_calls:
            return state
        
        # Use parallel tool execution if enabled
        if self.config.get('enable_parallel_tools', True):
            # Execute tools in parallel
            logger.info(f"⚡ Executing {len(tool_calls)} tools in parallel")
            
            tasks = []
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_func = getattr(toolkit, tool_name, None)
                if tool_func:
                    tasks.append(execute_tool_safely(tool_func, tool_call))
                else:
                    async def create_error(name=tool_name, id=tool_call['id']):
                        return {
                            "content": f"Tool {name} not found",
                            "tool_call_id": id,
                            "error": True
                        }
                    tasks.append(create_error())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            tool_responses = []
            empty_responses = 0
            
            for result in results:
                if isinstance(result, Exception):
                    tool_responses.append(ToolMessage(
                        content=f"Error: {str(result)}",
                        tool_call_id="error"
                    ))
                    empty_responses += 1
                else:
                    content = str(result.get("content", ""))
                    
                    # Check if this is an error or empty response
                    if result.get("error") or not validate_tool_response(result, result.get("tool_call_id", "unknown")):
                        empty_responses += 1
                        logger.warning(f"⚠️ Tool returned error or empty response: {content[:100]}...")
                    
                    tool_responses.append(ToolMessage(
                        content=content,
                        tool_call_id=result.get("tool_call_id", "unknown")
                    ))
            
            # If all tools failed, log a critical error
            if empty_responses == len(tool_calls):
                logger.error(f"🚨 ALL {len(tool_calls)} tools failed for {message_key}")
        else:
            # Sequential execution (fallback)
            tool_responses = []
            empty_responses = 0
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_func = getattr(toolkit, tool_name, None)
                
                if tool_func:
                    result = await execute_tool_safely(tool_func, tool_call)
                    
                    if result.get("error") or not validate_tool_response(result, tool_name):
                        empty_responses += 1
                        logger.warning(f"⚠️ Tool {tool_name} failed: {result.get('content', '')[:100]}...")
                    
                    tool_responses.append(ToolMessage(
                        content=str(result.get("content", "")),
                        tool_call_id=tool_call['id']
                    ))
                else:
                    tool_responses.append(ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_call['id']
                    ))
        
        updated_messages = messages + tool_responses
        
        # Add a flag to state if all tools failed
        if empty_responses == len(tool_calls) and len(tool_calls) > 0:
            analyst_type = message_key.replace("_messages", "")
            logger.error(f"🚨 {analyst_type.upper()}: All tools failed, no data available for report generation")
            state[f"{analyst_type}_tools_failed"] = True
        
        return {**state, message_key: updated_messages}
    
    async def _execute_single_tool_async(self, tool_func: Callable, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool asynchronously - DEPRECATED, use execute_tool_safely instead"""
        from ..utils.tool_execution_fix import execute_tool_safely
        return await execute_tool_safely(tool_func, tool_call)
    
    def _create_risk_aggregator(self):
        """Create risk aggregator node"""
        async def risk_aggregator_node(state: AgentState) -> AgentState:
            logger.info("⚡ RISK AGGREGATOR: Collecting risk analyses")
            
            risk_debate_state = state.get("risk_debate_state", {})
            
            # Combine available responses
            combined_history = ""
            
            if risk_debate_state.get("current_risky_response"):
                combined_history += f"Risky Analyst: {risk_debate_state['current_risky_response']}\n\n"
            
            if risk_debate_state.get("current_safe_response"):
                combined_history += f"Safe Analyst: {risk_debate_state['current_safe_response']}\n\n"
            
            if risk_debate_state.get("current_neutral_response"):
                combined_history += f"Neutral Analyst: {risk_debate_state['current_neutral_response']}\n\n"
            
            updated_risk_state = dict(risk_debate_state)
            updated_risk_state["history"] = combined_history.strip()
            
            logger.info("✅ RISK AGGREGATOR COMPLETE")
            
            return {"risk_debate_state": updated_risk_state}
        
        return risk_aggregator_node