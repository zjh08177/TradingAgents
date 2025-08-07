"""
Trading Graph Setup - SOLID-compliant Architecture
Single responsibility for graph construction with dependency injection
"""

import logging
import json
import asyncio
import threading
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from ..utils.agent_states import AgentState
from ..utils.agent_utils import Toolkit
from ..utils.tool_monitoring import get_tool_monitor  # TASK 6.1: Tool monitoring integration
from ..interfaces import ILLMProvider, IMemoryProvider, IAnalystToolkit, IGraphBuilder
from ..factories.llm_factory import LLMFactory
from ..factories.memory_factory import MemoryFactory
from ..factories.toolkit_factory import ToolkitFactory
from ..dataflows.config import get_config
from .nodes.dispatcher import create_parallel_dispatcher
from .prompt_batch_processor import get_graph_prompt_processor, ProcessedPrompts
from ..utils.prompt_injection import PromptInjectionContext

# Import all analyst creation functions
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

# Import debate nodes for multi-round research (parallel execution)
from ..controllers.research_debate_controller import create_research_debate_controller
# Judge functionality now merged into research_manager

# Import parallel risk execution nodes
from ..orchestrators.risk_debate_orchestrator import create_risk_debate_orchestrator
from .nodes.parallel_risk_debators import create_parallel_risk_debators

logger = logging.getLogger(__name__)

# Parallel risk debate mode only - sequential mode removed


async def isolated_analyst_execution(analyst_func, state):
    """
    Execute analyst with error isolation to prevent cascading failures.
    
    If an analyst fails, return a safe error state instead of crashing
    the entire system. This implements Task EI2 from the improvement plan.
    """
    try:
        return await analyst_func(state)
    except Exception as e:
        analyst_name = getattr(analyst_func, '__name__', 'unknown')
        logger.error(f"❌ {analyst_name} failed with error: {type(e).__name__}: {e}")
        
        # Return a safe error state with empty results
        error_state = {
            f"{analyst_name}_messages": [],
            f"{analyst_name}_report": f"Analysis failed due to error: {str(e)[:100]}...",
            "sender": analyst_name,
            "error": str(e)
        }
        
        # Map to correct report keys based on analyst type
        if "market" in analyst_name:
            error_state["market_report"] = error_state.pop(f"{analyst_name}_report", "")
        elif "social" in analyst_name:
            error_state["sentiment_report"] = error_state.pop(f"{analyst_name}_report", "")
        elif "news" in analyst_name:
            error_state["news_report"] = error_state.pop(f"{analyst_name}_report", "")
        elif "fundamentals" in analyst_name:
            error_state["fundamentals_report"] = error_state.pop(f"{analyst_name}_report", "")
            
        return error_state


def create_isolated_analyst(analyst_func):
    """Create an isolated version of an analyst function."""
    async def isolated_wrapper(state):
        return await isolated_analyst_execution(analyst_func, state)
    
    # Preserve the original function's name for debugging
    isolated_wrapper.__name__ = getattr(analyst_func, '__name__', 'isolated_analyst')
    return isolated_wrapper

class GraphBuilder(IGraphBuilder):
    """SOLID-compliant graph builder with dependency injection"""
    
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,
                 deep_thinking_llm: ILLMProvider,
                 config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.config = config
        
        # Add comprehensive config logging
        logger.info("🔍 CONFIG DIAGNOSTICS START")
        logger.info(f"Full config: {json.dumps(config, indent=2)}")
        logger.info(f"Parallel risk: {config.get('enable_parallel_risk_debate')}")
        logger.info(f"Token limits: {config.get('max_tokens_per_analyst')}")
        logger.info(f"Execution timeout: {config.get('execution_timeout')}")
        logger.info(f"Enable retry: {config.get('enable_retry', True)}")
        logger.info(f"Smart retry: {config.get('enable_smart_retry')}")
        logger.info(f"Tool cache: {config.get('enable_tool_cache')}")
        logger.info(f"Batch execution: {config.get('enable_batch_execution')}")
        logger.info(f"Batch prompt processing: {config.get('enable_batch_prompt_processing', True)}")
        logger.info("🔍 CONFIG DIAGNOSTICS END")
        
        # Create base toolkit and factories
        self.base_toolkit = Toolkit(self.config)
        self.toolkit_factory = ToolkitFactory()
        self.memory_factory = MemoryFactory()
        
        # Initialize batch prompt processor for Phase 3.2
        self.prompt_processor = get_graph_prompt_processor(self.config)
        self.preprocessed_prompts: Optional[ProcessedPrompts] = None
        
        logger.info("🚀 GraphBuilder initialized with dependency injection and batch processing")

    def setup_graph(self, selected_analysts: List[str] = None) -> CompiledStateGraph:
        """Build the complete graph following SOLID principles"""
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals"]
        
        logger.info(f"🚀 Building SOLID-compliant graph with analysts: {selected_analysts}")
        
        # Phase 3.2: Pre-process all analyst prompts in batch if enabled
        if self.config.get('enable_batch_prompt_processing', True):
            self._preprocess_prompts_sync(selected_analysts)
        
        graph = StateGraph(AgentState)
        
        # Add core nodes
        self._add_core_nodes(graph, selected_analysts)
        
        # Add analyst nodes based on selection
        # If batch processing is enabled, analysts will use pre-processed prompts
        if self.preprocessed_prompts:
            with PromptInjectionContext(self.preprocessed_prompts.prompts):
                self._add_analyst_nodes(graph, selected_analysts)
        else:
            self._add_analyst_nodes(graph, selected_analysts)
        
        # Add remaining workflow nodes
        self._add_workflow_nodes(graph)
        
        # Setup edges
        self._setup_edges(graph, selected_analysts)
        
        logger.info("✅ SOLID-compliant graph constructed successfully")
        return graph.compile()
    
    def _preprocess_prompts_sync(self, selected_analysts: List[str]):
        """
        Synchronous wrapper for prompt preprocessing that works in both sync and async contexts
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're in an async context (like LangGraph dev)
            # We can't use asyncio.run(), so we'll use the loop directly
            logger.info("📦 Detected async context, using event loop for batch processing")
            
            # Create a future to get the result
            import concurrent.futures
            import threading
            
            result_container = {'result': None}
            exception_container = {'exception': None}
            
            def run_in_thread():
                try:
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(
                            self._preprocess_analyst_prompts(selected_analysts)
                        )
                        result_container['result'] = result
                    finally:
                        new_loop.close()
                except Exception as e:
                    exception_container['exception'] = e
            
            # Run in a separate thread
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join(timeout=30)  # 30 second timeout
            
            if exception_container['exception']:
                raise exception_container['exception']
            
            # Result is stored in self.preprocessed_prompts by the async method
            
        except RuntimeError:
            # No running loop, we can use asyncio.run() safely
            logger.info("📦 No async context detected, using asyncio.run()")
            asyncio.run(self._preprocess_analyst_prompts(selected_analysts))
    
    async def _preprocess_analyst_prompts(self, selected_analysts: List[str]):
        """
        Phase 3.2: Pre-process all analyst prompts in batch
        This significantly improves performance by processing prompts in parallel
        """
        logger.info(f"📦 Pre-processing prompts for {len(selected_analysts)} analysts")
        
        # Collect base prompts from each analyst type
        analyst_configs = {}
        
        # Define base prompts for each analyst
        # These would normally come from the analyst modules, but we'll define them here
        base_prompts = {
            "market": """Expert market analyst: TA & trading signals.

