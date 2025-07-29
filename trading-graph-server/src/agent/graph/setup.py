"""
Trading Graph Setup - SOLID-compliant Architecture
Single responsibility for graph construction with dependency injection
"""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from ..utils.agent_states import AgentState
from ..utils.agent_utils import Toolkit
from ..interfaces import ILLMProvider, IMemoryProvider, IAnalystToolkit, IGraphBuilder
from ..factories.llm_factory import LLMFactory
from ..factories.memory_factory import MemoryFactory
from ..factories.toolkit_factory import ToolkitFactory
from ..dataflows.config import get_config

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
from ..risk_mgmt.aggresive_debator import create_risky_debator
from ..risk_mgmt.conservative_debator import create_safe_debator
from ..risk_mgmt.neutral_debator import create_neutral_debator

logger = logging.getLogger(__name__)

class GraphBuilder(IGraphBuilder):
    """SOLID-compliant graph builder with dependency injection"""
    
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,
                 deep_thinking_llm: ILLMProvider,
                 config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.config = config
        
        # Create base toolkit and factories
        self.base_toolkit = Toolkit(self.config)
        self.toolkit_factory = ToolkitFactory()
        self.memory_factory = MemoryFactory()
        
        logger.info("🚀 GraphBuilder initialized with dependency injection")

    def setup_graph(self, selected_analysts: List[str] = None) -> CompiledStateGraph:
        """Build the complete graph following SOLID principles"""
        if selected_analysts is None:
            selected_analysts = ["market", "social", "news", "fundamentals"]
        
        logger.info(f"🚀 Building SOLID-compliant graph with analysts: {selected_analysts}")
        
        graph = StateGraph(AgentState)
        
        # Add core nodes
        self._add_core_nodes(graph)
        
        # Add analyst nodes based on selection
        self._add_analyst_nodes(graph, selected_analysts)
        
        # Add remaining workflow nodes
        self._add_workflow_nodes(graph)
        
        # Setup edges
        self._setup_edges(graph, selected_analysts)
        
        logger.info("✅ SOLID-compliant graph constructed successfully")
        return graph.compile()

    def _add_core_nodes(self, graph: StateGraph):
        """Add core dispatcher and aggregator nodes"""
        graph.add_node("dispatcher", self._create_dispatcher())
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
        
        graph.add_node("market_analyst", analyst)
        graph.add_node("market_tools", tools)
        
        # Add conditional routing
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
        
        graph.add_node("social_analyst", analyst)
        graph.add_node("social_tools", tools)
        
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
        
        graph.add_node("news_analyst", analyst)
        graph.add_node("news_tools", tools)
        
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
        
        graph.add_node("fundamentals_analyst", analyst)
        graph.add_node("fundamentals_tools", tools)
        
        graph.add_conditional_edges("fundamentals_analyst", self._create_analyst_routing("fundamentals"), {
            "fundamentals_tools": "fundamentals_tools", 
            "aggregator": "aggregator"
        })
        graph.add_edge("fundamentals_tools", "fundamentals_analyst")

    def _add_workflow_nodes(self, graph: StateGraph):
        """Add core workflow nodes (research, risk, trading)"""
        # Research workflow
        graph.add_node("bull_researcher", create_bull_researcher(self.deep_thinking_llm, self.memory_factory.create_research_memory(self.config)))
        graph.add_node("bear_researcher", create_bear_researcher(self.deep_thinking_llm, self.memory_factory.create_research_memory(self.config)))
        graph.add_node("research_manager", create_research_manager(self.deep_thinking_llm, self.memory_factory.create_research_memory(self.config)))
        
        # Risk workflow
        graph.add_node("aggressive_debator", create_risky_debator(self.deep_thinking_llm))
        graph.add_node("conservative_debator", create_safe_debator(self.deep_thinking_llm))
        graph.add_node("neutral_debator", create_neutral_debator(self.deep_thinking_llm))
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
        """Setup graph edges for workflow"""
        # Setup main dispatcher
        graph.add_edge(START, "dispatcher")
        
        # Dispatcher to all analysts
        for analyst_type in selected_analysts:
            graph.add_edge("dispatcher", f"{analyst_type}_analyst")
          
        # Aggregator to research workflow
        graph.add_edge("aggregator", "bull_researcher")
        
        # Research workflow edges  
        graph.add_edge("bull_researcher", "bear_researcher")
        graph.add_edge("bear_researcher", "research_manager")
        
        # Risk workflow edges
        graph.add_edge("research_manager", "aggressive_debator")
        graph.add_edge("aggressive_debator", "conservative_debator")
        graph.add_edge("conservative_debator", "neutral_debator")
        graph.add_edge("neutral_debator", "risk_aggregator")
        graph.add_edge("risk_aggregator", "risk_manager")
        graph.add_edge("risk_manager", "trader")
        graph.add_edge("trader", END)

    def _create_analyst_routing(self, analyst_type: str):
        """Create routing logic for analyst nodes with loop prevention"""
        def route(state: AgentState) -> str:
            messages = state.get(f"{analyst_type}_messages", [])
            if not messages:
                return "aggregator"
            
            # Count tool calls to prevent infinite loops
            tool_call_count = sum(1 for msg in messages if hasattr(msg, 'tool_calls') and msg.tool_calls)
            
            # Limit to max 3 tool call cycles per analyst to prevent recursion
            if tool_call_count >= 3:
                return "aggregator"
            
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return f"{analyst_type}_tools"
            return "aggregator"
        
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

    async def _execute_tools(self, state: AgentState, toolkit: IAnalystToolkit, message_key: str) -> AgentState:
        """Common tool execution logic following DRY principle"""
        messages = state.get(message_key, [])
        if not messages:
            return state
            
        last_message = messages[-1]
        tool_calls = getattr(last_message, 'tool_calls', [])
        
        if not tool_calls:
            return state
        
        from langchain_core.messages import ToolMessage
        tool_responses = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_id = tool_call['id']
            
            logger.info(f"🔧 TOOLS: Executing {tool_name}")
            
            try:
                tool_func = getattr(toolkit, tool_name, None)
                if tool_func is None:
                    logger.error(f"🔧 TOOLS: Tool {tool_name} not found")
                    continue
                
                result = await tool_func.ainvoke(tool_args)
                tool_responses.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id
                ))
                logger.info(f"🔧 TOOLS: ✅ {tool_name} completed")
                
            except Exception as e:
                logger.error(f"🔧 TOOLS: ❌ {tool_name} failed: {e}")
                tool_responses.append(ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_id
                ))
        
        updated_messages = messages + tool_responses
        return {**state, message_key: updated_messages}

    def _create_dispatcher(self):
        """Create dispatcher node"""
        async def dispatcher(state: AgentState) -> AgentState:
            logger.info("🚀 DISPATCHER: Starting analysis")
            company = state.get("company_of_interest", "")
            date = state.get("trade_date", "")
            logger.info(f"🚀 Company: {company}, Date: {date}")
            return state
        return dispatcher

    def _create_aggregator(self):
        """Create aggregator node"""
        async def aggregator(state: AgentState) -> AgentState:
            logger.info("📊 AGGREGATOR: Collecting reports")
            updated_state = {**state}
            
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
