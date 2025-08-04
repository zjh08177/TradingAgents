#!/usr/bin/env python3
"""
Safe State Access Wrapper - Defensive State Management
Prevents KeyError issues by providing safe access patterns for all state fields
"""

import logging
from typing import Dict, Any, Optional, Union
from ..utils.agent_states import AgentState

logger = logging.getLogger(__name__)

class SafeStateWrapper:
    """
    Defensive wrapper for state access that prevents KeyError exceptions
    Provides backward compatibility and safe field access patterns
    """
    
    def __init__(self, state: AgentState):
        self._state = state
        self._field_mappings = {
            # Backward compatibility mappings
            "market_research_report": "market_report",
            "sentiment_analysis_report": "sentiment_report", 
            "social_analysis_report": "sentiment_report",
            "news_analysis_report": "news_report",
            "fundamentals_analysis_report": "fundamentals_report"
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Safe get method with backward compatibility mapping
        """
        # First try the direct key
        if key in self._state:
            return self._state[key]
        
        # Try mapped key for backward compatibility
        mapped_key = self._field_mappings.get(key)
        if mapped_key and mapped_key in self._state:
            logger.debug(f"🔄 State access: mapping '{key}' → '{mapped_key}'")
            return self._state[mapped_key]
        
        # Return default if nothing found
        logger.debug(f"⚠️ State field '{key}' not found, using default: {default}")
        return default
    
    def safe_format_dict(self) -> Dict[str, Any]:
        """
        Create a safe dictionary for f-string formatting that includes all possible field names
        """
        format_dict = dict(self._state)
        
        # Add backward compatibility aliases
        for old_key, new_key in self._field_mappings.items():
            if new_key in self._state:
                format_dict[old_key] = self._state[new_key]
            else:
                format_dict[old_key] = ""
        
        # Ensure all common fields have safe defaults
        safe_defaults = {
            "market_report": "",
            "market_research_report": "",
            "sentiment_report": "",
            "social_analysis_report": "",
            "news_report": "", 
            "news_analysis_report": "",
            "fundamentals_report": "",
            "fundamentals_analysis_report": "",
            "investment_plan": "",
            "trader_investment_plan": "",
            "company_of_interest": "UNKNOWN",
            "trade_date": ""
        }
        
        for key, default in safe_defaults.items():
            if key not in format_dict:
                format_dict[key] = default
        
        return format_dict
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-style access with safe fallback"""
        return self.get(key, "")
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator"""
        return key in self._state or key in self._field_mappings

def create_safe_state_wrapper(state: AgentState) -> SafeStateWrapper:
    """Factory function to create safe state wrapper"""
    return SafeStateWrapper(state)

def safe_state_get(state: AgentState, key: str, default: Any = None) -> Any:
    """
    Utility function for safe state access without creating wrapper object
    """
    wrapper = SafeStateWrapper(state)
    return wrapper.get(key, default)

def get_safe_format_vars(state: AgentState) -> Dict[str, Any]:
    """
    Get a safe dictionary for use in f-string formatting
    Prevents KeyError by ensuring all possible field names are present
    """
    wrapper = SafeStateWrapper(state)
    return wrapper.safe_format_dict()