MANDATORY: Use tools→get real data before analysis.
Tools: get_YFin_data, get_stockstats_indicators_report

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

Analyze (max 8): MA(50,200), EMA(10), MACD, RSI, BB, ATR, VWMA

Output structure:
1. Summary: Position|Signal|BUY/SELL/HOLD|Confidence|Target
2. Indicators: Trend(MA)|Momentum(MACD,RSI)|Volatility(BB,ATR)|Volume(VWMA)
3. Metrics table: Indicator|Value|Signal(↑↓→)|Weight(H/M/L)
4. Strategy: Entry|SL|TP|Size
5. Risk: Technical|Market|Volatility
6. Rec: Decision|Confidence(1-10)|1w/1m outlook""",
            
            "social": """Social media sentiment analyst specializing in market sentiment.

MANDATORY: Use tools→get real data before analysis.
Tools: get_reddit_stock_info

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

Output structure:
1. Summary: Sentiment|Bullish/Bearish/Neutral|Confidence
2. Sources: Reddit|Twitter|Forums|News mentions
3. Metrics: Positive%|Negative%|Volume|Trend
4. Key themes: Top 3 discussed topics
5. Influencers: Major voices and their stance
6. Risk: Hype risk|Manipulation|Echo chamber
7. Signal: BUY/SELL/HOLD based on sentiment""",
            
            "news": """News analyst specializing in market-moving events.

MANDATORY: Use tools→get real data before analysis.
Tools: get_global_news_openai, get_google_news

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

Output structure:
1. Summary: Impact|Positive/Negative/Neutral|Urgency
2. Key stories: Top 3 market movers
3. Categories: Company|Industry|Macro|Regulatory
4. Timeline: Immediate|Short-term|Long-term impacts
5. Sentiment: Media tone and coverage volume
6. Risks: Event risk|Headline risk|Regulatory
7. Signal: BUY/SELL/HOLD based on news""",
            
            "fundamentals": """Fundamentals analyst specializing in financial analysis.

MANDATORY: Use tools→get real data before analysis.
Tools: get_fundamentals_openai, get_simfin_balance_sheet, get_simfin_income_stmt

Workflow: 1)Call tools 2)Get data 3)Analyze 4)Report

