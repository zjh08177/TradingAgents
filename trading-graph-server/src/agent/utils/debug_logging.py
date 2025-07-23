#!/usr/bin/env python3
"""
Comprehensive debug logging utility for LangGraph nodes and tools
"""

import functools
import logging
import time
import traceback
import json
from typing import Any, Dict, Callable
from datetime import datetime

# Configure debug logger
debug_logger = logging.getLogger('graph_debug')
debug_logger.setLevel(logging.DEBUG)

# Create console handler with detailed formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create file handler for debug logs
file_handler = logging.FileHandler('graph_debug.log')
file_handler.setLevel(logging.DEBUG)

# Create detailed formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
if not debug_logger.handlers:
    debug_logger.addHandler(console_handler)
    debug_logger.addHandler(file_handler)

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
            debug_logger.info(f"\n{'='*80}")
            debug_logger.info(f"🚀 NODE START: {name}")
            debug_logger.info(f"📋 Node ID: {node_id}")
            debug_logger.info(f"⏰ Start Time: {datetime.now().isoformat()}")
            debug_logger.info(f"{'='*80}")
            
            # Log input state (safely)
            try:
                state_summary = _summarize_state(state, f"{name}_input")
                debug_logger.info(f"📥 INPUT STATE SUMMARY:")
                debug_logger.info(f"   📊 Total Keys: {len(state.keys())}")
                debug_logger.info(f"   🔑 Available Keys: {list(state.keys())}")
                
                for key, summary in state_summary.items():
                    debug_logger.info(f"   📝 {key}: {summary}")
                    
            except Exception as e:
                debug_logger.error(f"❌ Error logging input state: {e}")
            
            try:
                # Execute the actual function
                debug_logger.info(f"⚡ EXECUTING: {name}")
                result = await func(state, *args, **kwargs)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Log successful completion
                debug_logger.info(f"✅ NODE SUCCESS: {name}")
                debug_logger.info(f"⏱️  Execution Time: {execution_time:.3f} seconds")
                
                # Log output result (safely)
                try:
                    if isinstance(result, dict):
                        result_summary = _summarize_state(result, f"{name}_output")
                        debug_logger.info(f"📤 OUTPUT SUMMARY:")
                        debug_logger.info(f"   📊 Output Keys: {len(result.keys())}")
                        debug_logger.info(f"   🔑 Result Keys: {list(result.keys())}")
                        
                        for key, summary in result_summary.items():
                            debug_logger.info(f"   📝 {key}: {summary}")
                    else:
                        debug_logger.info(f"📤 OUTPUT: {type(result).__name__} - {str(result)[:200]}...")
                        
                except Exception as e:
                    debug_logger.error(f"❌ Error logging output: {e}")
                
                debug_logger.info(f"{'='*80}")
                debug_logger.info(f"🏁 NODE COMPLETE: {name}")
                debug_logger.info(f"{'='*80}\n")
                
                return result
                
            except Exception as e:
                # Calculate execution time even on error
                execution_time = time.time() - start_time
                
                # Log error with full details
                debug_logger.error(f"\n{'!'*80}")
                debug_logger.error(f"💥 NODE ERROR: {name}")
                debug_logger.error(f"📋 Node ID: {node_id}")
                debug_logger.error(f"⏱️  Failed After: {execution_time:.3f} seconds")
                debug_logger.error(f"❌ Error Type: {type(e).__name__}")
                debug_logger.error(f"💬 Error Message: {str(e)}")
                debug_logger.error(f"📍 Error Location: {func.__name__} in {func.__module__}")
                debug_logger.error(f"🔍 Full Traceback:")
                
                # Log full traceback
                for line in traceback.format_exc().split('\n'):
                    if line.strip():
                        debug_logger.error(f"   {line}")
                
                # Log state at time of error
                try:
                    debug_logger.error(f"🗂️  STATE AT ERROR:")
                    state_at_error = _summarize_state(state, f"{name}_error")
                    for key, summary in state_at_error.items():
                        debug_logger.error(f"   📝 {key}: {summary}")
                except Exception as state_error:
                    debug_logger.error(f"❌ Could not log state at error: {state_error}")
                
                debug_logger.error(f"{'!'*80}\n")
                
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
    debug_logger.info(f"\n🔧 TOOL EXECUTION: {tool_name}")
    debug_logger.info(f"⏱️  Execution Time: {execution_time:.3f} seconds")
    
    try:
        if isinstance(input_data, dict):
            debug_logger.info(f"📥 Input Keys: {list(input_data.keys())}")
        else:
            debug_logger.info(f"📥 Input: {str(input_data)[:200]}...")
            
        if isinstance(output_data, dict):
            debug_logger.info(f"📤 Output Keys: {list(output_data.keys())}")
        else:
            debug_logger.info(f"📤 Output: {str(output_data)[:200]}...")
            
    except Exception as e:
        debug_logger.error(f"❌ Error logging tool execution: {e}")

