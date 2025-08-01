"""
Message validation utility for OpenAI API compliance
"""
import logging
from typing import List, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)

def validate_message_sequence(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Validate and fix message sequence for OpenAI API compliance.
    
    OpenAI rules:
    1. Messages with role 'tool' must follow a preceding message with 'tool_calls'
    2. AI messages with 'tool_calls' must be followed by ToolMessages for each tool_call_id
    """
    if not messages:
        return messages
    
    validated_messages = []
    i = 0
    
    while i < len(messages):
        msg = messages[i]
        
        # Check if this is an AI message with tool_calls
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Add the AI message
            validated_messages.append(msg)
            i += 1
            
            # Collect expected tool_call_ids
            expected_tool_ids = set()
            for tc in msg.tool_calls:
                if hasattr(tc, 'id'):
                    expected_tool_ids.add(tc.id)
                elif isinstance(tc, dict) and 'id' in tc:
                    expected_tool_ids.add(tc['id'])
                else:
                    logger.warning(f"🔧 Tool call missing id: {tc}")
            
            # Look for ToolMessages that respond to these tool_calls
            tool_responses = []
            while i < len(messages) and hasattr(messages[i], 'type') and messages[i].type == 'tool':
                tool_msg = messages[i]
                if hasattr(tool_msg, 'tool_call_id') and tool_msg.tool_call_id in expected_tool_ids:
                    tool_responses.append(tool_msg)
                    expected_tool_ids.discard(tool_msg.tool_call_id)
                i += 1
            
            # Add the valid tool responses
            validated_messages.extend(tool_responses)
            
            # Create dummy responses for missing tool_call_ids
            for missing_id in expected_tool_ids:
                logger.warning(f"🔧 Creating dummy ToolMessage for missing tool_call_id: {missing_id}")
                validated_messages.append(ToolMessage(
                    content="Tool execution completed",
                    tool_call_id=missing_id
                ))
            
            # Don't increment i here as we've already processed the tool messages
            continue
            
        # Check if this is a ToolMessage
        elif hasattr(msg, 'type') and msg.type == 'tool':
            # Check if previous message has tool_calls
            if len(validated_messages) == 0:
                # ToolMessage at start - convert to HumanMessage
                logger.warning(f"🔧 Converting ToolMessage at start to HumanMessage: {msg.content[:100]}...")
                validated_messages.append(HumanMessage(content=f"Tool result: {msg.content}"))
            else:
                prev_msg = validated_messages[-1]
                # More thorough check for tool_calls
                has_tool_calls = False
                if hasattr(prev_msg, 'tool_calls'):
                    has_tool_calls = prev_msg.tool_calls and len(prev_msg.tool_calls) > 0
                elif hasattr(prev_msg, 'additional_kwargs') and 'tool_calls' in prev_msg.additional_kwargs:
                    has_tool_calls = len(prev_msg.additional_kwargs['tool_calls']) > 0
                
                logger.debug(f"🔧 Checking ToolMessage {i}: prev_msg={type(prev_msg).__name__}, has_tool_calls={has_tool_calls}")
                
                if has_tool_calls:
                    # Valid ToolMessage following tool_calls
                    validated_messages.append(msg)
                else:
                    # Invalid ToolMessage - convert to HumanMessage 
                    logger.warning(f"🔧 Converting orphaned ToolMessage to HumanMessage: {msg.content[:100]}...")
                    validated_messages.append(HumanMessage(content=f"Tool result: {msg.content}"))
        else:
            # Non-tool message - keep as is
            validated_messages.append(msg)
        
        i += 1
    
    if len(validated_messages) != len(messages):
        logger.info(f"🔧 Message validation: {len(messages)} -> {len(validated_messages)} messages")
    
    return validated_messages

def clean_messages_for_llm(messages: List[Any]) -> List[BaseMessage]:
    """
    Clean and validate messages before sending to LLM
    """
    if not messages:
        logger.info("🔧 clean_messages_for_llm: No messages to clean")
        return []
    
    logger.info(f"🔧 clean_messages_for_llm: Processing {len(messages)} messages")
    
    # Convert to BaseMessage objects if needed
    clean_messages = []
    for i, msg in enumerate(messages):
        if isinstance(msg, BaseMessage):
            logger.debug(f"🔧 Message {i}: {type(msg).__name__} - {getattr(msg, 'type', 'no_type')}")
            clean_messages.append(msg)
        elif isinstance(msg, dict):
            # Convert dict to appropriate message type
            role = msg.get('role', 'human')
            content = msg.get('content', str(msg))
            logger.debug(f"🔧 Message {i}: Dict with role={role}")
            
            if role == 'user' or role == 'human':
                clean_messages.append(HumanMessage(content=content))
            elif role == 'assistant' or role == 'ai':
                clean_messages.append(AIMessage(content=content))
            elif role == 'tool':
                # Convert tool role to human for safety
                logger.warning(f"🔧 Converting dict tool message to HumanMessage: {content[:100]}...")
                clean_messages.append(HumanMessage(content=f"Tool result: {content}"))
            else:
                clean_messages.append(HumanMessage(content=content))
        else:
            # Convert other types to string content
            logger.debug(f"🔧 Message {i}: {type(msg).__name__} -> HumanMessage")
            clean_messages.append(HumanMessage(content=str(msg)))
    
    logger.info(f"🔧 clean_messages_for_llm: Converted to {len(clean_messages)} BaseMessages")
    
    # Validate sequence
    validated = validate_message_sequence(clean_messages)
    logger.info(f"🔧 clean_messages_for_llm: Final output {len(validated)} messages")
    return validated