Output structure:
1. Summary: Health|Strong/Average/Weak|Valuation
2. Metrics: P/E|EPS|Revenue|Margins|ROE
3. Growth: Revenue growth|Earnings growth|Trends
4. Balance sheet: Assets|Liabilities|Cash|Debt
5. Comparison: vs Industry|vs Peers|Historical
6. Risks: Financial|Business model|Competition
7. Signal: BUY/SELL/HOLD based on fundamentals"""
        }
        
        # Build configs for selected analysts
        for analyst in selected_analysts:
            if analyst in base_prompts:
                analyst_configs[analyst] = {
                    "base_prompt": base_prompts[analyst],
                    "config": self.config
                }
        
        # Process prompts in batch
        import time
        batch_start = time.time()
        
        self.preprocessed_prompts = await self.prompt_processor.process_analyst_prompts_batch(
            analyst_configs
        )
        
        batch_time = time.time() - batch_start
        
        if self.preprocessed_prompts:
            logger.info(f"📦 Batch prompt processing complete:")
            logger.info(f"   - Time: {batch_time:.3f}s")
            logger.info(f"   - Speedup: {self.preprocessed_prompts.speedup:.1f}x")
            logger.info(f"   - Token savings: {self.preprocessed_prompts.token_savings}")
            logger.info(f"   - Prompts ready: {len(self.preprocessed_prompts.prompts)}")
        else:
            logger.warning("⚠️ Batch prompt processing failed, falling back to sequential")

    def _add_core_nodes(self, graph: StateGraph, selected_analysts: List[str] = None):
        """Add core dispatcher and aggregator nodes"""
        graph.add_node("dispatcher", self._create_dispatcher(selected_analysts))
        graph.add_node("aggregator", self._create_aggregator())

    def _add_analyst_nodes(self, graph: StateGraph, selected_analysts: List[str]):
        """Add analyst nodes and their dedicated tools using factories"""
        
        analyst_builders = {
            "market": self._build_market_analyst,
            "social": self._build_social_analyst,
            "news": self._build_news_analyst,
            "fundamentals": self._build_fundamentals_analyst
        }
        
        for analyst_type in selected_analysts:
            if analyst_type in analyst_builders:
                logger.info(f"🔧 Building {analyst_type} analyst with dedicated toolkit")
                analyst_builders[analyst_type](graph)

    def _build_market_analyst(self, graph: StateGraph):
        """Build market analyst with its dedicated toolkit and routing"""
        toolkit = self.toolkit_factory.create_market_toolkit(self.base_toolkit)
        analyst = create_market_analyst(self.quick_thinking_llm, toolkit)
        tools = self._create_market_tool_node(toolkit)
        
        graph.add_node("market_analyst", create_isolated_analyst(analyst))
        graph.add_node("market_tools", tools)
        
        # Add conditional routing - TASK 1.2: These edges support parallel execution
        graph.add_conditional_edges("market_analyst", self._create_analyst_routing("market"), {
            "market_tools": "market_tools",
            "aggregator": "aggregator"
        })
        graph.add_edge("market_tools", "market_analyst")

    def _build_social_analyst(self, graph: StateGraph):
        """Build social analyst with its dedicated toolkit and routing"""
        toolkit = self.toolkit_factory.create_social_toolkit(self.base_toolkit)
        analyst = create_social_media_analyst(self.quick_thinking_llm, toolkit)
        tools = self._create_social_tool_node(toolkit)
        
        graph.add_node("social_analyst", create_isolated_analyst(analyst))
        graph.add_node("social_tools", tools)
        
        # Add conditional routing - TASK 1.2: These edges support parallel execution
        graph.add_conditional_edges("social_analyst", self._create_analyst_routing("social"), {
            "social_tools": "social_tools",
            "aggregator": "aggregator"
        })
        graph.add_edge("social_tools", "social_analyst")

    def _build_news_analyst(self, graph: StateGraph):
        """Build news analyst with its dedicated toolkit and routing"""
        toolkit = self.toolkit_factory.create_news_toolkit(self.base_toolkit)
        analyst = create_news_analyst(self.quick_thinking_llm, toolkit)
        tools = self._create_news_tool_node(toolkit)
        
        graph.add_node("news_analyst", create_isolated_analyst(analyst))
        graph.add_node("news_tools", tools)
        
        # Add conditional routing - TASK 1.2: These edges support parallel execution
        graph.add_conditional_edges("news_analyst", self._create_analyst_routing("news"), {
            "news_tools": "news_tools",
            "aggregator": "aggregator"
        })
        graph.add_edge("news_tools", "news_analyst")

    def _build_fundamentals_analyst(self, graph: StateGraph):
        """Build fundamentals analyst with its dedicated toolkit and routing"""
        toolkit = self.toolkit_factory.create_fundamentals_toolkit(self.base_toolkit)
        analyst = create_fundamentals_analyst(self.quick_thinking_llm, toolkit)
        tools = self._create_fundamentals_tool_node(toolkit)
        
        graph.add_node("fundamentals_analyst", create_isolated_analyst(analyst))
        graph.add_node("fundamentals_tools", tools)
        
        # Add conditional routing - TASK 1.2: These edges support parallel execution
        graph.add_conditional_edges("fundamentals_analyst", self._create_analyst_routing("fundamentals"), {
            "fundamentals_tools": "fundamentals_tools", 
            "aggregator": "aggregator"
        })
        graph.add_edge("fundamentals_tools", "fundamentals_analyst")

    def _add_workflow_nodes(self, graph: StateGraph):
        """Add core workflow nodes with parallel risk debate only"""
        # Research workflow with multi-round debate (parallel execution)
        graph.add_node("research_debate_controller", create_research_debate_controller(self.config))
        graph.add_node("bull_researcher", create_bull_researcher(self.deep_thinking_llm, self.memory_factory.create_research_memory(self.config)))
        graph.add_node("bear_researcher", create_bear_researcher(self.deep_thinking_llm, self.memory_factory.create_research_memory(self.config)))
        # Research manager handles both judge and final plan generation
        graph.add_node("research_manager", create_research_manager(
            self.deep_thinking_llm, 
            self.memory_factory.create_research_memory(self.config), 
            self.config
        ))
        
        # Risk workflow - Parallel mode only
        logger.info("⚡ Risk debate mode: PARALLEL (always enabled)")
        
        # Add parallel risk nodes only
        graph.add_node("risk_debate_orchestrator", create_risk_debate_orchestrator())
        graph.add_node("parallel_risk_debators", create_parallel_risk_debators(
            self.deep_thinking_llm,
            self.deep_thinking_llm,
            self.deep_thinking_llm
        ))
        
        # Common nodes for both modes
        graph.add_node("risk_aggregator", self._create_risk_aggregator())
        graph.add_node("risk_manager", create_risk_manager(self.deep_thinking_llm, self.memory_factory.create_risk_memory(self.config)))
        
        # Trading workflow
        graph.add_node("trader", create_trader(self.deep_thinking_llm, self.memory_factory.create_trader_memory(self.config)))

    def _create_risk_aggregator(self):
        """Create risk aggregator node that collects all risk analyses."""
        
        async def risk_aggregator_node(state: AgentState) -> AgentState:
            logger.info("⚡ NODE EXECUTING: RISK AGGREGATOR")
            
            risk_debate_state = state.get("risk_debate_state", {})
            
            # Get individual risk analyst responses
            risky_response = risk_debate_state.get("current_risky_response", "")
            safe_response = risk_debate_state.get("current_safe_response", "")
            neutral_response = risk_debate_state.get("current_neutral_response", "")
            
            logger.info("⚡ Risk Aggregator: Checking risk analysis status:")
            logger.info(f"   - Risky analyst response: {len(risky_response)} chars")
            logger.info(f"   - Safe analyst response: {len(safe_response)} chars")
            logger.info(f"   - Neutral analyst response: {len(neutral_response)} chars")
            
            # Count available responses
            responses = [risky_response, safe_response, neutral_response]
            available_responses = [r for r in responses if r and len(r.strip()) > 0]
            total_responses = len(available_responses)
            
            if total_responses == 0:
                logger.error("⚡ Risk Aggregator: ❌ NO RISK ANALYSES AVAILABLE")
                return state
            
            if total_responses < 3:
                logger.warning(f"⚡ Risk Aggregator: ⚠️ Only {total_responses}/3 risk analyses available")
            
            # Combine all available responses into a unified debate history
            combined_history = ""
            
            if risky_response:
                combined_history += f"Risky Analyst: {risky_response}\n\n"
            
            if safe_response:
                combined_history += f"Safe Analyst: {safe_response}\n\n"
            
            if neutral_response:
                combined_history += f"Neutral Analyst: {neutral_response}\n\n"
            
            if total_responses == 3:
                logger.info("⚡ Risk Aggregator: ✅ All risk analyses complete")
            
            # Update risk debate state with combined history
            updated_risk_state = dict(risk_debate_state)
            updated_risk_state["history"] = combined_history.strip()
            
            logger.info(f"⚡ Risk Aggregator: Combined history length: {len(combined_history)} chars")
            logger.info("⚡ Risk Aggregator: Risk analyses aggregated for final judgment")
            logger.info("✅ RISK AGGREGATOR COMPLETE")
            
            return {
                "risk_debate_state": updated_risk_state
            }
        
        return risk_aggregator_node

    def _setup_edges(self, graph: StateGraph, selected_analysts: List[str]):
        """Setup graph edges for TRUE PARALLEL workflow - Task 1.1 Implementation"""
        # Setup main dispatcher
        graph.add_edge(START, "dispatcher")
        
        # CRITICAL: Dispatcher to ALL analysts in PARALLEL (Task 1.1)
        # This is the key architectural change from conditional routing to true parallel
        for analyst_type in selected_analysts:
            graph.add_edge("dispatcher", f"{analyst_type}_analyst")
            logger.info(f"🔗 Added PARALLEL edge: dispatcher -> {analyst_type}_analyst")
          
        # Aggregator to research debate workflow
        graph.add_edge("aggregator", "research_debate_controller")
        
        # Research debate workflow edges - NEW PARALLEL FLOW
        # Controller spawns both bull and bear in parallel
        graph.add_edge("research_debate_controller", "bull_researcher")
        graph.add_edge("research_debate_controller", "bear_researcher")
        
        # Both researchers route directly to research manager
        graph.add_edge("bull_researcher", "research_manager")
        graph.add_edge("bear_researcher", "research_manager")
        
        # Research manager conditional routing (back to controller or forward to risk manager)
        def research_manager_router(state):
            """Route from research manager based on simplified debate logic"""
            # Check if debate should continue (new simplified logic)
            if state.get("continue_debate") == True:
                logger.info("🔄 Continue debate flag set - routing back to debate controller")
                return "research_debate_controller"
            # Check if investment plan exists (debate completed)
            elif state.get("investment_plan"):
                logger.info("✅ Investment plan ready - routing to risk manager")
                return "risk_manager"
            else:
                # Fallback to continue debate if no clear direction
                logger.info("🔄 Fallback - routing back to debate controller")
                return "research_debate_controller"
        
        graph.add_conditional_edges(
            "research_manager",
            research_manager_router,
            {
                "research_debate_controller": "research_debate_controller",
                "risk_manager": "risk_manager"
            }
        )
        
        # Risk manager routing to parallel risk debate
        def risk_manager_router(state):
            """Route from risk manager to parallel risk debate or trader"""
            # Check if we need risk debate or can proceed directly
            risk_analysis_needed = state.get("risk_analysis_needed", True)
            
            if not risk_analysis_needed:
                logger.info("✅ Risk analysis complete - proceeding to trader")
                return "trader"
            
            # Always route to parallel risk debate
            logger.info("⚡ Routing to PARALLEL risk debate")
            return "risk_debate_orchestrator"
        
        graph.add_conditional_edges(
            "risk_manager",
            risk_manager_router,
            {
                "risk_debate_orchestrator": "risk_debate_orchestrator",
                "trader": "trader"
            }
        )
        
        # Risk workflow edges - parallel only
        graph.add_edge("risk_debate_orchestrator", "parallel_risk_debators")
        graph.add_edge("parallel_risk_debators", "risk_aggregator")
        
        # Common edges - risk aggregator back to risk manager for final decision
        graph.add_edge("risk_aggregator", "risk_manager")
        # Risk manager will conditionally route to trader when complete
        graph.add_edge("trader", END)

    def _create_analyst_routing(self, analyst_type: str):
        """Create routing logic for analyst nodes with smart retry optimization (Optimization 4)"""
        def route(state: AgentState) -> str:
            messages = state.get(f"{analyst_type}_messages", [])
            if not messages:
                return "aggregator"
            
            # OPTIMIZATION 4: Smart Retry Logic - Skip unnecessary retries when valid data is present
            if self.config.get("enable_smart_retry", True):
                from ..utils.smart_retry import should_skip_analyst_retry
                
                # Check if we should skip retry based on data quality
                should_skip = should_skip_analyst_retry(analyst_type, messages, state)
                
                if should_skip:
                    logger.info(f"🚀 OPTIMIZATION 4: {analyst_type.upper()} retry SKIPPED - sufficient data quality")
                    return "aggregator"
            
            # TASK 0.2.2: Validate tool usage before proceeding
            from ..utils.tool_validator import ToolUsageValidator
            
            # Check if we've already validated and retried
            retry_count = state.get(f"{analyst_type}_retry_count", 0)
            
            # TASK 8.1.2: Optimize retry logic - check if we have valid tool data first
            # Check if tools have already been executed (look for ToolMessage instances)
            tool_messages = [msg for msg in messages if hasattr(msg, 'type') and str(getattr(msg, 'type', '')) == 'tool']
            has_tool_responses = len(tool_messages) > 0
            
            # If we have tool responses, check if they're valid
            if has_tool_responses:
                # Check if any tool response has actual data (not just errors)
                valid_tool_data = any(
                    msg for msg in tool_messages 
                    if hasattr(msg, 'content') and msg.content 
                    and not msg.content.startswith("Error")
                    and len(msg.content) > 50  # Ensure substantial response
                )
                
                if valid_tool_data:
                    # We have valid tool data, skip retry and go to aggregator
                    logger.info(f"✅ {analyst_type.upper()}_ROUTING: Valid tool data present, skipping retry")
                    return "aggregator"
            
            # Only validate and retry if we haven't exceeded retry limit AND don't have valid tool data
            if retry_count < 2 and not has_tool_responses:
                has_valid_tools = ToolUsageValidator.validate_analyst_response(analyst_type, messages)
                
                if not has_valid_tools:
                    # Check if last message has any content (indicating attempted analysis without tools)
                    last_message = messages[-1]
                    if hasattr(last_message, 'content') and last_message.content and len(last_message.content) > 100:
                        # Analyst tried to provide analysis without tools - force retry
                        logger.error(f"🚨 {analyst_type}: Analysis attempted without tools - forcing retry")
                        state[f"{analyst_type}_retry_count"] = retry_count + 1
                        state[f"{analyst_type}_retry_reason"] = "NO_TOOLS_CALLED"
                        
                        # Add a system message to force tool usage
                        validation_msg = ToolUsageValidator.get_validation_message(analyst_type)
                        state[f"{analyst_type}_force_tools_message"] = validation_msg
                        
                        return f"{analyst_type}_analyst"  # Loop back to analyst
            
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                # TASK 4.1 FIX: Check if tools have already been executed once
                # This eliminates the 3-iteration loop that was causing 67% performance loss
                if has_tool_responses:
                    # Tools have been executed once, go directly to aggregator
                    logger.info(f"🔧 {analyst_type.upper()}_ROUTING: Single-pass complete, routing to aggregator")
                    return "aggregator"
                # First tool execution - proceed to tools
                logger.info(f"🔧 {analyst_type.upper()}_ROUTING: Starting single tool execution")
                return f"{analyst_type}_tools"
            return "aggregator"
        
        return route
    
    def _create_research_debate_routing(self):
        """OPTIMIZATION 5: Optimized routing logic for multi-round research debate"""
        def route(state: AgentState) -> str:
            # OPTIMIZATION 5: Use debate optimizer for smart routing decisions
            if self.config.get("enable_debate_optimization", True):
                from ..utils.debate_optimizer import optimize_research_debate_routing
                
                # Get round start time if available
                round_start_time = state.get("research_debate_round_start_time")
                
                # Use optimized routing with performance monitoring
                result = optimize_research_debate_routing(state, round_start_time)
                return result
            else:
                # Fallback to original logic
                debate_state = state.get("research_debate_state", {})
                
                current_round = debate_state.get("current_round", 0)
                max_rounds = debate_state.get("max_rounds", 1)
                consensus_reached = debate_state.get("consensus_reached", False)
                
                if consensus_reached or current_round >= max_rounds:
                    logger.info(f"✅ Research debate complete after {current_round} rounds")
                    return "research_manager"
                else:
                    logger.info(f"🔄 Continuing to round {current_round + 1}")
                    return "research_debate_controller"
        
        return route

    def _create_market_tool_node(self, toolkit: IAnalystToolkit):
        """Create dedicated tool node for market analyst"""
        async def market_tools(state: AgentState) -> AgentState:
            logger.info("🔧 MARKET TOOLS: Executing tools")
            return await self._execute_tools(state, toolkit, "market_messages")
        return market_tools

    def _create_social_tool_node(self, toolkit: IAnalystToolkit):
        """Create dedicated tool node for social analyst"""
        async def social_tools(state: AgentState) -> AgentState:
            logger.info("🔧 SOCIAL TOOLS: Executing tools")
            return await self._execute_tools(state, toolkit, "social_messages")
        return social_tools

    def _create_news_tool_node(self, toolkit: IAnalystToolkit):
        """Create dedicated tool node for news analyst"""
        async def news_tools(state: AgentState) -> AgentState:
            logger.info("🔧 NEWS TOOLS: Executing tools")
            return await self._execute_tools(state, toolkit, "news_messages")
        return news_tools

    def _create_fundamentals_tool_node(self, toolkit: IAnalystToolkit):
        """Create dedicated tool node for fundamentals analyst"""
        async def fundamentals_tools(state: AgentState) -> AgentState:
            logger.info("🔧 FUNDAMENTALS TOOLS: Executing tools")
            return await self._execute_tools(state, toolkit, "fundamentals_messages")
        return fundamentals_tools

    def _get_required_tools_for_analyst(self, analyst_type: str) -> List[str]:
        """TASK 4.3: Define deterministic tool execution order for each analyst"""
        tool_order = {
            "market": [
                "get_YFin_data",  # Always first - provides base price data
                "get_YFin_data_online",  # Online version as alternative
                "get_stockstats_indicators_report",  # Second - technical analysis
                "get_stockstats_indicators_report_online"  # Online version
            ],
            "social": [
                "get_reddit_stock_info",  # Primary social sentiment source
                "get_stock_news_openai",  # Secondary if available
                "get_stocktwits_sentiment",  # Additional if available
                "get_twitter_mentions"  # Additional if available
            ],
            "news": [
                "get_global_news_openai",  # Broad market news first
                "get_finnhub_news",  # Alternative market news
                "get_google_news",   # Specific company news second
                "get_reddit_news"    # Social news last
            ],
            "fundamentals": [
                "get_fundamentals_openai",  # Primary fundamentals source
                "get_simfin_balance_sheet",  # Financial position first
                "get_simfin_income_stmt",    # Profitability second  
                "get_simfin_cashflow",        # Cash generation third
                "get_finnhub_company_insider_sentiment",  # Insider info
                "get_finnhub_company_insider_transactions"  # Insider trades
            ]
        }
        return tool_order.get(analyst_type, [])

    async def _execute_tools(self, state: AgentState, toolkit: IAnalystToolkit, message_key: str) -> AgentState:
        """Common tool execution logic following DRY principle"""
        messages = state.get(message_key, [])
        if not messages:
            return state
            
        last_message = messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])
        
        if not tool_calls:
            return state
        
        # OPTIMIZATION 2: Enable parallel tool execution for all analysts
        if self.config.get("enable_parallel_tools", True):
            return await self._execute_tools_parallel(state, toolkit, message_key, tool_calls)
        else:
            return await self._execute_tools_sequential(state, toolkit, message_key, tool_calls)

    async def _execute_tools_sequential(self, state: AgentState, toolkit: IAnalystToolkit, message_key: str, tool_calls) -> AgentState:
        """Sequential tool execution for non-fundamentals analysts with monitoring and retry logic"""
        from langchain_core.messages import ToolMessage, AIMessage
        from ..utils.tool_retry import execute_tool_with_fallback
        import time
        
        tool_responses = []
        messages = state.get(message_key, [])
        monitor = get_tool_monitor()  # TASK 6.1: Get monitor instance
        analyst_type = message_key.replace('_messages', '')  # Extract analyst type
        
        # TASK 4.3: Get deterministic tool order for this analyst
        required_tools = self._get_required_tools_for_analyst(analyst_type)
        logger.info(f"🔧 {analyst_type.upper()}_TOOLS: Using deterministic order: {required_tools[:4]}")  # Show first 4 tools
        
        # Create a map of requested tools for quick lookup
        requested_tools = {tc['name']: tc for tc in tool_calls}
        
        # TASK 4.3: Execute tools in deterministic order
        ordered_tool_calls = []
        for tool_name in required_tools:
            if tool_name in requested_tools:
                ordered_tool_calls.append(requested_tools[tool_name])
                logger.info(f"🔧 TOOLS: Executing {tool_name} (deterministic order)")
        
        # Add any tools not in the predefined order (for flexibility)
        for tc in tool_calls:
            if tc not in ordered_tool_calls:
                ordered_tool_calls.append(tc)
                logger.warning(f"🔧 TOOLS: Tool {tc['name']} not in predefined order, adding at end")
        
        # TASK 8.1.1: Create proper AIMessage with tool_calls for LangGraph tracking
        # This ensures LangGraph properly tracks our tool executions
        tool_call_message = AIMessage(
            content="",
            tool_calls=[{
                "id": tc['id'],
                "name": tc['name'], 
                "args": tc['args']
            } for tc in ordered_tool_calls]
        )
        messages.append(tool_call_message)
        logger.info(f"📊 TRACKING: Added AIMessage with {len(ordered_tool_calls)} tool calls for proper tracking")
        
        for tool_call in ordered_tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_id = tool_call['id']
            
            # TASK 6.1: Record tool execution start
            tool_start = time.time()
            logger.info(f"🔧 TOOLS: Executing {tool_name}")
            
            try:
                tool_func = getattr(toolkit, tool_name, None)
                if tool_func is None:
                    tool_end = time.time()
                    logger.error(f"🔧 TOOLS: Tool {tool_name} not found")
                    
                    # CRITICAL FIX: Always add ToolMessage even when tool is not found
                    # This prevents the "tool_calls must be followed by tool messages" error
                    tool_responses.append(ToolMessage(
                        content=f"Error: Tool {tool_name} not found in toolkit",
                        tool_call_id=tool_id
                    ))
                    
                    # TASK 6.1: Record failed execution
                    monitor.record_execution(
                        tool_name=tool_name,
                        analyst_type=analyst_type,
                        start_time=tool_start,
                        end_time=tool_end,
                        success=False,
                        error_message=f"Tool {tool_name} not found",
                        input_data=tool_args
                    )
                    continue
                
                # TASK 7.2: Use retry logic with fallback
                # Determine fallback tool based on the primary tool
                fallback_tool = None
                if tool_name == "get_fundamentals_openai" and hasattr(toolkit, "get_simfin_balance_sheet"):
                    fallback_tool = toolkit.get_simfin_balance_sheet
                elif tool_name == "get_stock_news_openai" and hasattr(toolkit, "get_reddit_stock_info"):
                    fallback_tool = toolkit.get_reddit_stock_info
                elif tool_name == "get_global_news_openai" and hasattr(toolkit, "get_reddit_news"):
                    fallback_tool = toolkit.get_reddit_news
                
                # Execute with retry and fallback
                result = await execute_tool_with_fallback(
                    primary_tool=tool_func,
                    fallback_tool=fallback_tool,
                    params=tool_args,
                    tool_name=tool_name
                )
                
                tool_end = time.time()
                
                # Check if result is an error with fallback
                if isinstance(result, dict) and result.get("fallback"):
                    logger.warning(f"🔧 TOOLS: {tool_name} used fallback after failure")
                    # Still record as success if fallback worked
                    success = not result.get("error", "").startswith("Tool")
                else:
                    success = True
                
                tool_responses.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id
                ))
                
                # TASK 6.1: Record execution (success or failure)
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=tool_start,
                    end_time=tool_end,
                    success=success,
                    input_data=tool_args,
                    output_data=result,
                    error_message=result.get("original_error") if isinstance(result, dict) and result.get("fallback") else None
                )
                
                if success:
                    logger.info(f"🔧 TOOLS: ✅ {tool_name} completed")
                else:
                    logger.error(f"🔧 TOOLS: ❌ {tool_name} failed after retries")
                
            except Exception as e:
                tool_end = time.time()
                logger.error(f"🔧 TOOLS: ❌ {tool_name} failed: {e}")
                
                # TASK 6.1: Record failed execution
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=tool_start,
                    end_time=tool_end,
                    success=False,
                    error_message=str(e),
                    input_data=tool_args
                )
                
                tool_responses.append(ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_id
                ))
        
        updated_messages = messages + tool_responses
        return {**state, message_key: updated_messages}

    async def _execute_tools_parallel(self, state: AgentState, toolkit: IAnalystToolkit, message_key: str, tool_calls) -> AgentState:
        """OPTIMIZATION 2: Parallel tool execution for all analysts - 50%+ speedup target"""
        import asyncio
        import time
        from langchain_core.messages import ToolMessage, AIMessage
        
        messages = state.get(message_key, [])
        parallel_start = time.time()
        
        analyst_type = message_key.replace('_messages', '')
        logger.info(f"⚡ {analyst_type.upper()}: Starting parallel tool execution ({len(tool_calls)} tools)")
        
        # TASK 6.1: Get monitor instance for parallel execution
        monitor = get_tool_monitor()
        
        # TASK 4.3: Get deterministic tool order for this analyst
        required_tools = self._get_required_tools_for_analyst(analyst_type)
        logger.info(f"🔧 {analyst_type.upper()}: Using deterministic order: {required_tools[:4]}")  # Show first 4 tools
        
        # Create a map of requested tools for quick lookup
        requested_tools = {tc['name']: tc for tc in tool_calls}
        
        # TASK 4.3: Prepare tools in deterministic order for parallel execution
        ordered_tool_calls = []
        for tool_name in required_tools:
            if tool_name in requested_tools:
                ordered_tool_calls.append(requested_tools[tool_name])
                logger.info(f"🔧 {analyst_type.upper()}: Queuing {tool_name} for parallel execution (deterministic order)")
        
        # Add any tools not in the predefined order
        for tc in tool_calls:
            if tc not in ordered_tool_calls:
                ordered_tool_calls.append(tc)
                logger.warning(f"🔧 {analyst_type.upper()}: Tool {tc['name']} not in predefined order, adding at end")
        
        # TASK 8.1.1: Create proper AIMessage with tool_calls for LangGraph tracking
        # This ensures LangGraph properly tracks our tool executions
        tool_call_message = AIMessage(
            content="",
            tool_calls=[{
                "id": tc['id'],
                "name": tc['name'], 
                "args": tc['args']
            } for tc in ordered_tool_calls]
        )
        messages.append(tool_call_message)
        logger.info(f"📊 TRACKING: Added AIMessage with {len(ordered_tool_calls)} tool calls for parallel tracking")
        
        async def execute_single_tool(tool_call):
            """Execute a single tool and return result with metadata"""
            from ..utils.tool_retry import execute_tool_with_fallback
            from ..utils.tool_cache import get_tool_cache
            
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_id = tool_call['id']
            
            tool_start = time.time()
            logger.info(f"🔧 {analyst_type.upper()}: Starting {tool_name}")
            
            try:
                tool_func = getattr(toolkit, tool_name, None)
                if tool_func is None:
                    tool_end = time.time()
                    logger.error(f"🔧 {analyst_type.upper()}: Tool {tool_name} not found")
                    
                    # TASK 6.1: Record failed execution
                    monitor.record_execution(
                        tool_name=tool_name,
                        analyst_type=analyst_type,
                        start_time=tool_start,
                        end_time=tool_end,
                        success=False,
                        error_message=f"Tool {tool_name} not found",
                        input_data=tool_args
                    )
                    
                    return ToolMessage(
                        content=f"Error: Tool {tool_name} not found",
                        tool_call_id=tool_id
                    )
                
                # OPTIMIZATION 3: Smart caching integration
                cache = get_tool_cache()
                
                def cached_execution():
                    """Wrapper for cached tool execution"""
                    # TASK 7.2: Use retry logic with fallback for parallel execution
                    # Determine fallback tool based on the primary tool
                    fallback_tool = None
                    if tool_name == "get_fundamentals_openai" and hasattr(toolkit, "get_simfin_balance_sheet"):
                        fallback_tool = toolkit.get_simfin_balance_sheet
                    elif tool_name == "get_stock_news_openai" and hasattr(toolkit, "get_reddit_stock_info"):
                        fallback_tool = toolkit.get_reddit_stock_info
                    elif tool_name == "get_global_news_openai" and hasattr(toolkit, "get_reddit_news"):
                        fallback_tool = toolkit.get_reddit_news
                    
                    # Execute with retry and fallback (this will be async but wrapped)
                    import asyncio
                    return asyncio.create_task(execute_tool_with_fallback(
                        primary_tool=tool_func,
                        fallback_tool=fallback_tool,
                        params=tool_args,
                        tool_name=tool_name
                    ))
                
                # Use cache if enabled, otherwise execute directly
                if self.config.get("enable_smart_caching", True):
                    task = cache.get_or_fetch(tool_name, tool_args, cached_execution)
                    result = await task  # Await the cached or new task
                else:
                    # Direct execution without caching
                    fallback_tool = None
                    if tool_name == "get_fundamentals_openai" and hasattr(toolkit, "get_simfin_balance_sheet"):
                        fallback_tool = toolkit.get_simfin_balance_sheet
                    elif tool_name == "get_stock_news_openai" and hasattr(toolkit, "get_reddit_stock_info"):
                        fallback_tool = toolkit.get_reddit_stock_info
                    elif tool_name == "get_global_news_openai" and hasattr(toolkit, "get_reddit_news"):
                        fallback_tool = toolkit.get_reddit_news
                    
                    result = await execute_tool_with_fallback(
                        primary_tool=tool_func,
                        fallback_tool=fallback_tool,
                        params=tool_args,
                        tool_name=tool_name
                    )
                
                tool_end = time.time()
                tool_time = tool_end - tool_start
                
                # Check if result is an error with fallback
                if isinstance(result, dict) and result.get("fallback"):
                    logger.warning(f"🔧 {analyst_type.upper()}: {tool_name} used fallback after failure")
                    # Still record as success if fallback worked
                    success = not result.get("error", "").startswith("Tool")
                else:
                    success = True
                
                # TASK 6.1: Record execution (success or failure)
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=tool_start,
                    end_time=tool_end,
                    success=success,
                    input_data=tool_args,
                    output_data=result,
                    error_message=result.get("original_error") if isinstance(result, dict) and result.get("fallback") else None
                )
                
                if success:
                    logger.info(f"🔧 {analyst_type.upper()}: ✅ {tool_name} completed in {tool_time:.2f}s")
                else:
                    logger.error(f"🔧 {analyst_type.upper()}: ❌ {tool_name} failed after retries in {tool_time:.2f}s")
                
                return ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id
                )
                
            except Exception as e:
                tool_end = time.time()
                tool_time = tool_end - tool_start
                
                # TASK 6.1: Record failed execution
                monitor.record_execution(
                    tool_name=tool_name,
                    analyst_type=analyst_type,
                    start_time=tool_start,
                    end_time=tool_end,
                    success=False,
                    error_message=str(e),
                    input_data=tool_args
                )
                
                logger.error(f"🔧 {analyst_type.upper()}: ❌ {tool_name} failed after {tool_time:.2f}s: {e}")
                return ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_id
                )
        
        # Execute all tools in parallel using asyncio.gather
        # TASK 4.3: Use ordered_tool_calls instead of tool_calls
        tool_responses = await asyncio.gather(*[
            execute_single_tool(tool_call) for tool_call in ordered_tool_calls
        ], return_exceptions=True)
        
        # Handle any exceptions from gather
        final_responses = []
        for i, response in enumerate(tool_responses):
            if isinstance(response, Exception):
                # TASK 4.3: Use ordered_tool_calls instead of tool_calls
                tool_call = ordered_tool_calls[i]
                logger.error(f"⚡ {analyst_type.upper()}: ❌ {tool_call['name']} raised exception: {response}")
                final_responses.append(ToolMessage(
                    content=f"Critical error in {tool_call['name']}: {str(response)}",
                    tool_call_id=tool_call['id']
                ))
            else:
                final_responses.append(response)
        
        parallel_time = time.time() - parallel_start
        
        # Dynamic performance targets based on analyst type
        target_times = {
            "market": 20.0,      # Market data is usually fast
            "social": 25.0,      # Social media can be slower
            "news": 30.0,        # News API can be variable
            "fundamentals": 22.0  # Existing target
        }
        target_time = target_times.get(analyst_type, 25.0)
        
        logger.info(f"⚡ {analyst_type.upper()}: Parallel execution completed in {parallel_time:.2f}s (target: <{target_time}s)")
        
        # Validate performance target
        if parallel_time < target_time:
            logger.info(f"🎯 {analyst_type.upper()}: Performance target ACHIEVED! {parallel_time:.2f}s < {target_time}s target")
        else:
            logger.warning(f"⚠️ {analyst_type.upper()}: Performance target MISSED: {parallel_time:.2f}s > {target_time}s target")
        
        updated_messages = messages + final_responses
        return {**state, message_key: updated_messages}

    def _create_dispatcher(self, selected_analysts: List[str] = None):
        """Create parallel dispatcher node - Task 1.1 Implementation"""
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals"]
        
        # Use the new SOLID-compliant parallel dispatcher
        return create_parallel_dispatcher(selected_analysts)

    def _create_aggregator(self):
        """Create aggregator node with report validation (Task 7.3)"""
        async def aggregator(state: AgentState) -> AgentState:
            logger.info("📊 AGGREGATOR: Collecting and validating reports")
            
            # TASK 6.1: Log tool health dashboard at aggregation
            from ..utils.tool_monitoring import log_tool_health_summary
            log_tool_health_summary()
            
            # OPTIMIZATION 3: Log cache performance summary
            if self.config.get("enable_smart_caching", True):
                from ..utils.tool_cache import get_tool_cache
                cache = get_tool_cache()
                cache.log_performance_summary()
            
            # OPTIMIZATION 5: Log debate optimization summary
            if self.config.get("enable_debate_optimization", True):
                from ..utils.debate_optimizer import log_debate_optimization_summary
                log_debate_optimization_summary()
            
            # TASK 7.3: Validate all analyst reports
            from ..utils.report_validator import ReportValidator
            from ..utils.tool_validator import ToolUsageValidator
            
            validations = {}
            analyst_types = ["market", "news", "social", "fundamentals"]
            
            # TASK 7.5.1: Add report readiness check
            reports_ready = 0
            report_readiness = {}
            
            for analyst in analyst_types:
                # Get report and messages
                report_key = f"{analyst}_report" if analyst != "social" else "sentiment_report"
                report = state.get(report_key, "")
                messages = state.get(f"{analyst}_messages", [])
                
                # Check if tools were used
                has_tool_data = ToolUsageValidator.validate_analyst_response(analyst, messages)
                
                # Validate report
                validation_result = ReportValidator.validate_report(analyst, report, has_tool_data)
                validations[analyst] = validation_result
                
                # Track readiness
                is_ready = validation_result.get("valid", False) and len(report) > 50
                report_readiness[analyst] = {
                    "ready": is_ready,
                    "has_report": len(report) > 0,
                    "has_tools": has_tool_data,
                    "length": len(report)
                }
                
                if is_ready:
                    reports_ready += 1
                
                # Log validation results
                if not validation_result["valid"]:
                    logger.error(f"❌ {analyst} report validation FAILED: {validation_result['issues']}")
            
            # Log readiness status
            logger.info(f"📊 AGGREGATOR: {reports_ready}/4 reports ready")
            if reports_ready < 4:
                logger.warning(f"⚠️ AGGREGATOR: Only {reports_ready}/4 reports ready - may affect downstream analysis")
            
            # Generate validation summary
            validation_summary = ReportValidator.get_validation_summary(validations)
            logger.info(f"\n{validation_summary}")
            
            updated_state = {**state}
            updated_state["report_validations"] = validations
            
            # TASK 7.5.2: Add aggregation ready flag and readiness info
            updated_state["aggregation_ready"] = reports_ready >= 3  # Allow proceeding with 3/4 reports
            updated_state["report_readiness"] = report_readiness
            
            # Initialize debate states if needed
            if "investment_debate_state" not in updated_state:
                updated_state["investment_debate_state"] = {
                    "bull_history": "",
                    "bear_history": "",
                    "history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0
                }
            
            if "risk_debate_state" not in updated_state:
                updated_state["risk_debate_state"] = {
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
            
            logger.info("📊 AGGREGATOR: ✅ All reports collected")
            return updated_state
        return aggregator


class GraphSetup:
    """Legacy wrapper for backward compatibility"""
    
    def __init__(self, quick_thinking_llm, deep_thinking_llm, config=None):
        """Initialize with dependency injection"""
        self.config = config or get_config()
        
        # Use factories for dependency injection
        self.graph_builder = GraphBuilder(
            quick_thinking_llm,
            deep_thinking_llm,
            self.config
        )
        
        logger.info("🚀 GraphSetup initialized with SOLID principles")

    def setup_graph(self, selected_analysts=None) -> CompiledStateGraph:
        """Setup graph using the SOLID-compliant builder"""
        return self.graph_builder.setup_graph(selected_analysts)