def log_graph_state_transition(from_node: str, to_node: str, state_keys: list):
    """
    Log state transitions between nodes
    
    Args:
        from_node: Source node name
        to_node: Destination node name
        state_keys: Keys available in state
    """
    debug_logger.info(f"\n🔄 STATE TRANSITION: {from_node} → {to_node}")
    debug_logger.info(f"🔑 Available State Keys: {state_keys}")

def log_conditional_logic(condition_name: str, condition_result: str, reasoning: str = ""):
    """
    Log conditional logic decisions
    
    Args:
        condition_name: Name of the condition being evaluated
        condition_result: Result of the condition (e.g., "continue", "end")
        reasoning: Optional reasoning for the decision
    """
    debug_logger.info(f"\n🤔 CONDITIONAL: {condition_name}")
    debug_logger.info(f"🎯 Decision: {condition_result}")
    if reasoning:
        debug_logger.info(f"💭 Reasoning: {reasoning}")

def log_memory_operation(operation: str, query: str = "", results_count: int = 0):
    """
    Log memory system operations
    
    Args:
        operation: Type of memory operation (get, store, search)
        query: Query used for memory operation
        results_count: Number of results returned
    """
    debug_logger.info(f"\n🧠 MEMORY {operation.upper()}: {query}")
    debug_logger.info(f"📊 Results Count: {results_count}")

def log_llm_interaction(model: str, prompt_length: int, response_length: int, execution_time: float):
    """
    Log LLM interactions - backwards compatible version
    
    Args:
        model: LLM model name
        prompt_length: Length of prompt in characters
        response_length: Length of response in characters
        execution_time: Time taken for LLM call
    """
    debug_logger.info(f"\n🤖 LLM CALL: {model}")
    debug_logger.info(f"📝 Prompt Length: {prompt_length} chars")
    # Downgrade response length to DEBUG to avoid false warnings
    debug_logger.debug(f"📤 Response Length: {response_length} chars")  # Changed to DEBUG
    debug_logger.info(f"⏱️  LLM Time: {execution_time:.3f} seconds")

def log_llm_interaction_new(result, request_type, logger):
    """Log LLM interaction with reduced noise for empty responses - new version"""
    if hasattr(result, 'content') and result.content:
        response_length = len(result.content) if result.content else 0
        if response_length > 0:  # Only log non-empty responses
            logger.debug(f"📤 Response Length: {response_length} chars")  # Changed to DEBUG
            debug_logger.debug(f"📤 Response Length: {response_length} chars")
    
    # Log tool calls if present  
    if hasattr(result, 'tool_calls') and result.tool_calls:
        logger.info(f"🔧 Tool Calls: {len(result.tool_calls)} calls")
        debug_logger.info(f"🔧 Tool Calls: {len(result.tool_calls)} calls")

def log_data_fetch(source, data, logger):
    """Log data fetch operation with minimal noise"""
    if hasattr(data, '__len__'):
        count = len(data)
        if count > 0:
            logger.debug(f"📊 Results: {count} items")  # Changed to DEBUG
            debug_logger.debug(f"📊 Results: {count} items")
    else:
        logger.debug(f"📊 Fetched: {type(data).__name__}")
        debug_logger.debug(f"📊 Fetched: {type(data).__name__}")

def log_state_transition(state, node_name, logger):
    """Log state transition with simplified empty state handling"""
    logger.info(f"🔄 {node_name.upper()}")
    debug_logger.info(f"🔄 {node_name.upper()}")
    
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
        logger.debug(f"   📝 {key}: {format_value(value)}")
        debug_logger.debug(f"   📝 {key}: {format_value(value)}") 