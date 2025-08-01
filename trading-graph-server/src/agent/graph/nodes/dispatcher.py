"""
Dispatcher Node - SOLID Compliant Implementation with Send-based Parallelism
Single Responsibility: Coordinate parallel analyst execution
Open/Closed: Extensible for new analyst types
Liskov Substitution: Compatible with node interface
Interface Segregation: Focused dispatcher interface
Dependency Inversion: Depends on abstractions
"""

import logging
import time
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage
# from langgraph.types import Send  # Not needed with direct edge approach

from ...utils.agent_states import AgentState
from ...utils.debug_logging import debug_node

logger = logging.getLogger(__name__)


class IDispatcher:
    """Interface for dispatcher implementations - Interface Segregation"""
    
    async def dispatch_analysts(self, state: AgentState) -> AgentState:
        """Dispatch work to analysts in parallel"""
        raise NotImplementedError


class ParallelDispatcher(IDispatcher):
    """
    Parallel Dispatcher implementation following SOLID principles
    
    Single Responsibility: Coordinates parallel analyst execution
    Open/Closed: Extensible for new analyst types without modification
    Liskov Substitution: Can be substituted for any IDispatcher
    Interface Segregation: Only implements necessary dispatcher methods
    Dependency Inversion: Depends on IDispatcher abstraction
    """
    
    def __init__(self, selected_analysts: List[str] = None):
        """Initialize dispatcher with analyst selection
        
        Args:
            selected_analysts: List of analyst types to coordinate
        """
        self.selected_analysts = selected_analysts or ["market", "social", "news", "fundamentals"]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info(f"🚀 ParallelDispatcher initialized for analysts: {self.selected_analysts}")
    
    async def dispatch_analysts(self, state: AgentState) -> AgentState:
        """
        Dispatch analysts for parallel execution
        
        This is the core of Task 1.1 - enabling true parallel execution
        by initializing all analyst message channels simultaneously
        """
        company = state.get("company_of_interest", "")
        trade_date = state.get("trade_date", "")
        
        self.logger.info("🚀 PARALLEL DISPATCHER: Starting coordinated analysis")
        self.logger.info(f"   📊 Company: {company}")
        self.logger.info(f"   📅 Date: {trade_date}")
        self.logger.info(f"   👥 Analysts: {len(self.selected_analysts)} parallel")
        
        # Create initial message for all analysts to start their work
        initial_message = HumanMessage(
            content=f"""Begin comprehensive analysis for {company} on {trade_date}.
            
            You are part of a parallel analysis team. Conduct your specialized analysis independently:
            - Use your dedicated tools to gather data
            - Provide thorough analysis within your domain
            - Generate a complete report with actionable insights
            
            Company: {company}
            Analysis Date: {trade_date}
            """
        )
        
        # Initialize separate message channels for parallel execution
        # This is the key architectural change from conditional routing to true parallel
        updated_state = dict(state)
        
        # Initialize all analyst message channels simultaneously
        for analyst_type in self.selected_analysts:
            message_key = f"{analyst_type}_messages"
            updated_state[message_key] = [initial_message]
            
            self.logger.info(f"   ✅ {analyst_type}_messages initialized for parallel execution")
        
        # Initialize report fields
        for analyst_type in self.selected_analysts:
            report_mapping = {
                "market": "market_report",
                "social": "sentiment_report", 
                "news": "news_report",
                "fundamentals": "fundamentals_report"
            }
            
            report_key = report_mapping.get(analyst_type, f"{analyst_type}_report")
            updated_state[report_key] = ""
        
        self.logger.info("🚀 PARALLEL DISPATCHER: All analysts initialized for simultaneous execution")
        self.logger.info("   ⚡ True parallel execution enabled - no sequential dependencies")
        
        return updated_state


def create_parallel_dispatcher(selected_analysts: List[str] = None) -> callable:
    """
    Factory function to create parallel dispatcher node
    
    This implementation relies on direct graph edges for true parallel execution
    of all analysts. The graph setup creates edges from dispatcher to all analysts,
    which LangGraph executes in parallel automatically.
    
    Args:
        selected_analysts: List of analyst types to coordinate
        
    Returns:
        Async function compatible with LangGraph node interface that returns state dict
    """
    selected_analysts = selected_analysts or ["market", "social", "news", "fundamentals"]
    
    @debug_node("Parallel_Dispatcher")
    async def parallel_dispatcher_node(state: AgentState) -> Dict[str, Any]:
        """
        Parallel dispatcher for true concurrent execution
        
        This is the key fix for Task 1.1 - the graph has direct edges from
        dispatcher to all analysts, which LangGraph executes in parallel automatically.
        """
        start_time = time.time()
        
        company = state.get("company_of_interest", "")
        trade_date = state.get("trade_date", "")
        
        logger.info("⚡ PARALLEL DISPATCHER: Starting TRUE parallel execution")
        logger.info(f"   📊 Company: {company}")
        logger.info(f"   📅 Date: {trade_date}")
        logger.info(f"   👥 Analysts: {len(selected_analysts)} parallel")
        logger.info(f"⏱️ Dispatcher START: {time.time()}")
        
        # Create initial message for all analysts
        initial_message = HumanMessage(
            content=f"""Begin comprehensive analysis for {company} on {trade_date}.
            
            You are part of a parallel analysis team. Conduct your specialized analysis independently:
            - Use your dedicated tools to gather data
            - Provide thorough analysis within your domain
            - Generate a complete report with actionable insights
            
            Company: {company}
            Analysis Date: {trade_date}
            """
        )
        
        # Prepare state with initialized message channels
        prepared_state = dict(state)
        for analyst_type in selected_analysts:
            message_key = f"{analyst_type}_messages"
            prepared_state[message_key] = [initial_message]
            
            # Initialize report fields
            report_mapping = {
                "market": "market_report",
                "social": "sentiment_report", 
                "news": "news_report",
                "fundamentals": "fundamentals_report"
            }
            report_key = report_mapping.get(analyst_type, f"{analyst_type}_report")
            prepared_state[report_key] = ""
        
        # Log the prepared state for all analysts
        for analyst_type in selected_analysts:
            logger.info(f"   🚀 Initialized {analyst_type}_analyst for parallel execution")
        
        duration = time.time() - start_time
        logger.info(f"⏱️ Dispatcher END: {time.time()} (duration: {duration:.2f}s)")
        logger.info(f"⚡ PARALLEL DISPATCHER: {len(selected_analysts)} analysts initialized")
        logger.info("   ✅ All analysts will execute CONCURRENTLY via graph edges!")
        
        # Return the prepared state - graph edges handle parallel execution
        return prepared_state
    
    return parallel_dispatcher_node


# Legacy compatibility - maintains existing interface
def create_dispatcher(selected_analysts: List[str] = None) -> callable:
    """Legacy compatibility wrapper"""
    return create_parallel_dispatcher(selected_analysts)


class DispatcherFactory:
    """
    Factory for creating different dispatcher types
    Follows Open/Closed Principle - extensible for new dispatcher types
    """
    
    @staticmethod
    def create_parallel_dispatcher(selected_analysts: List[str] = None) -> callable:
        """Create parallel dispatcher"""
        return create_parallel_dispatcher(selected_analysts)
    
    @staticmethod
    def create_sequential_dispatcher(selected_analysts: List[str] = None) -> callable:
        """Create sequential dispatcher (for backward compatibility)"""
        # Could implement sequential version here if needed
        logger.warning("Sequential dispatcher requested - falling back to parallel")
        return create_parallel_dispatcher(selected_analysts)


# Module-level factory instance
dispatcher_factory = DispatcherFactory()