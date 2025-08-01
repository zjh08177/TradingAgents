"""
Token limiting utility for enforcing token limits on LLM interactions
"""
import logging
from typing import List, Any, Dict, Optional
import tiktoken
import asyncio
import threading

logger = logging.getLogger(__name__)

class TokenLimiter:
    """Enforces token limits on messages and responses"""
    
    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens
        self._encoding = None  # Lazy initialization
        self._lock = threading.Lock()  # Thread-safe lazy loading
    
    @property
    def encoding(self):
        """Lazy load tiktoken encoding to avoid blocking calls at module init"""
        if self._encoding is None:
            with self._lock:
                if self._encoding is None:  # Double-check pattern
                    try:
                        # This is the blocking call we defer until first use
                        self._encoding = tiktoken.encoding_for_model("gpt-4")
                        logger.info("✅ Tiktoken encoding loaded successfully")
                    except Exception as e:
                        logger.error(f"Failed to load tiktoken encoding: {e}")
                        # Fallback to a simple encoding if tiktoken fails
                        self._encoding = None
                        raise
        return self._encoding
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using approximation: {e}")
            # Fallback: approximate 1 token per 4 characters
            return len(text) // 4
    
    def count_messages_tokens(self, messages: List[Any]) -> int:
        """Count total tokens in a list of messages"""
        total_tokens = 0
        for msg in messages:
            if hasattr(msg, 'content'):
                total_tokens += self.count_tokens(str(msg.content))
            elif isinstance(msg, dict) and 'content' in msg:
                total_tokens += self.count_tokens(str(msg['content']))
            else:
                total_tokens += self.count_tokens(str(msg))
        return total_tokens
    
    def check_and_enforce_limit(self, messages: List[Any], component: str = "Unknown") -> List[Any]:
        """Check token limit and truncate if necessary"""
        total_tokens = self.count_messages_tokens(messages)
        
        if total_tokens > self.max_tokens:
            logger.warning(f"⚠️ Token limit exceeded: {component} used {total_tokens} > {self.max_tokens}")
            logger.warning(f"🚨 TOKEN LIMIT EXCEEDED: {total_tokens} tokens")
            
            # Truncate messages from the beginning (keep most recent)
            truncated_messages = []
            current_tokens = 0
            
            # Process messages in reverse order (keep most recent)
            for msg in reversed(messages):
                msg_tokens = self.count_tokens(str(msg.content if hasattr(msg, 'content') else msg))
                if current_tokens + msg_tokens <= self.max_tokens:
                    truncated_messages.insert(0, msg)
                    current_tokens += msg_tokens
                else:
                    # Add truncation notice
                    if truncated_messages and len(truncated_messages) > 0:
                        logger.warning(f"📋 Truncated {len(messages) - len(truncated_messages)} messages to fit token limit")
                    break
            
            return truncated_messages
        
        return messages
    
    def truncate_response(self, response: str, component: str = "Unknown") -> str:
        """Truncate a response to fit within token limits"""
        response_tokens = self.count_tokens(response)
        
        if response_tokens > self.max_tokens:
            logger.warning(f"⚠️ Response token limit exceeded: {component} generated {response_tokens} > {self.max_tokens}")
            
            # Truncate response to fit limit
            words = response.split()
            truncated = []
            current_tokens = 0
            
            for word in words:
                word_tokens = self.count_tokens(word + " ")
                if current_tokens + word_tokens <= self.max_tokens - 50:  # Leave some buffer
                    truncated.append(word)
                    current_tokens += word_tokens
                else:
                    truncated.append("... [TRUNCATED DUE TO TOKEN LIMIT]")
                    break
            
            return " ".join(truncated)
        
        return response

# Global instance with config-based limit
_token_limiter_instance = None
_token_limiter_lock = threading.Lock()

def get_token_limiter(config=None):
    """Get token limiter with config-based max tokens"""
    global _token_limiter_instance
    
    if _token_limiter_instance is None:
        with _token_limiter_lock:
            if _token_limiter_instance is None:
                if config:
                    max_tokens = config.get('max_tokens_per_analyst', 2000)
                else:
                    max_tokens = 2000
                _token_limiter_instance = TokenLimiter(max_tokens=max_tokens)
                logger.info(f"🔧 Created TokenLimiter instance with {max_tokens} max tokens")
    
    return _token_limiter_instance

# Lazy global instance property
@property
def token_limiter():
    """Lazy-loaded default token limiter instance"""
    return get_token_limiter()

# For backward compatibility, create a module-level getter
class _TokenLimiterModule:
    @property
    def token_limiter(self):
        return get_token_limiter()

# Replace module to support property access
import sys
sys.modules[__name__].__dict__['token_limiter'] = property(lambda self: get_token_limiter())