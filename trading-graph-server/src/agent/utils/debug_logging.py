#!/usr/bin/env python3
"""
Debug logging utility for LangGraph trading agents.
Provides comprehensive debugging and monitoring for node execution and tool calls.
FIXED: Lazy initialization to prevent blocking calls in Studio async environment.
"""

import functools
import logging
import time
import json
import traceback
from typing import Any, Dict, Callable, Optional
from datetime import datetime
import os


# Configure main logger - NOTE: No file handler at module level to prevent blocking
logger = logging.getLogger('trading_graph_debug')
logger.setLevel(logging.DEBUG)

def _format_value(value):
    """Format values for logging display"""
    if isinstance(value, str):
        return value[:100] + "..." if len(value) > 100 else value
    elif isinstance(value, (list, dict)):
        return f"{type(value).__name__}(len={len(value)})"
    else:
        return str(value)[:50]

# Console handler (non-blocking)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# LAZY FILE HANDLER: Prevents blocking calls during module import
_file_handler = None

def get_file_handler():
    """Lazy initialization of file handler to prevent blocking in Studio"""
    global _file_handler
    if _file_handler is None:
        try:
            # Use environment variable for log file location if available
            log_file = os.getenv('TRADINGAGENTS_LOG_FILE', 'graph_debug.log')
            _file_handler = logging.FileHandler(log_file)
            _file_handler.setLevel(logging.DEBUG)
            
            # Create detailed formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            _file_handler.setFormatter(formatter)
            
        except Exception as e:
            # Fallback to NullHandler if file operations fail in Studio
            _file_handler = logging.NullHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s [FILE_LOGGING_DISABLED: %(exc_info)s]'
            ))
    
    return _file_handler

# Create formatter for console
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
console_handler.setFormatter(formatter)

# Add console handler immediately (non-blocking)
if not logger.handlers:
    logger.addHandler(console_handler)

def ensure_file_logging():
    """Ensure file logging is set up (call when needed)"""
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = get_file_handler()
        if not isinstance(file_handler, logging.NullHandler):
            logger.addHandler(file_handler)

