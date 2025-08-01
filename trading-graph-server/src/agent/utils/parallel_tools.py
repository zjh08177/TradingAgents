"""Enhanced parallel tool execution utilities for PT1 optimization."""

import asyncio
import logging
import time
from typing import List, Dict, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


def log_parallel_execution(func: Callable) -> Callable:
    """Decorator to log parallel execution metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"⚡ Starting parallel execution: {func.__name__}")
        
        result = await func(*args, **kwargs)
        
        execution_time = time.time() - start_time
        logger.info(f"✅ Parallel execution completed: {func.__name__} in {execution_time:.2f}s")
        
        return result
    return wrapper


async def execute_tools_in_parallel(
    tool_calls: List[Dict[str, Any]], 
    toolkit: Any,
    analyst_type: str
) -> List[Dict[str, Any]]:
    """
    Execute multiple tool calls in parallel for maximum performance.
    
    This is the core of PT1 optimization - ensuring true parallel execution
    of all tool calls within an analyst.
    
    Args:
        tool_calls: List of tool call dictionaries with 'name', 'args', 'id'
        toolkit: The toolkit containing the tool implementations
        analyst_type: The type of analyst (for logging)
        
    Returns:
        List of tool results in the same order as tool_calls
    """
    logger.info(f"⚡ {analyst_type.upper()}: Executing {len(tool_calls)} tools in parallel")
    
    async def execute_single_tool(tool_call: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Execute a single tool and return result with metadata."""
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        tool_id = tool_call['id']
        
        tool_start = time.time()
        logger.info(f"🔧 [{index}] Starting tool: {tool_name}")
        
        try:
            # Get the tool from toolkit
            tool = getattr(toolkit, tool_name, None)
            if not tool:
                raise ValueError(f"Tool {tool_name} not found in toolkit")
            
            # Execute the tool
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**tool_args)
            else:
                # Run sync tools in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool(**tool_args))
            
            execution_time = time.time() - tool_start
            logger.info(f"✅ [{index}] Completed {tool_name} in {execution_time:.2f}s")
            
            return {
                'tool_id': tool_id,
                'tool_name': tool_name,
                'result': result,
                'execution_time': execution_time,
                'index': index,
                'success': True
            }
            
        except Exception as e:
            execution_time = time.time() - tool_start
            logger.error(f"❌ [{index}] Failed {tool_name} after {execution_time:.2f}s: {e}")
            
            return {
                'tool_id': tool_id,
                'tool_name': tool_name,
                'error': str(e),
                'execution_time': execution_time,
                'index': index,
                'success': False
            }
    
    # Create tasks for all tool calls
    tasks = [
        execute_single_tool(tool_call, i) 
        for i, tool_call in enumerate(tool_calls)
    ]
    
    # Execute all tasks in parallel
    parallel_start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=False)
    parallel_time = time.time() - parallel_start
    
    # Calculate speedup
    total_sequential_time = sum(r['execution_time'] for r in results)
    speedup = total_sequential_time / parallel_time if parallel_time > 0 else 1.0
    
    logger.info(
        f"⚡ {analyst_type.upper()}: Parallel execution complete! "
        f"Sequential time: {total_sequential_time:.2f}s, "
        f"Parallel time: {parallel_time:.2f}s, "
        f"Speedup: {speedup:.2f}x"
    )
    
    # Sort results back to original order
    results.sort(key=lambda x: x['index'])
    
    return results


def create_parallel_tool_executor(analyst_type: str):
    """
    Create a parallel tool executor for a specific analyst type.
    
    Args:
        analyst_type: The type of analyst (market, news, social, fundamentals)
        
    Returns:
        Async function that executes tools in parallel
    """
    @log_parallel_execution
    async def parallel_executor(tool_calls: List[Dict[str, Any]], toolkit: Any) -> List[Dict[str, Any]]:
        return await execute_tools_in_parallel(tool_calls, toolkit, analyst_type)
    
    return parallel_executor


# Utility function to batch tool calls for even better performance
def batch_tool_calls_by_type(tool_calls: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group tool calls by type for potential optimization.
    
    Some tools might benefit from batched execution (e.g., multiple indicator calls).
    
    Args:
        tool_calls: List of tool calls
        
    Returns:
        Dictionary mapping tool names to lists of calls
    """
    batches = {}
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        if tool_name not in batches:
            batches[tool_name] = []
        batches[tool_name].append(tool_call)
    
    return batches


# Export key functions
__all__ = [
    'execute_tools_in_parallel',
    'create_parallel_tool_executor',
    'batch_tool_calls_by_type',
    'log_parallel_execution'
]