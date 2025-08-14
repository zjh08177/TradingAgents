#!/usr/bin/env python3
"""
Enhanced Optimized Trading Graph Setup with Send API + Conditional Edges
Implements true parallel analyst execution while maintaining individual node visibility
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import enhanced state and components
from ..utils.enhanced_agent_states import EnhancedAnalystState, BackwardCompatibilityAdapter
from ..utils.agent_utils import Toolkit
from ..utils.tool_monitoring import get_tool_monitor

# Send API dispatcher and routing
from .send_api_dispatcher import (
    create_dispatcher_node,
    create_routing_function, 
    create_robust_aggregator,
    FallbackExecutionManager,
    LangGraphVersionManager
)

# Enhanced analyst nodes
from .nodes.enhanced_parallel_analysts import (
    create_market_analyst_node,
    create_news_analyst_node,
    create_social_analyst_node,
    create_fundamentals_analyst_node
)

# Phase 1 Optimization Imports - CLEANED UP
# Removed unused optimization imports:
# - AsyncTokenOptimizer (stale, never properly integrated)
# - UltraPromptTemplates (stale, unused)
# - parallel_execution_manager doesn't exist
# - phase1_integration will be removed

# Original imports (preserved for compatibility)
from ..interfaces import ILLMProvider, IMemoryProvider, IAnalystToolkit, IGraphBuilder
from ..factories.llm_factory import LLMFactory
from ..factories.memory_factory import MemoryFactory
from ..factories.toolkit_factory import ToolkitFactory
from ..dataflows.config import get_config

# Import analyst creation functions
from ..analysts.market_analyst_pandas_enabled import create_ultra_fast_market_analyst as create_market_analyst
from ..analysts.social_media_analyst import create_social_media_analyst  
from ..analysts.news_analyst import create_news_analyst
# Crypto-aware implementation enabled (handles both stocks and crypto)
from ..analysts.fundamentals_analyst_crypto_aware import create_fundamentals_analyst_crypto_aware as create_fundamentals_analyst
# Ultra-fast (stock only): from ..analysts.fundamentals_analyst_ultra_fast import create_fundamentals_analyst_ultra_fast as create_fundamentals_analyst
# Original (disabled): from ..analysts.fundamentals_analyst import create_fundamentals_analyst

# Import other node creation functions (preserved)
from ..researchers.bull_researcher import create_bull_researcher
from ..researchers.bear_researcher import create_bear_researcher
from ..managers.research_manager import create_research_manager
from ..trader.trader import create_trader
from ..managers.risk_manager import create_risk_manager

# Import debate nodes (preserved)
from ..controllers.research_debate_controller import create_research_debate_controller
from ..orchestrators.risk_debate_orchestrator import create_risk_debate_orchestrator
from .nodes.parallel_risk_debators import create_parallel_risk_debators

logger = logging.getLogger(__name__)

class EnhancedOptimizedGraphBuilder(IGraphBuilder):
    """
    Enhanced Graph Builder with Send API + Conditional Edges
    Implements true parallel analyst execution with individual node visibility
    Maintains backward compatibility while providing superior performance
    """
    
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,
                 deep_thinking_llm: ILLMProvider,
                 config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.config = config
        
        # Enhanced configuration
        self.config['enable_send_api'] = self.config.get('enable_send_api', True)
        self.config['enable_enhanced_monitoring'] = self.config.get('enable_enhanced_monitoring', True)
        self.config['enable_fallback'] = self.config.get('enable_fallback', True)
        
        # Preserve Phase 1 optimizations
        self.config['enable_phase1_optimizations'] = self.config.get('enable_phase1_optimizations', True)
        self.config['enable_async_tokens'] = self.config.get('enable_async_tokens', True)
        self.config['enable_ultra_prompts'] = self.config.get('enable_ultra_prompts', True)
        self.config['enable_parallel_execution'] = True  # Always enable for enhanced version
        
        # Check LangGraph compatibility
        self.implementation_strategy = LangGraphVersionManager.get_implementation_strategy()
        if self.implementation_strategy != "send_api_parallel":
            logger.warning("⚠️ Send API not available - using fallback strategy")
            self.config['enable_send_api'] = False
        
        # Initialize Phase 1 components - DISABLED (stale code removed)
        if self.config['enable_phase1_optimizations']:
            # These components were removed as they were never properly integrated:
            # - Phase1Optimizer (unused)
            # - AsyncTokenOptimizer (stale)
            # - ParallelExecutionManager (doesn't exist)
            logger.info("⚠️ Phase 1 Optimizations DISABLED - stale code removed")
        
        # Create base toolkit and factories
        self.base_toolkit = Toolkit(self.config)
        self.toolkit_factory = ToolkitFactory()
        self.memory_factory = MemoryFactory()
        
        logger.info("🚀 EnhancedOptimizedGraphBuilder initialized with Send API support")
    
    def setup_graph(self, selected_analysts: List[str] = None) -> CompiledStateGraph:
        """Build enhanced graph with Send API + Conditional Edges"""
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals"]
        
        logger.info(f"🚀 Building ENHANCED graph with Send API for analysts: {selected_analysts}")
        
        # Use enhanced state schema
        graph = StateGraph(EnhancedAnalystState)
        
        if self.config.get('enable_send_api', True):
            # Enhanced Send API implementation
            self._add_send_api_nodes(graph, selected_analysts)
            self._add_workflow_nodes(graph)
            self._setup_send_api_edges(graph, selected_analysts)
            logger.info("✅ Enhanced graph with Send API constructed successfully")
        else:
            # Fallback to existing implementation with enhanced state
            logger.warning("⚠️ Using fallback implementation without Send API")
            self._add_fallback_nodes(graph, selected_analysts)
            self._add_workflow_nodes(graph)
            self._setup_fallback_edges(graph, selected_analysts)
        
        return graph.compile()
    
    def _add_send_api_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add nodes for Send API + Conditional Edges architecture"""
        
        # Core Send API nodes
        logger.info("📦 Adding Send API core nodes...")
        
        # 1. Dispatcher node (prepares state)
        graph.add_node("dispatcher", self._create_enhanced_dispatcher())
        
        # 2. Individual analyst nodes (each visible in LangGraph)
        self._add_individual_analyst_nodes(graph, selected_analysts)
        
        # 3. Enhanced aggregator with error handling
        graph.add_node("enhanced_aggregator", self._create_enhanced_aggregator())
        
        logger.info(f"✅ Added {1 + len(selected_analysts) + 1} Send API nodes to graph")
    
    def _add_individual_analyst_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add individual analyst nodes for Send API routing"""
        
        for analyst_type in selected_analysts:
            node_name = f"{analyst_type}_analyst"
            
            if analyst_type == "market":
                toolkit = self.toolkit_factory.create_market_toolkit(self.base_toolkit)
                node_func = self._create_enhanced_market_analyst(toolkit)
                
            elif analyst_type == "social":
                toolkit = self.toolkit_factory.create_social_toolkit(self.base_toolkit)
                node_func = self._create_enhanced_social_analyst(toolkit)
                
            elif analyst_type == "news":
                toolkit = self.toolkit_factory.create_news_toolkit(self.base_toolkit)
                node_func = self._create_enhanced_news_analyst(toolkit)
                
            elif analyst_type == "fundamentals":
                toolkit = self.toolkit_factory.create_fundamentals_toolkit(self.base_toolkit)
                node_func = self._create_enhanced_fundamentals_analyst(toolkit)
            
            else:
                logger.warning(f"⚠️ Unknown analyst type: {analyst_type}")
                continue
            
            graph.add_node(node_name, node_func)
            logger.info(f"📊 Added {node_name} node")
    
    def _create_enhanced_market_analyst(self, toolkit: IAnalystToolkit) -> Callable:
        """Create enhanced market analyst node"""
        async def enhanced_market_analyst_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            market_analyst = await create_market_analyst_node(self.quick_thinking_llm, toolkit)
            return await market_analyst(state)
        return enhanced_market_analyst_wrapper
    
    def _create_enhanced_news_analyst(self, toolkit: IAnalystToolkit) -> Callable:
        """Create enhanced news analyst node"""
        async def enhanced_news_analyst_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            news_analyst = await create_news_analyst_node(self.quick_thinking_llm, toolkit)
            return await news_analyst(state)
        return enhanced_news_analyst_wrapper
    
    def _create_enhanced_social_analyst(self, toolkit: IAnalystToolkit) -> Callable:
        """Create enhanced social analyst node"""
        async def enhanced_social_analyst_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            social_analyst = await create_social_analyst_node(self.quick_thinking_llm, toolkit)
            return await social_analyst(state)
        return enhanced_social_analyst_wrapper
    
    def _create_enhanced_fundamentals_analyst(self, toolkit: IAnalystToolkit) -> Callable:
        """Create enhanced fundamentals analyst node"""
        async def enhanced_fundamentals_analyst_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            fundamentals_analyst = await create_fundamentals_analyst_node(self.quick_thinking_llm, toolkit)
            return await fundamentals_analyst(state)
        return enhanced_fundamentals_analyst_wrapper
    
    def _create_enhanced_dispatcher(self) -> Callable:
        """Create enhanced dispatcher with performance tracking"""
        async def enhanced_dispatcher_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            dispatcher = await create_dispatcher_node()
            result = await dispatcher(state)
            
            # Add configuration info
            result["send_api_implementation"] = self.implementation_strategy
            result["enhanced_monitoring_enabled"] = self.config.get('enable_enhanced_monitoring', True)
            
            return result
        return enhanced_dispatcher_wrapper
    
    def _create_enhanced_aggregator(self) -> Callable:
        """Create enhanced aggregator with backward compatibility"""
        async def enhanced_aggregator_wrapper(state: EnhancedAnalystState) -> EnhancedAnalystState:
            aggregator = await create_robust_aggregator()
            result = await aggregator(state)
            
            # Phase 1 optimization metrics disabled - stale code removed
            # if self.config['enable_phase1_optimizations']:
            #     summary = self.phase1_optimizer.get_optimization_summary()
            #     if summary.get("total_runs", 0) > 0:
            #         logger.info(
            #             f"⚡ Phase 1 + Send API Metrics: "
            #             f"Token reduction {summary['average_token_reduction']:.1%}, "
            #             f"Runtime reduction {summary['average_runtime_reduction']:.1%}"
            #         )
            
            return result
        return enhanced_aggregator_wrapper
    
    def _setup_send_api_edges(self, graph: StateGraph, selected_analysts: List[str]):
        """Setup edges for Send API + Conditional Edges execution"""
        
        # 1. Start to dispatcher
        graph.add_edge(START, "dispatcher")
        
        # 2. Dispatcher to conditional edges with routing function
        routing_function = create_routing_function(selected_analysts)
        
        # Create the path mapping for conditional edges
        analyst_paths = {}
        for analyst_type in selected_analysts:
            node_name = f"{analyst_type}_analyst"
            analyst_paths[node_name] = node_name
        
        graph.add_conditional_edges(
            "dispatcher",
            routing_function,
            analyst_paths
        )
        
        logger.info(f"🎯 Added conditional edges routing to {len(selected_analysts)} analysts")
        
        # 3. All analysts to enhanced aggregator
        for analyst_type in selected_analysts:
            node_name = f"{analyst_type}_analyst"
            graph.add_edge(node_name, "enhanced_aggregator")
        
        # 4. Enhanced aggregator to research workflow
        graph.add_edge("enhanced_aggregator", "research_debate_controller")
        
        # 5. Rest of workflow (preserved from original)
        self._setup_downstream_workflow_edges(graph)
        
        logger.info("✅ Send API edges configured for true parallel execution")
    
    def _add_workflow_nodes(self, graph: StateGraph):
        """Add workflow nodes (research, risk, trader) - preserved from original"""
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
    
    def _setup_downstream_workflow_edges(self, graph: StateGraph):
        """Setup downstream workflow edges (preserved from original)"""
        
        # Research debate workflow
        graph.add_edge("research_debate_controller", "bull_researcher")
        graph.add_edge("research_debate_controller", "bear_researcher")
        graph.add_edge("bull_researcher", "research_manager")
        graph.add_edge("bear_researcher", "research_manager")
        
        # Research manager routing
        def research_manager_router(state):
            # Convert enhanced state for compatibility
            adapted_state = BackwardCompatibilityAdapter.adapt_state_for_research_manager(state)
            # Check if debate should continue (new simplified logic)
            if state.get("continue_debate") == True:
                return "research_debate_controller"
            # Check if investment plan exists (debate completed)
            elif adapted_state.get("investment_plan"):
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
    
    def _create_risk_aggregator(self):
        """Create risk aggregator node (preserved from original)"""
        async def risk_aggregator_node(state: EnhancedAnalystState) -> EnhancedAnalystState:
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
    
    # Fallback methods (for when Send API is not available)
    def _add_fallback_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add fallback nodes when Send API is not available"""
        logger.warning("⚠️ Adding fallback nodes (Send API not available)")
        
        # Use existing parallel_analysts approach but with enhanced state
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
        graph.add_node("parallel_analysts", create_parallel_analysts_executor(analysts_dict))
        graph.add_node("aggregator", self._create_enhanced_aggregator())
    
    def _setup_fallback_edges(self, graph: StateGraph, selected_analysts: List[str]):
        """Setup edges for fallback implementation"""
        logger.warning("⚠️ Setting up fallback edges (Send API not available)")
        
        # Simple linear flow for fallback
        graph.add_edge(START, "parallel_analysts")
        graph.add_edge("parallel_analysts", "aggregator")
        graph.add_edge("aggregator", "research_debate_controller")
        
        # Rest of workflow
        self._setup_downstream_workflow_edges(graph)
    
    def _wrap_analyst_with_tools(self, analyst_func: Callable, toolkit: IAnalystToolkit, analyst_type: str) -> Callable:
        """Wrap an analyst function to handle tool execution internally (fallback only)"""
        async def analyst_with_tools(state: EnhancedAnalystState) -> EnhancedAnalystState:
            # Convert to legacy state format for compatibility
            from ..utils.agent_states import AgentState
            legacy_state = dict(state)  # Simple conversion for fallback
            
            # Call the analyst
            result = await analyst_func(legacy_state)
            
            # Convert back to enhanced state format
            enhanced_result = dict(result)
            
            return enhanced_result
        
        return analyst_with_tools

# Convenience function for backward compatibility
def create_enhanced_optimized_graph_builder(quick_thinking_llm: ILLMProvider, 
                                           deep_thinking_llm: ILLMProvider, 
                                           config: Dict[str, Any]) -> EnhancedOptimizedGraphBuilder:
    """Create enhanced optimized graph builder with Send API support"""
    return EnhancedOptimizedGraphBuilder(quick_thinking_llm, deep_thinking_llm, config)