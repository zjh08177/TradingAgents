# UPDATED TO USE UNIFIED CONFIG SYSTEM
# This maintains backwards compatibility while using the new unified configuration
# ASYNC-SAFE: No blocking I/O at module level

from ..config import get_config as get_unified_config, get_trading_config
from typing import Dict, Optional

# Backwards compatibility: maintain same interface but use unified config
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = get_unified_config()
        DATA_DIR = _config["data_dir"]


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = get_unified_config()
    _config.update(config)
    DATA_DIR = _config["data_dir"]


def get_config() -> Dict:
    """Get the current configuration."""
    global DATA_DIR
    if _config is None:
        initialize_config()
    # Ensure DATA_DIR is always set when config is accessed
    if DATA_DIR is None and _config and "data_dir" in _config:
        DATA_DIR = _config["data_dir"]
    return _config.copy()


# CRITICAL FIX: Removed module-level initialization to prevent blocking I/O
# The config will be initialized lazily on first access via get_config()
# This prevents BlockingError in LangGraph ASGI server
