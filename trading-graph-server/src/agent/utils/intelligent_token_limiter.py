#!/usr/bin/env python3
"""
Intelligent Token Limiter with Predictive Capabilities
Smart token limiting with context-aware truncation and multi-model support
"""

import logging
import re
from typing import List, Any, Dict, Optional, Tuple
import tiktoken
import threading
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

from .token_limiter import TokenLimiter

logger = logging.getLogger(__name__)

class IntelligentTokenLimiter(TokenLimiter):
    """Smart token limiting with predictive capabilities and context preservation"""
    
    def __init__(self, model_configs: Optional[Dict[str, Dict[str, int]]] = None):
        """
        Initialize with model-specific configurations
        
        Args:
            model_configs: Dict of model_name -> {max_prompt_tokens, max_response_tokens}
        """
        # Default configurations
        default_configs = {
            "gpt-4o-mini": {
                "max_prompt_tokens": 8000,
                "max_response_tokens": 2000,
                "total_context_limit": 10000
            },
            "gpt-4": {
                "max_prompt_tokens": 6000,
                "max_response_tokens": 1500,
                "total_context_limit": 8000
            },
            "gpt-3.5-turbo": {
                "max_prompt_tokens": 4000,
                "max_response_tokens": 1000,
                "total_context_limit": 5000
            }
        }
        
        self.model_configs = model_configs or default_configs
        self.current_model = "gpt-4o-mini"
        
        # Initialize base class with total limit
        super().__init__(max_tokens=self.model_configs[self.current_model]["total_context_limit"])
        
        # Prediction tracking
        self.response_history = defaultdict(list)
        self.prediction_accuracy = defaultdict(list)
        
        # Priority sections for different agent types
        self.priority_sections = {
            "market_analyst": ["recommendation", "indicators", "risk", "strategy"],
            "news_analyst": ["sentiment", "impact", "headlines", "recommendation"],
            "fundamentals_analyst": ["valuation", "metrics", "outlook", "recommendation"],
            "risk_manager": ["risks", "mitigation", "assessment", "recommendation"],
            "trader": ["decision", "entry", "exit", "position"],
            "default": ["summary", "analysis", "recommendation", "conclusion"]
        }
        
        logger.info("🧠 Intelligent Token Limiter initialized")
    
    def set_model(self, model_name: str):
        """Switch to a different model configuration"""
        if model_name in self.model_configs:
            self.current_model = model_name
            self.max_tokens = self.model_configs[model_name]["total_context_limit"]
            logger.info(f"Switched to model: {model_name}")
        else:
            logger.warning(f"Unknown model: {model_name}, keeping current settings")
    
    def predict_response_tokens(self, prompt: str, agent_type: str, 
                              context_messages: Optional[List[Dict]] = None) -> int:
        """
        Predict response token count based on history and context
        
        Args:
            prompt: The prompt being sent
            agent_type: Type of agent making the request
            context_messages: Previous messages in conversation
            
        Returns:
            Predicted token count for response
        """
        prompt_tokens = self.count_tokens(prompt)
        
        # Factor in context if provided
        context_tokens = 0
        if context_messages:
            context_tokens = sum(self.count_tokens(str(msg.get("content", ""))) 
                               for msg in context_messages)
        
        # Use historical data if available
        if agent_type in self.response_history and len(self.response_history[agent_type]) > 5:
            recent_history = self.response_history[agent_type][-10:]
            
            # Calculate average ratio with outlier removal
            ratios = [h["actual"] / h["prompt_tokens"] for h in recent_history 
                     if h["prompt_tokens"] > 0]
            
            if ratios:
                # Remove outliers
                mean_ratio = np.mean(ratios)
                std_ratio = np.std(ratios)
                filtered_ratios = [r for r in ratios 
                                 if abs(r - mean_ratio) <= 2 * std_ratio]
                
                if filtered_ratios:
                    avg_ratio = np.mean(filtered_ratios)
                    
                    # Adjust for context length
                    context_factor = 1.0
                    if context_tokens > 0:
                        # More context typically leads to shorter responses
                        context_factor = max(0.7, 1.0 - (context_tokens / 10000))
                    
                    predicted = int(prompt_tokens * avg_ratio * context_factor)
                    
                    logger.debug(f"Predicted {predicted} tokens for {agent_type} "
                               f"(ratio: {avg_ratio:.2f}, context_factor: {context_factor:.2f})")
                    
                    return predicted
        
        # Fallback predictions by agent type
        DEFAULT_RATIOS = {
            "market_analyst": 0.4,
            "news_analyst": 0.35,
            "social_media_analyst": 0.3,
            "fundamentals_analyst": 0.5,
            "risk_manager": 0.35,
            "research_manager": 0.45,
            "trader": 0.2,
            "bull_researcher": 0.4,
            "bear_researcher": 0.4
        }
        
        base_ratio = DEFAULT_RATIOS.get(agent_type, 0.4)
        
        # Adjust for prompt complexity
        complexity_factor = 1.0
        if "analyze" in prompt.lower() and "comprehensive" in prompt.lower():
            complexity_factor = 1.3
        elif "summarize" in prompt.lower() or "brief" in prompt.lower():
            complexity_factor = 0.7
        
        predicted = int(prompt_tokens * base_ratio * complexity_factor)
        
        return min(predicted, self.model_configs[self.current_model]["max_response_tokens"])
    
    def smart_truncate(self, content: str, max_tokens: int, 
                      preserve_sections: Optional[List[str]] = None,
                      agent_type: Optional[str] = None) -> str:
        """
        Intelligently truncate content while preserving key sections
        
        Args:
            content: Content to truncate
            max_tokens: Maximum token limit
            preserve_sections: Sections to prioritize (uses agent defaults if not provided)
            agent_type: Agent type for default priority sections
            
        Returns:
            Truncated content preserving important information
        """
        current_tokens = self.count_tokens(content)
        
        if current_tokens <= max_tokens:
            return content
        
        # Get priority sections
        if preserve_sections is None and agent_type:
            preserve_sections = self.priority_sections.get(agent_type, 
                                                          self.priority_sections["default"])
        elif preserve_sections is None:
            preserve_sections = self.priority_sections["default"]
        
        # Parse content into sections
        sections = self._parse_sections(content)
        
        if not sections:
            # No clear sections, do simple truncation
            return self._simple_truncate(content, max_tokens)
        
        # Separate priority and other sections
        priority_content = []
        other_content = []
        
        for section_name, section_content in sections.items():
            is_priority = any(preserve in section_name.lower() 
                            for preserve in preserve_sections)
            
            if is_priority:
                priority_content.append((section_name, section_content, 
                                       self.count_tokens(section_content)))
            else:
                other_content.append((section_name, section_content,
                                    self.count_tokens(section_content)))
        
        # Build truncated content
        result_parts = []
        current_tokens = 0
        
        # Add priority sections first (up to 70% of limit)
        priority_limit = int(max_tokens * 0.7)
        
        for name, content, tokens in priority_content:
            if current_tokens + tokens <= priority_limit:
                result_parts.append(f"### {name}\n{content}")
                current_tokens += tokens
            else:
                # Truncate this section to fit
                remaining = priority_limit - current_tokens
                if remaining > 50:  # Only add if meaningful content remains
                    truncated = self._truncate_to_tokens(content, remaining - 20)
                    result_parts.append(f"### {name}\n{truncated}\n[truncated]")
                    current_tokens = priority_limit
                break
        
        # Add other sections with remaining space
        remaining_tokens = max_tokens - current_tokens - 50  # Reserve for truncation notice
        
        for name, content, tokens in other_content:
            if tokens <= remaining_tokens:
                result_parts.append(f"### {name}\n{content}")
                remaining_tokens -= tokens
            elif remaining_tokens > 100:  # Only add if meaningful space
                truncated = self._truncate_to_tokens(content, remaining_tokens - 20)
                result_parts.append(f"### {name}\n{truncated}\n[truncated]")
                break
        
        # Add truncation notice
        if len(other_content) > len([p for p in result_parts if "###" in p]) - len(priority_content):
            result_parts.append("\n[Additional sections truncated due to token limit]")
        
        return "\n\n".join(result_parts)
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse content into sections based on headers"""
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for section headers (###, ##, #, numbered lists)
            header_match = re.match(r'^#{1,3}\s+(.+)$', line)
            numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
            
            if header_match or numbered_match:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                if header_match:
                    current_section = header_match.group(1).strip()
                else:
                    current_section = numbered_match.group(1).strip()
                
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to specific token count"""
        if max_tokens <= 0:
            return ""
        
        # Try to truncate at sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        result = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            if current_tokens + sentence_tokens <= max_tokens:
                result.append(sentence)
                current_tokens += sentence_tokens
            else:
                # Add partial sentence if space allows
                if current_tokens < max_tokens - 20:
                    words = sentence.split()
                    partial = []
                    for word in words:
                        if self.count_tokens(' '.join(partial + [word])) <= max_tokens - current_tokens - 10:
                            partial.append(word)
                        else:
                            break
                    if partial:
                        result.append(' '.join(partial) + "...")
                break
        
        return ' '.join(result)
    
    def _simple_truncate(self, text: str, max_tokens: int) -> str:
        """Simple truncation when structure parsing fails"""
        return self._truncate_to_tokens(text, max_tokens - 50) + "\n[truncated]"
    
    def check_and_prepare_context(self, messages: List[Dict[str, Any]], 
                                agent_type: str, include_prediction: bool = True) -> Dict[str, Any]:
        """
        Check token limits and prepare optimized context
        
        Returns dict with:
            - messages: Optimized message list
            - predicted_response_tokens: Expected response size
            - available_tokens: Tokens available for response
            - truncated: Whether truncation occurred
        """
        model_config = self.model_configs[self.current_model]
        
        # Calculate current usage
        prompt_tokens = self.count_messages_tokens(messages)
        
        # Predict response size
        predicted_response = 0
        if include_prediction and messages:
            last_message = messages[-1]
            prompt_content = str(last_message.get('content', ''))
            predicted_response = self.predict_response_tokens(
                prompt_content, agent_type, messages[:-1]
            )
        
        # Check if we're within limits
        total_predicted = prompt_tokens + predicted_response
        max_allowed = model_config["total_context_limit"]
        
        result = {
            "messages": messages,
            "predicted_response_tokens": predicted_response,
            "prompt_tokens": prompt_tokens,
            "available_tokens": max_allowed - prompt_tokens,
            "truncated": False
        }
        
        if total_predicted > max_allowed:
            logger.warning(f"Token limit predicted to exceed: {total_predicted} > {max_allowed}")
            
            # Calculate how much to trim
            target_prompt_tokens = max_allowed - predicted_response - 200  # Safety margin
            
            # Smart truncation preserving recent context
            optimized_messages = self._optimize_message_context(
                messages, target_prompt_tokens, agent_type
            )
            
            new_prompt_tokens = self.count_messages_tokens(optimized_messages)
            
            result.update({
                "messages": optimized_messages,
                "prompt_tokens": new_prompt_tokens,
                "available_tokens": max_allowed - new_prompt_tokens,
                "truncated": True,
                "original_tokens": prompt_tokens,
                "saved_tokens": prompt_tokens - new_prompt_tokens
            })
        
        return result
    
    def _optimize_message_context(self, messages: List[Dict[str, Any]], 
                                target_tokens: int, agent_type: str) -> List[Dict[str, Any]]:
        """Optimize message context to fit within token limit"""
        if not messages:
            return messages
        
        # Always preserve system message
        system_msgs = [m for m in messages if m.get('role') == 'system']
        other_msgs = [m for m in messages if m.get('role') != 'system']
        
        if not other_msgs:
            return system_msgs
        
        # Keep most recent messages
        preserved = system_msgs.copy()
        current_tokens = self.count_messages_tokens(preserved)
        
        # Add messages from most recent backwards
        for msg in reversed(other_msgs):
            msg_tokens = self.count_tokens(str(msg.get('content', '')))
            
            if current_tokens + msg_tokens <= target_tokens:
                preserved.insert(len(system_msgs), msg)  # Insert after system messages
                current_tokens += msg_tokens
            else:
                # Try to add truncated version
                if current_tokens < target_tokens - 100:
                    available = target_tokens - current_tokens - 50
                    truncated_content = self.smart_truncate(
                        str(msg.get('content', '')), 
                        available,
                        agent_type=agent_type
                    )
                    truncated_msg = msg.copy()
                    truncated_msg['content'] = truncated_content
                    preserved.insert(len(system_msgs), truncated_msg)
                break
        
        return preserved
    
    def record_actual_response(self, agent_type: str, prompt_tokens: int, 
                             actual_response_tokens: int, predicted_tokens: int):
        """Record actual response size for improving predictions"""
        record = {
            "prompt_tokens": prompt_tokens,
            "actual": actual_response_tokens,
            "predicted": predicted_tokens,
            "error": abs(actual_response_tokens - predicted_tokens),
            "error_rate": abs(actual_response_tokens - predicted_tokens) / actual_response_tokens 
                         if actual_response_tokens > 0 else 0,
            "timestamp": datetime.now()
        }
        
        self.response_history[agent_type].append(record)
        
        # Track prediction accuracy
        self.prediction_accuracy[agent_type].append(record["error_rate"])
        
        # Keep only recent history (last 100 records)
        if len(self.response_history[agent_type]) > 100:
            self.response_history[agent_type] = self.response_history[agent_type][-100:]
        
        if len(self.prediction_accuracy[agent_type]) > 100:
            self.prediction_accuracy[agent_type] = self.prediction_accuracy[agent_type][-100:]
        
        # Log if prediction was significantly off
        if record["error_rate"] > 0.5:
            logger.warning(f"{agent_type} prediction error: {predicted_tokens} vs {actual_response_tokens} actual")
    
    def get_prediction_accuracy_report(self) -> Dict[str, Any]:
        """Generate report on prediction accuracy"""
        report = {
            "by_agent": {},
            "overall": {
                "total_predictions": 0,
                "avg_error_rate": 0
            }
        }
        
        all_errors = []
        
        for agent_type, accuracy_history in self.prediction_accuracy.items():
            if accuracy_history:
                avg_error = np.mean(accuracy_history)
                recent_error = np.mean(accuracy_history[-10:]) if len(accuracy_history) >= 10 else avg_error
                
                report["by_agent"][agent_type] = {
                    "predictions": len(accuracy_history),
                    "avg_error_rate": round(avg_error, 3),
                    "recent_error_rate": round(recent_error, 3),
                    "improving": recent_error < avg_error
                }
                
                all_errors.extend(accuracy_history)
        
        if all_errors:
            report["overall"]["total_predictions"] = len(all_errors)
            report["overall"]["avg_error_rate"] = round(np.mean(all_errors), 3)
        
        return report

# Global instance with thread-safe initialization
_intelligent_limiter_instance = None
_intelligent_limiter_lock = threading.Lock()

def get_intelligent_token_limiter(model_configs=None):
    """Get intelligent token limiter instance"""
    global _intelligent_limiter_instance
    
    if _intelligent_limiter_instance is None:
        with _intelligent_limiter_lock:
            if _intelligent_limiter_instance is None:
                _intelligent_limiter_instance = IntelligentTokenLimiter(model_configs)
                logger.info("🧠 Created IntelligentTokenLimiter instance")
    
    return _intelligent_limiter_instance