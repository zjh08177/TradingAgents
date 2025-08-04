#!/usr/bin/env python3
"""
Tool Execution Fix - Handles proper invocation of LangChain tools
Fixes the parameter mismatch issue when calling @tool decorated static methods
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Union
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

async def execute_tool_safely(tool_func: Union[Callable, BaseTool], tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely execute a tool function, handling both regular functions and BaseTool instances
    
    Args:
        tool_func: The tool function or BaseTool instance
        tool_call: Dictionary containing 'name', 'args', and 'id'
        
    Returns:
        Dictionary with 'content' and 'tool_call_id'
    """
    try:
        args = tool_call.get('args', {})
        
        # Check if this is a BaseTool instance
        if isinstance(tool_func, BaseTool):
            # BaseTool instances should be invoked using invoke() or run()
            logger.debug(f"Executing BaseTool {tool_call['name']} with args: {args}")
            
            # Try async invoke first (for async tools)
            if hasattr(tool_func, 'ainvoke'):
                try:
                    result = await tool_func.ainvoke(args)
                except Exception as e:
                    # If async fails, try sync in thread
                    logger.debug(f"Async invoke failed, trying sync: {e}")
                    result = await asyncio.to_thread(tool_func.invoke, args)
            else:
                # Use sync invoke in thread
                result = await asyncio.to_thread(tool_func.invoke, args)
                
        else:
            # Regular function - call directly
            logger.debug(f"Executing function {tool_call['name']} with args: {args}")
            
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**args)
            else:
                # Run sync function in thread to avoid blocking
                result = await asyncio.to_thread(tool_func, **args)
        
        return {
            "content": str(result),
            "tool_call_id": tool_call.get('id', 'unknown'),
            "success": True
        }
        
    except Exception as e:
        error_msg = f"Error executing {tool_call.get('name', 'unknown')}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Return error in a format that allows the agent to understand what went wrong
        return {
            "content": error_msg,
            "tool_call_id": tool_call.get('id', 'unknown'),
            "error": True,
            "error_type": type(e).__name__,
            "error_details": str(e)
        }


def validate_tool_response(response: Dict[str, Any], tool_name: str) -> bool:
    """
    Validate that a tool response contains actual data, not just an error
    
    Args:
        response: The tool response dictionary
        tool_name: Name of the tool for logging
        
    Returns:
        True if response contains valid data, False otherwise
    """
    if response.get('error'):
        logger.error(f"Tool {tool_name} returned an error: {response.get('content')}")
        return False
        
    content = response.get('content', '')
    
    # Check for common error patterns
    error_patterns = [
        'Error executing',
        'Error:',
        'Exception:',
        'Failed to',
        'Could not',
        'Unable to',
        'No data available',
        'Not found'
    ]
    
    content_lower = content.lower()
    for pattern in error_patterns:
        if pattern.lower() in content_lower:
            logger.warning(f"Tool {tool_name} response contains error pattern: {pattern}")
            return False
    
    # Check if response is too short to be meaningful
    if len(content.strip()) < 10:
        logger.warning(f"Tool {tool_name} response too short: {len(content)} chars")
        return False
        
    return True


async def execute_tools_with_retry(
    tool_calls: list,
    toolkit: Any,
    max_retries: int = 2
) -> list:
    """
    Execute multiple tool calls with retry logic and validation
    
    Args:
        tool_calls: List of tool call dictionaries
        toolkit: The toolkit containing the tools
        max_retries: Maximum number of retries for failed tools
        
    Returns:
        List of tool responses
    """
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        tool_func = getattr(toolkit, tool_name, None)
        
        if not tool_func:
            results.append({
                "content": f"Tool {tool_name} not found in toolkit",
                "tool_call_id": tool_call.get('id', 'unknown'),
                "error": True
            })
            continue
        
        # Try to execute with retries
        last_error = None
        for attempt in range(max_retries):
            response = await execute_tool_safely(tool_func, tool_call)
            
            if validate_tool_response(response, tool_name):
                results.append(response)
                break
            else:
                last_error = response
                if attempt < max_retries - 1:
                    logger.info(f"Retrying {tool_name} (attempt {attempt + 2}/{max_retries})")
                    await asyncio.sleep(0.5)  # Brief delay before retry
        else:
            # All retries failed
            results.append(last_error or {
                "content": f"Tool {tool_name} failed after {max_retries} attempts",
                "tool_call_id": tool_call.get('id', 'unknown'),
                "error": True
            })
    
    return results