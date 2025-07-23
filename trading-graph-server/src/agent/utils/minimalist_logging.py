#!/usr/bin/env python3
"""
Minimalist logging utility for LangGraph nodes and tools.
Stores only the first 200 words of model responses.
Logs: node ID, request, truncated response, duration, start & finish timestamps.
"""

import functools
import logging
import time
import json
from typing import Any, Dict, Callable, Optional
from datetime import datetime
import os


# Configure minimalist logger
min_logger = logging.getLogger('minimalist_debug')
min_logger.setLevel(logging.INFO)

# Create file handler for minimalist logs
log_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
log_file = os.path.join(log_dir, 'minimalist_debug.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create simple formatter  
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
if not min_logger.handlers:
    min_logger.addHandler(file_handler)


def truncate_to_words(text: str, max_words: int = 200) -> str:
    """Truncate text to first N words."""
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'


def log_llm_call(
    node_id: str,
    request: str,
    response: str,
    duration: float,
    start_time: datetime,
    end_time: datetime,
    agent_name: Optional[str] = None
):
    """
    Log LLM call with minimalist format.
    
    Args:
        node_id: Unique identifier for the node
        request: The request/prompt sent to LLM
        response: The response from LLM (will be truncated)
        duration: Duration in seconds
        start_time: Start timestamp
        end_time: End timestamp
        agent_name: Optional agent name for identification
    """
    truncated_response = truncate_to_words(response, 200)
    
    log_entry = {
        "type": "llm_call",
        "node_id": node_id,
        "agent": agent_name or "unknown",
        "request": request[:500],  # Limit request to 500 chars
        "response": truncated_response,
        "duration": round(duration, 3),
        "start": start_time.isoformat(),
        "finish": end_time.isoformat()
    }
    
    min_logger.info(json.dumps(log_entry))


def log_tool_call(
    node_id: str,
    tool_name: str,
    tool_input: Any,
    tool_output: Any,
    duration: float,
    start_time: datetime,
    end_time: datetime,
    agent_name: Optional[str] = None
):
    """
    Log tool call with minimalist format.
    
    Args:
        node_id: Unique identifier for the node
        tool_name: Name of the tool being called
        tool_input: Input to the tool
        tool_output: Output from the tool
        duration: Duration in seconds
        start_time: Start timestamp
        end_time: End timestamp
        agent_name: Optional agent name for identification
    """
    # Truncate tool output if it's a string
    if isinstance(tool_output, str):
        tool_output = truncate_to_words(tool_output, 200)
    else:
        tool_output = str(tool_output)[:500]  # Limit other types to 500 chars
    
    log_entry = {
        "type": "tool_call", 
        "node_id": node_id,
        "agent": agent_name or "unknown",
        "tool": tool_name,
        "input": str(tool_input)[:500],  # Limit input to 500 chars
        "output": tool_output,
        "duration": round(duration, 3),
        "start": start_time.isoformat(),
        "finish": end_time.isoformat()
    }
    
    min_logger.info(json.dumps(log_entry))


def minimalist_node(name: str):
    """
    Decorator for minimalist logging of node execution.
    
    Args:
        name: Human-readable name of the node/agent
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(state: Dict[str, Any], *args, **kwargs):
            start_time = datetime.now()
            start_timestamp = time.time()
            node_id = f"{name}_{int(start_timestamp * 1000)}"
            
            try:
                # Execute the actual function
                result = await func(state, *args, **kwargs)
                
                # Calculate execution time
                end_time = datetime.now()
                duration = time.time() - start_timestamp
                
                # Log node execution summary
                log_entry = {
                    "type": "node_execution",
                    "node_id": node_id,
                    "agent": name,
                    "status": "success",
                    "duration": round(duration, 3),
                    "start": start_time.isoformat(),
                    "finish": end_time.isoformat()
                }
                
                min_logger.info(json.dumps(log_entry))
                
                return result
                
            except Exception as e:
                # Log error
                end_time = datetime.now()
                duration = time.time() - start_timestamp
                
                log_entry = {
                    "type": "node_execution",
                    "node_id": node_id,
                    "agent": name,
                    "status": "error",
                    "error": str(e),
                    "duration": round(duration, 3),
                    "start": start_time.isoformat(),
                    "finish": end_time.isoformat()
                }
                
                min_logger.info(json.dumps(log_entry))
                raise
                
        return wrapper
    return decorator


class MinimalistLogInterceptor:
    """
    Interceptor to capture and log LLM/tool calls with minimalist format.
    Can be used to wrap existing LLM or tool instances.
    """
    
    def __init__(self, wrapped_object: Any, agent_name: str = "unknown"):
        self.wrapped = wrapped_object
        self.agent_name = agent_name
    
    async def ainvoke(self, *args, **kwargs):
        """Async invoke with logging."""
        start_time = datetime.now()
        start_timestamp = time.time()
        node_id = f"{self.agent_name}_{int(start_timestamp * 1000)}"
        
        # Extract request/prompt
        request = ""
        if args and hasattr(args[0], '__iter__'):
            request = str(args[0])[:500]
        elif 'messages' in kwargs:
            request = str(kwargs['messages'])[:500]
        
        try:
            # Call the wrapped method
            result = await self.wrapped.ainvoke(*args, **kwargs)
            
            # Extract response
            response = ""
            if hasattr(result, 'content'):
                response = result.content
            else:
                response = str(result)
            
            # Log the call
            end_time = datetime.now()
            duration = time.time() - start_timestamp
            
            log_llm_call(
                node_id=node_id,
                request=request,
                response=response,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                agent_name=self.agent_name
            )
            
            return result
            
        except Exception as e:
            # Log error
            end_time = datetime.now()
            duration = time.time() - start_timestamp
            
            log_entry = {
                "type": "llm_error",
                "node_id": node_id,
                "agent": self.agent_name,
                "error": str(e),
                "duration": round(duration, 3),
                "start": start_time.isoformat(),
                "finish": end_time.isoformat()
            }
            
            min_logger.info(json.dumps(log_entry))
            raise
    
    def __getattr__(self, name):
        """Forward all other attributes to wrapped object."""
        return getattr(self.wrapped, name)