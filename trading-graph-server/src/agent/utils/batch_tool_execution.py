"""
Batch Tool Execution Utility for Priority 2 Optimization
Executes multiple tool calls in parallel within analysts
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Callable
from .parallel_tools import execute_tools_in_parallel

logger = logging.getLogger(__name__)


async def execute_tools_parallel(tool_calls: List[Dict[str, Any]], analyst_type: str) -> List[Any]:
    """
    Execute multiple tool calls in parallel.
    
    This is the implementation for Priority 2: Batch Tool Calls in Analysts.
    Instead of sequential execution, all tools are called concurrently.
    
    Args:
        tool_calls: List of tool call specifications with 'function' callable and 'args' dict
        analyst_type: Name of the analyst for logging purposes
        
    Returns:
        List of results in the same order as tool_calls
    """
    if not tool_calls:
        return []
    
    start_time = time.time()
    logger.info(f"⚡ {analyst_type}: Starting parallel execution of {len(tool_calls)} tools")
    
    async def execute_single_tool(tool_call: Dict[str, Any], index: int) -> Any:
        """Execute a single tool call."""
        tool_func = tool_call.get('function')
        tool_args = tool_call.get('args', {})
        tool_name = getattr(tool_func, '__name__', 'unknown')
        
        tool_start = time.time()
        try:
            logger.info(f"   🔧 [{index}] Starting: {tool_name}")
            
            # Execute the tool
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_args)
            else:
                # Run sync functions in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool_func(**tool_args))
            
            duration = time.time() - tool_start
            logger.info(f"   ✅ [{index}] Completed: {tool_name} in {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - tool_start
            logger.error(f"   ❌ [{index}] Failed: {tool_name} after {duration:.2f}s - {str(e)}")
            raise
    
    # Create tasks for all tool calls
    tasks = []
    for i, tool_call in enumerate(tool_calls):
        task = asyncio.create_task(execute_single_tool(tool_call, i))
        tasks.append(task)
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Tool {i} failed with exception: {result}")
            # You might want to handle this differently based on your needs
            processed_results.append(None)
        else:
            processed_results.append(result)
    
    total_time = time.time() - start_time
    logger.info(f"⚡ {analyst_type}: Completed parallel execution in {total_time:.2f}s")
    
    return processed_results


def create_tool_batch(tool_func: Callable, args_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a batch of tool calls for the same tool with different arguments.
    
    Args:
        tool_func: The tool function to call
        args_list: List of argument dictionaries for each call
        
    Returns:
        List of tool call specifications
    """
    return [
        {'function': tool_func, 'args': args}
        for args in args_list
    ]


# For backwards compatibility and ease of use
async def execute_tools_batch(tool_calls: List[Dict[str, Any]], analyst_type: str = "Unknown") -> List[Any]:
    """
    Execute multiple tools concurrently (wrapper for execute_tools_parallel).
    
    This matches the interface suggested in the performance diagnosis document.
    """
    return await execute_tools_parallel(tool_calls, analyst_type)