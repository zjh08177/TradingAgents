"""
Custom tool wrapper to handle duplicate tool calls properly.

This wrapper ensures that every tool call gets a response, even if it's a duplicate.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode

logger = logging.getLogger(__name__)


class DedupToolNode(ToolNode):
    """
    Custom ToolNode that handles duplicate tool calls gracefully.
    
    Instead of skipping duplicate calls without a response, it returns
    a ToolMessage indicating the call was deduplicated.
    """
    
    def __init__(self, tools, *, name: str = "tools"):
        super().__init__(tools, name=name)
        self.tool_call_history: Dict[str, Any] = {}
        
    def _get_tool_call_key(self, tool_name: str, args: dict) -> str:
        """Generate a unique key for a tool call based on name and arguments."""
        # Sort args to ensure consistent keys
        sorted_args = sorted(args.items())
        return f"{tool_name}:{sorted_args}"
    
    def invoke(self, input: dict) -> dict:
        """Override invoke to handle duplicate tool calls."""
        messages = input.get("messages", [])
        
        # Find the last AI message with tool calls
        last_ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_ai_message = msg
                break
        
        if not last_ai_message or not last_ai_message.tool_calls:
            # No tool calls to process
            return {"messages": []}
        
        # Process each tool call
        tool_messages = []
        
        for tool_call in last_ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            # Generate key for deduplication
            call_key = self._get_tool_call_key(tool_name, tool_args)
            
            # Check if this exact call was made before
            if call_key in self.tool_call_history:
                logger.warning(
                    f"🔧 Duplicate tool call detected: {tool_name} with args {tool_args}. "
                    f"Returning cached result."
                )
                
                # Return a tool message indicating it's a duplicate
                cached_result = self.tool_call_history[call_key]
                tool_message = ToolMessage(
                    content=f"[CACHED RESULT - Duplicate call]\n{cached_result}",
                    tool_call_id=tool_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
            else:
                # Execute the tool normally
                try:
                    # Find the tool
                    tool_func = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            tool_func = tool
                            break
                    
                    if not tool_func:
                        raise ValueError(f"Tool {tool_name} not found")
                    
                    # Execute the tool
                    logger.info(f"🔧 Executing tool: {tool_name} with args {tool_args}")
                    result = tool_func.invoke(tool_args)
                    
                    # Cache the result
                    self.tool_call_history[call_key] = result
                    
                    # Create tool message
                    tool_message = ToolMessage(
                        content=result,
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_messages.append(tool_message)
                    
                except Exception as e:
                    logger.error(f"❌ Error executing tool {tool_name}: {e}")
                    # Return error message
                    tool_message = ToolMessage(
                        content=f"Error executing tool: {str(e)}",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_messages.append(tool_message)
        
        return {"messages": tool_messages}


class SmartToolNode(ToolNode):
    """
    Enhanced ToolNode with better error handling and logging.
    
    This version doesn't deduplicate but provides better error messages
    and ensures every tool call gets a response.
    """
    
    def __init__(self, tools, *, name: str = "tools", max_retries: int = 1):
        super().__init__(tools, name=name)
        self.max_retries = max_retries
        self.call_count = {}
        
    def invoke(self, input: dict) -> dict:
        """Override invoke to add better error handling."""
        messages = input.get("messages", [])
        
        # Find the last AI message with tool calls
        last_ai_message = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_ai_message = msg
                break
        
        if not last_ai_message or not last_ai_message.tool_calls:
            # No tool calls to process
            logger.info("🔧 No tool calls found in messages")
            return {"messages": []}
        
        logger.info(f"🔧 Processing {len(last_ai_message.tool_calls)} tool calls")
        
        # Process each tool call
        tool_messages = []
        
        for i, tool_call in enumerate(last_ai_message.tool_calls):
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            logger.info(f"🔧 [{i+1}/{len(last_ai_message.tool_calls)}] Executing {tool_name}")
            logger.info(f"   Args: {tool_args}")
            logger.info(f"   ID: {tool_id}")
            
            # Track call count
            self.call_count[tool_name] = self.call_count.get(tool_name, 0) + 1
            
            # Execute the tool with retry logic
            retries = 0
            while retries <= self.max_retries:
                try:
                    # Find the tool
                    tool_func = None
                    for tool in self.tools:
                        if tool.name == tool_name:
                            tool_func = tool
                            break
                    
                    if not tool_func:
                        raise ValueError(f"Tool {tool_name} not found in available tools")
                    
                    # Execute the tool
                    result = tool_func.invoke(tool_args)
                    
                    # Create tool message
                    tool_message = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    tool_messages.append(tool_message)
                    
                    logger.info(f"✅ Tool {tool_name} executed successfully")
                    break
                    
                except Exception as e:
                    retries += 1
                    logger.error(f"❌ Error executing tool {tool_name} (attempt {retries}/{self.max_retries + 1}): {e}")
                    
                    if retries > self.max_retries:
                        # Return error message
                        error_msg = f"Failed to execute tool after {self.max_retries + 1} attempts: {str(e)}"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                        tool_messages.append(tool_message)
                    else:
                        # Wait before retry
                        import time
                        time.sleep(1)
        
        logger.info(f"🔧 Returning {len(tool_messages)} tool messages")
        return {"messages": tool_messages}