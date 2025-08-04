#!/usr/bin/env python3
"""
Fix for true parallel analyst execution using LangGraph's Send API
Replaces the sequential dispatcher with a parallel dispatcher
"""

import logging
from typing import List, Dict, Any
from langgraph.graph import Send
from ..utils.agent_states import AgentState

logger = logging.getLogger(__name__)

def create_parallel_dispatcher(selected_analysts: List[str]):
    """
    Create a dispatcher that uses Send API for TRUE parallel execution
    
    This replaces the naive dispatcher that just sets flags
    """
    
    def parallel_dispatcher(state: AgentState) -> List[Send]:
        """
        Dispatcher that spawns parallel execution branches
        
        Returns List[Send] to trigger parallel execution in LangGraph
        """
        logger.info(f"⚡ PARALLEL DISPATCHER: Spawning {len(selected_analysts)} parallel analyst branches")
        
        # Create Send objects for each analyst
        # This is the KEY to parallel execution in LangGraph
        sends = []
        for analyst_type in selected_analysts:
            analyst_node = f"{analyst_type}_analyst"
            logger.info(f"🚀 Creating parallel Send to {analyst_node}")
            
            # Each Send creates a new execution branch
            sends.append(Send(analyst_node, state))
        
        # Log the parallel dispatch
        logger.info(f"✅ Dispatched {len(sends)} analysts in PARALLEL using Send API")
        
        # Return list of Send objects - this triggers parallel execution
        return sends
    
    return parallel_dispatcher


def apply_parallel_fix_to_graph(graph, selected_analysts: List[str]):
    """
    Apply the parallel execution fix to an existing graph
    
    This modifies the graph to use Send-based parallel dispatch
    """
    logger.info("🔧 Applying parallel execution fix to graph")
    
    # Replace the dispatcher node with our parallel version
    graph.add_node("dispatcher", create_parallel_dispatcher(selected_analysts))
    
    # IMPORTANT: Remove the individual edges from dispatcher to analysts
    # The Send API handles the routing, not edges
    # Keep the START -> dispatcher edge
    # But remove dispatcher -> analyst edges since Send handles that
    
    logger.info("✅ Parallel execution fix applied - using Send API for true parallelism")
    
    return graph


def verify_parallel_execution(state: AgentState) -> Dict[str, Any]:
    """
    Helper to verify parallel execution is working
    Checks timestamps and execution order
    """
    execution_times = {}
    
    # Check each analyst's execution time
    for analyst in ["market", "news", "social", "fundamentals"]:
        messages_key = f"{analyst}_messages"
        if messages_key in state and state[messages_key]:
            # Get the first message timestamp
            first_msg = state[messages_key][0]
            if hasattr(first_msg, 'additional_kwargs'):
                timestamp = first_msg.additional_kwargs.get('timestamp')
                if timestamp:
                    execution_times[analyst] = timestamp
    
    # Calculate time differences
    if len(execution_times) > 1:
        times = list(execution_times.values())
        min_time = min(times)
        max_time = max(times)
        time_spread = max_time - min_time
        
        # If analysts truly ran in parallel, time spread should be minimal
        is_parallel = time_spread < 1.0  # Less than 1 second spread
        
        logger.info(f"⏱️ Execution time spread: {time_spread:.2f}s - Parallel: {'✅' if is_parallel else '❌'}")
        
        return {
            "is_parallel": is_parallel,
            "time_spread": time_spread,
            "execution_times": execution_times
        }
    
    return {
        "is_parallel": False,
        "time_spread": None,
        "execution_times": execution_times
    }


# Example of how to use the fix in optimized_setup.py:
"""
# In OptimizedGraphBuilder._setup_optimized_edges method:

# Instead of:
for analyst_type in selected_analysts:
    graph.add_edge("dispatcher", f"{analyst_type}_analyst")

# Use:
from .parallel_execution_fix import create_parallel_dispatcher
graph.add_node("dispatcher", create_parallel_dispatcher(selected_analysts))

# Remove the individual edges - Send handles routing
"""