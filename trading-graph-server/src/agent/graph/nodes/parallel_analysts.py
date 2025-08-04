"""
Parallel Analysts Executor Node
Executes all analysts (market, news, social, fundamentals) in parallel
Uses asyncio.gather() for true parallel execution
"""
import asyncio
import time
import logging
from typing import Dict, List, Callable
from ...utils.agent_states import AgentState

logger = logging.getLogger(__name__)

def create_parallel_analysts_executor(analysts_dict: Dict[str, Callable]):
    """
    Create a node that executes all analysts in parallel
    
    This replaces the sequential dispatcher->analyst flow with a single node
    that runs all analysts concurrently using asyncio.gather()
    
    Args:
        analysts_dict: Dictionary mapping analyst names to their node functions
                      e.g. {"market": market_analyst_node, "news": news_analyst_node, ...}
    
    Returns:
        Async parallel analysts executor node function
    """
    
    async def parallel_analysts_node(state: AgentState) -> AgentState:
        start_time = time.time()
        logger.info(f"⚡ PARALLEL ANALYSTS: Starting {len(analysts_dict)} analysts concurrently")
        
        # Create async tasks for each analyst
        async def run_analyst(name: str, analyst_func: Callable):
            try:
                analyst_start = time.time()
                logger.info(f"🚀 Starting {name} analyst")
                
                # Call the analyst function with state
                result = await analyst_func(state)
                
                analyst_time = time.time() - analyst_start
                logger.info(f"✅ {name} analyst completed in {analyst_time:.2f}s")
                
                return (name, result, analyst_time)
            except Exception as e:
                logger.error(f"❌ {name} analyst failed: {e}")
                return (name, None, 0)
        
        # Execute all analysts in parallel
        logger.info("🚀 Launching all analysts concurrently...")
        results = await asyncio.gather(
            *[run_analyst(name, func) for name, func in analysts_dict.items()],
            return_exceptions=True
        )
        
        # Process results and merge state updates
        merged_state = state.copy()
        successful_analysts = 0
        analyst_times = {}
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Analyst failed with exception: {result}")
                continue
            
            name, analyst_state, exec_time = result
            if analyst_state:
                successful_analysts += 1
                analyst_times[name] = exec_time
                
                # Merge the analyst's state updates
                for key, value in analyst_state.items():
                    if key != "messages":  # Don't merge message history
                        merged_state[key] = value
        
        # Performance tracking
        total_time = time.time() - start_time
        max_analyst_time = max(analyst_times.values()) if analyst_times else 0
        
        logger.info(f"⚡ PARALLEL ANALYSTS: Completed in {total_time:.2f}s")
        logger.info(f"✅ Successful analysts: {successful_analysts}/{len(analysts_dict)}")
        logger.info(f"⏱️ Max analyst time: {max_analyst_time:.2f}s")
        logger.info(f"🚀 Parallelism speedup: {sum(analyst_times.values()):.2f}s sequential → {max_analyst_time:.2f}s parallel")
        
        # Add performance metrics to state
        merged_state["parallel_analysts_metrics"] = {
            "total_time": total_time,
            "successful_count": successful_analysts,
            "analyst_times": analyst_times,
            "speedup_factor": sum(analyst_times.values()) / max_analyst_time if max_analyst_time > 0 else 1
        }
        
        # Mark as ready for aggregation
        merged_state["parallel_execution_complete"] = True
        
        return merged_state
    
    return parallel_analysts_node