def debug_node(name: str):
    """
    Decorator to log node execution with comprehensive debugging info
    
    Args:
        name: Human-readable name of the node/tool
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(state: Dict[str, Any], *args, **kwargs):
            start_time = time.time()
            node_id = f"{name}_{int(start_time * 1000)}"
            
            # Log node start
            logger.info(f"\n{'='*80}")
            logger.info(f"🚀 NODE START: {name}")
            logger.info(f"📋 Node ID: {node_id}")
            logger.info(f"⏰ Start Time: {datetime.now().isoformat()}")
            logger.info(f"{'='*80}")
            
            # Log input state (safely)
            try:
                state_summary = _summarize_state(state, f"{name}_input")
                logger.info(f"📥 INPUT STATE SUMMARY:")
                logger.info(f"   📊 Total Keys: {len(state.keys())}")
                logger.info(f"   🔑 Available Keys: {list(state.keys())}")
                
                for key, summary in state_summary.items():
                    logger.info(f"   📝 {key}: {summary}")
                    
            except Exception as e:
                logger.error(f"❌ Error logging input state: {e}")
            
            try:
                # Execute the actual function
                logger.info(f"⚡ EXECUTING: {name}")
                result = await func(state, *args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log successful completion
                logger.info(f"✅ NODE SUCCESS: {name}")
                logger.info(f"⏱️  Execution Time: {execution_time:.3f} seconds")
                
                # Log output result (safely)
                try:
                    if isinstance(result, dict):
                        result_summary = _summarize_state(result, f"{name}_output")
                        logger.info(f"📤 OUTPUT SUMMARY:")
                        logger.info(f"   📊 Output Keys: {len(result.keys())}")
                        logger.info(f"   🔑 Result Keys: {list(result.keys())}")
                        
                        for key, summary in result_summary.items():
                            logger.info(f"   📝 {key}: {summary}")
                    else:
                        logger.info(f"📤 OUTPUT: {type(result).__name__} - {str(result)[:200]}...")
                        
                except Exception as e:
                    logger.error(f"❌ Error logging output: {e}")
                
                logger.info(f"{'='*80}")
                logger.info(f"🏁 NODE COMPLETE: {name}")
                logger.info(f"{'='*80}\n")
                
                return result
                
            except Exception as e:
                # Calculate execution time even on error
                execution_time = time.time() - start_time
                
                # Log error with full details
                logger.error(f"\n{'!'*80}")
                logger.error(f"💥 NODE ERROR: {name}")
                logger.error(f"📋 Node ID: {node_id}")
                logger.error(f"⏱️  Failed After: {execution_time:.3f} seconds")
                logger.error(f"❌ Error Type: {type(e).__name__}")
                logger.error(f"💬 Error Message: {str(e)}")
                logger.error(f"📍 Error Location: {func.__name__} in {func.__module__}")
                logger.error(f"🔍 Full Traceback:")
                
                # Log full traceback
                for line in traceback.format_exc().split('\n'):
                    if line.strip():
                        logger.error(f"   {line}")
                
                # Log state at time of error
                try:
                    logger.error(f"🗂️  STATE AT ERROR:")
                    state_at_error = _summarize_state(state, f"{name}_error")
                    for key, summary in state_at_error.items():
                        logger.error(f"   📝 {key}: {summary}")
                except Exception as state_error:
                    logger.error(f"❌ Could not log state at error: {state_error}")
                
                logger.error(f"{'!'*80}\n")
                
                # Re-raise the original exception
                raise
                
        return wrapper
    return decorator

def _summarize_state(state: Dict[str, Any], context: str) -> Dict[str, str]:
    """
    Create a safe summary of state dictionary with size limits
    
    Args:
        state: State dictionary to summarize
        context: Context for logging (e.g., "node_input", "node_output")
    
    Returns:
        Dictionary with summarized values
    """
    summary = {}
    
    for key, value in state.items():
        try:
            # Skip empty initial states to eliminate false warnings
            if context.endswith("_input"):
                if key.endswith('_report') and isinstance(value, str) and len(value) == 0:
                    continue  # Skip empty reports in input state
                if key.endswith('_messages') and isinstance(value, list) and len(value) == 0:
                    continue  # Skip empty message lists in input state
                if key.endswith('_state') and isinstance(value, dict) and len(value) == 0:
                    continue  # Skip empty debate states in input state
                if key == 'investment_plan' and isinstance(value, str) and len(value) == 0:
                    continue  # Skip empty investment plan in input state
            
            if value is None:
                summary[key] = "None"
            elif isinstance(value, str):
                if len(value) > 200:
                    summary[key] = f"String({len(value)} chars): {value[:200]}..."
                else:
                    summary[key] = f"String({len(value)} chars): {value}"
            elif isinstance(value, (int, float, bool)):
                summary[key] = f"{type(value).__name__}: {value}"
            elif isinstance(value, (list, tuple)):
                summary[key] = f"{type(value).__name__}({len(value)} items): {str(value)[:100]}..."
            elif isinstance(value, dict):
                summary[key] = f"Dict({len(value)} keys): {list(value.keys())}"
            else:
                summary[key] = f"{type(value).__name__}: {str(value)[:100]}..."
                
        except Exception as e:
            summary[key] = f"Error summarizing: {e}"
    
    return summary

def log_tool_execution(tool_name: str, input_data: Any, output_data: Any, execution_time: float):
    """
    Log tool execution details
    
    Args:
        tool_name: Name of the tool
        input_data: Input to the tool
        output_data: Output from the tool  
        execution_time: Time taken to execute
    """
    logger.info(f"\n🔧 TOOL EXECUTION: {tool_name}")
    logger.info(f"⏱️  Execution Time: {execution_time:.3f} seconds")
    
    try:
        if isinstance(input_data, dict):
            logger.info(f"📥 Input Keys: {list(input_data.keys())}")
        else:
            logger.info(f"📥 Input: {str(input_data)[:200]}...")
            
        if isinstance(output_data, dict):
            logger.info(f"📤 Output Keys: {list(output_data.keys())}")
        else:
            logger.info(f"📤 Output: {str(output_data)[:200]}...")
            
    except Exception as e:
        logger.error(f"❌ Error logging tool execution: {e}")

def log_graph_state_transition(from_node: str, to_node: str, state_keys: list):
    """
    Log state transitions between nodes
    
    Args:
        from_node: Source node name
        to_node: Destination node name
        state_keys: Keys available in state
    """
    logger.info(f"\n🔄 STATE TRANSITION: {from_node} → {to_node}")
    logger.info(f"🔑 Available State Keys: {state_keys}")

def log_conditional_logic(condition_name: str, condition_result: str, reasoning: str = ""):
    """
    Log conditional logic decisions
    
    Args:
        condition_name: Name of the condition being evaluated
        condition_result: Result of the condition (e.g., "continue", "end")
        reasoning: Optional reasoning for the decision
    """
    logger.info(f"\n🤔 CONDITIONAL: {condition_name}")
    logger.info(f"🎯 Decision: {condition_result}")
    if reasoning:
        logger.info(f"💭 Reasoning: {reasoning}")

def log_memory_operation(operation: str, query: str = "", results_count: int = 0):
    """
    Log memory system operations
    
    Args:
        operation: Type of memory operation (get, store, search)
        query: Query used for memory operation
        results_count: Number of results returned
    """
    logger.info(f"\n🧠 MEMORY {operation.upper()}: {query}")
    logger.info(f"📊 Results Count: {results_count}")

def log_llm_interaction(model: str, prompt_length: int, response_length: int, execution_time: float):
    """
    Log LLM interactions - backwards compatible version
    
    Args:
        model: LLM model name
        prompt_length: Length of prompt in characters
        response_length: Length of response in characters
        execution_time: Time taken for LLM call
    """
    logger.info(f"\n🤖 LLM CALL: {model}")
    logger.info(f"📝 Prompt Length: {prompt_length} chars")
    # Downgrade response length to DEBUG to avoid false warnings
    logger.debug(f"📤 Response Length: {response_length} chars")  # Changed to DEBUG
    logger.info(f"⏱️  LLM Time: {execution_time:.3f} seconds")

def log_llm_interaction_new(result, request_type, logger):
    """Log LLM interaction with reduced noise for empty responses - new version"""
    if hasattr(result, 'content') and result.content:
        response_length = len(result.content) if result.content else 0
        if response_length > 0:  # Only log non-empty responses
            logger.debug(f"📤 Response Length: {response_length} chars")  # Changed to DEBUG
            logger.debug(f"📤 Response Length: {response_length} chars")
    
    # Log tool calls if present  
    if hasattr(result, 'tool_calls') and result.tool_calls:
        logger.info(f"🔧 Tool Calls: {len(result.tool_calls)} calls")
        logger.info(f"🔧 Tool Calls: {len(result.tool_calls)} calls")

def log_data_fetch(source, data, logger):
    """Log data fetch operation with minimal noise"""
    if hasattr(data, '__len__'):
        count = len(data)
        if count > 0:
            logger.debug(f"📊 Results: {count} items")  # Changed to DEBUG
            logger.debug(f"📊 Results: {count} items")
    else:
        logger.debug(f"📊 Fetched: {type(data).__name__}")
        logger.debug(f"📊 Fetched: {type(data).__name__}")

def log_state_transition(state, node_name, logger):
    """Log state transition with simplified empty state handling"""
    logger.info(f"🔄 {node_name.upper()}")
    logger.info(f"🔄 {node_name.upper()}")
    
    # Log state details - completely skip empty initial values
    for key, value in state.items():
        # Skip all empty initial states to eliminate false warnings
        if key.endswith('_report') and isinstance(value, str) and len(value) == 0:
            continue  # Skip empty reports entirely
        if key.endswith('_messages') and isinstance(value, list) and len(value) == 0:
            continue  # Skip empty message lists entirely
        if key.endswith('_state') and isinstance(value, dict) and len(value) == 0:
            continue  # Skip empty debate states entirely
        if key == 'investment_plan' and isinstance(value, str) and len(value) == 0:
            continue  # Skip empty investment plan entirely
            
        # Only log non-empty values
        logger.debug(f"   📝 {key}: {_format_value(value)}") 