# BACKWARDS COMPATIBILITY LAYER
# This file now imports from the unified config system but maintains all existing functionality
# IMPORTANT: All existing config values are preserved and .env integration is fixed

import os
from .config import get_config, get_trading_config, get_absolute_project_dir, get_absolute_results_dir, get_absolute_data_dir, DEFAULT_CONFIG

# BACKWARDS COMPATIBILITY: Re-export the lazy DEFAULT_CONFIG from config module
# CRITICAL: Do NOT call get_config() at module level to avoid blocking I/O
# DEFAULT_CONFIG is now imported directly from config.py where it's a lazy wrapper

# LEGACY SUPPORT: Keep original functions for any code that might be using them

# LEGACY FUNCTIONS: Preserved for backwards compatibility
def get_backend_dir():
    """Lazy evaluation of backend directory to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_project_root():
    """Lazy evaluation of project root to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
