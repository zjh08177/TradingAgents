#!/usr/bin/env python3
"""
Prompt Injection Utility - Phase 3.2 Performance Optimization
Allows injecting pre-processed prompts into analyst creation functions
"""

import logging
from typing import Dict, Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Global registry for pre-processed prompts
_preprocessed_prompts: Dict[str, str] = {}


def set_preprocessed_prompts(prompts: Dict[str, str]):
    """
    Set the pre-processed prompts for injection
    
    Args:
        prompts: Dictionary mapping agent_type to processed prompt
    """
    global _preprocessed_prompts
    _preprocessed_prompts = prompts
    logger.info(f"💉 Set {len(prompts)} pre-processed prompts for injection")


def get_preprocessed_prompt(agent_type: str) -> Optional[str]:
    """
    Get a pre-processed prompt for an agent type
    
    Args:
        agent_type: Type of agent (e.g., 'market_analyst', 'news_analyst')
        
    Returns:
        Pre-processed prompt if available, None otherwise
    """
    return _preprocessed_prompts.get(agent_type)


def clear_preprocessed_prompts():
    """Clear all pre-processed prompts"""
    global _preprocessed_prompts
    _preprocessed_prompts = {}
    logger.debug("🗑️ Cleared pre-processed prompts")


def inject_preprocessed_prompt(agent_type: str):
    """
    Decorator to inject pre-processed prompts into analyst functions
    
    This decorator intercepts the prompt processing in analyst creation
    and uses pre-processed prompts when available.
    
    Args:
        agent_type: Type of agent for prompt lookup
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we have a pre-processed prompt
            preprocessed = get_preprocessed_prompt(agent_type)
            
            if preprocessed:
                logger.info(f"💉 Injecting pre-processed prompt for {agent_type}")
                # Add the preprocessed prompt to kwargs
                kwargs['_preprocessed_prompt'] = preprocessed
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class PromptInjectionContext:
    """
    Context manager for temporarily setting pre-processed prompts
    
    Usage:
        with PromptInjectionContext(prompts):
            # Create analysts with injected prompts
            create_market_analyst(llm, toolkit)
    """
    
    def __init__(self, prompts: Dict[str, str]):
        self.prompts = prompts
        self.previous_prompts = None
    
    def __enter__(self):
        global _preprocessed_prompts
        self.previous_prompts = _preprocessed_prompts.copy()
        set_preprocessed_prompts(self.prompts)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _preprocessed_prompts
        _preprocessed_prompts = self.previous_prompts
        return False


def should_use_preprocessed_prompt(agent_type: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if we should use pre-processed prompt for an agent
    
    Args:
        agent_type: Type of agent
        config: Optional configuration
        
    Returns:
        True if pre-processed prompt should be used
    """
    # Check config flag
    if config and not config.get('enable_batch_prompt_processing', True):
        return False
    
    # Check if prompt is available
    return agent_type in _preprocessed_prompts


def get_prompt_stats() -> Dict[str, Any]:
    """Get statistics about pre-processed prompts"""
    return {
        "total_prompts": len(_preprocessed_prompts),
        "agent_types": list(_preprocessed_prompts.keys()),
        "total_size": sum(len(p) for p in _preprocessed_prompts.values())
    }