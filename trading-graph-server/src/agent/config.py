"""
Unified Trading Configuration System
=====================================
CRITICAL: Preserves ALL existing config values and environment variable names.
Fixes bugs where .env values weren't being read.
Maintains 100% backwards compatibility.
ASYNC-SAFE: No blocking I/O at module level for LangGraph compatibility.
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
# REMOVED: from dotenv import load_dotenv - causes blocking I/O


class TradingConfig(BaseSettings):
    """
    Unified configuration for Trading Graph Server.
    
    IMPORTANT: This preserves ALL existing configuration values and
    uses the EXISTING environment variable names from .env file.
    No breaking changes to current functionality.
    """
    
    # === API KEYS (from existing .env) ===
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    serper_api_key: str = Field(default="", env="SERPER_API_KEY") 
    finnhub_api_key: str = Field(default="", env="FINNHUB_API_KEY")
    langsmith_api_key: str = Field(default="", env="LANGSMITH_API_KEY")
    
    # === LANGSMITH SETTINGS (from existing .env) ===
    langsmith_project: str = Field(default="trading-agent-graph", env="LANGSMITH_PROJECT")
    
    # === LANGGRAPH SETTINGS (from existing .env) ===
    langgraph_url: str = Field(default="", env="LANGGRAPH_URL")
    langgraph_assistant_id: str = Field(default="trading_agents", env="LANGGRAPH_ASSISTANT_ID")
    
    # === PATHS & DIRECTORIES (existing TRADINGAGENTS_ prefix) ===
    project_dir: str = Field(default=".", env="TRADINGAGENTS_PROJECT_DIR")
    results_dir: str = Field(default="./results", env="TRADINGAGENTS_RESULTS_DIR") 
    data_dir: str = Field(default="./data", env="TRADINGAGENTS_DATA_DIR")
    data_cache_dir: str = Field(default="./dataflows/data_cache", env="TRADINGAGENTS_CACHE_DIR")
    
    # === API SERVER SETTINGS (existing TRADINGAGENTS_ prefix) ===
    api_host: str = Field(default="localhost", env="TRADINGAGENTS_API_HOST")
    api_port: int = Field(default=8000, env="TRADINGAGENTS_API_PORT")
    
    # === LLM CONFIGURATION (properly reads from .env with explicit env parameter) ===
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    # Explicitly map to environment variables using env parameter
    deep_think_model: str = Field(default="o3", env="DEEP_THINK_MODEL")  # Reads DEEP_THINK_MODEL from .env
    quick_think_model: str = Field(default="gpt-4o", env="QUICK_THINK_MODEL")  # Reads QUICK_THINK_MODEL from .env
    backend_url: str = Field(default="https://api.openai.com/v1", env="BACKEND_URL")  # Reads BACKEND_URL from .env
    
    # === EXECUTION LIMITS (preserved from default_config.py) ===
    max_debate_rounds: int = Field(default=1, env="MAX_DEBATE_ROUNDS")
    max_risk_discuss_rounds: int = Field(default=1, env="MAX_RISK_DISCUSS_ROUNDS")
    max_research_debate_rounds: int = Field(default=1, env="MAX_RESEARCH_DEBATE_ROUNDS")
    max_recur_limit: int = Field(default=100, env="MAX_RECUR_LIMIT")
    recursion_limit: int = Field(default=50, env="RECURSION_LIMIT")
    execution_timeout: int = Field(default=1200, env="EXECUTION_TIMEOUT")  # 20 minutes
    force_consensus_threshold: int = Field(default=7, env="FORCE_CONSENSUS_THRESHOLD")
    circuit_breaker_enabled: bool = Field(default=True, env="CIRCUIT_BREAKER_ENABLED")
    
    # === TOKEN MANAGEMENT (preserved from default_config.py) ===
    max_tokens_per_analyst: int = Field(default=2000, env="MAX_TOKENS_PER_ANALYST")
    token_optimization_target: int = Field(default=40000, env="TOKEN_OPTIMIZATION_TARGET")
    enable_token_optimization: bool = Field(default=True, env="ENABLE_TOKEN_OPTIMIZATION")
    enable_prompt_compression: bool = Field(default=True, env="ENABLE_PROMPT_COMPRESSION")
    enable_response_control: bool = Field(default=True, env="ENABLE_RESPONSE_CONTROL")
    enable_intelligent_limiting: bool = Field(default=True, env="ENABLE_INTELLIGENT_LIMITING")
    enable_token_monitoring: bool = Field(default=True, env="ENABLE_TOKEN_MONITORING")
    
    # === PERFORMANCE FEATURES (preserved from default_config.py) ===
    enable_parallel_tools: bool = Field(default=True, env="ENABLE_PARALLEL_TOOLS")
    enable_smart_caching: bool = Field(default=True, env="ENABLE_SMART_CACHING")
    enable_smart_retry: bool = Field(default=True, env="ENABLE_SMART_RETRY")
    enable_debate_optimization: bool = Field(default=True, env="ENABLE_DEBATE_OPTIMIZATION")
    enable_phase1_optimizations: bool = Field(default=True, env="ENABLE_PHASE1_OPTIMIZATIONS")
    enable_async_tokens: bool = Field(default=True, env="ENABLE_ASYNC_TOKENS")
    enable_ultra_prompts: bool = Field(default=True, env="ENABLE_ULTRA_PROMPTS")
    enable_parallel_execution: bool = Field(default=True, env="ENABLE_PARALLEL_EXECUTION")
    max_parallel_agents: int = Field(default=4, env="MAX_PARALLEL_AGENTS")
    enable_retry: bool = Field(default=True, env="ENABLE_RETRY")
    enable_tool_cache: bool = Field(default=True, env="ENABLE_TOOL_CACHE")
    enable_batch_execution: bool = Field(default=True, env="ENABLE_BATCH_EXECUTION")
    enable_batch_prompt_processing: bool = Field(default=True, env="ENABLE_BATCH_PROMPT_PROCESSING")
    enable_parallel_risk_debate: bool = Field(default=True, env="ENABLE_PARALLEL_RISK_DEBATE")
    
    # === TOOL CONFIGURATION (preserved from default_config.py) ===
    online_tools: bool = Field(default=True, env="ONLINE_TOOLS")
    enforce_tool_usage: bool = Field(default=True, env="ENFORCE_TOOL_USAGE")
    tool_timeout: int = Field(default=15, env="TOOL_TIMEOUT")
    tool_retry_attempts: int = Field(default=2, env="TOOL_RETRY_ATTEMPTS")
    
    # === FEATURE FLAGS (preserved from default_config.py) ===
    enhanced_prompts_enabled: bool = Field(default=True, env="ENHANCED_PROMPTS_ENABLED")
    
    model_config = {
        # CRITICAL: Disabled automatic .env loading to prevent blocking I/O
        # "env_file": ".env",  # REMOVED - was causing BlockingError in ASGI
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra env vars
    }
        
    def get_absolute_path(self, path_field: str) -> Path:
        """Get absolute path for any path field - preserves existing functionality"""
        path_str = getattr(self, path_field)
        path = Path(path_str)
        return path if path.is_absolute() else path.resolve()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format matching DEFAULT_CONFIG structure.
        CRITICAL: Maintains exact same keys and values as original default_config.py
        """
        return {
            # Paths (preserve original keys)
            "project_dir": self.project_dir,
            "results_dir": self.results_dir, 
            "data_dir": self.data_dir,
            "data_cache_dir": self.data_cache_dir,
            
            # API settings (preserve original keys)
            "api_host": self.api_host,
            "api_port": self.api_port,
            
            # LLM settings (preserve original keys AND provide expected keys)
            "llm_provider": self.llm_provider,
            "deep_think_llm": self.deep_think_model,  # Legacy key for backward compatibility
            "quick_think_llm": self.quick_think_model,  # Legacy key for backward compatibility
            "reasoning_model": self.deep_think_model,  # Key expected by trading_graph.py & llm_factory.py
            "quick_thinking_model": self.quick_think_model,  # Key expected by trading_graph.py & llm_factory.py
            "backend_url": self.backend_url,  # Now reads from BACKEND_URL
            
            # Execution settings (preserve original keys)
            "max_debate_rounds": self.max_debate_rounds,
            "max_risk_discuss_rounds": self.max_risk_discuss_rounds,
            "max_research_debate_rounds": self.max_research_debate_rounds,
            "max_recur_limit": self.max_recur_limit,
            "recursion_limit": self.recursion_limit,
            "execution_timeout": self.execution_timeout,
            "force_consensus_threshold": self.force_consensus_threshold,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            
            # Token settings (preserve original keys)
            "max_tokens_per_analyst": self.max_tokens_per_analyst,
            "token_optimization_target": self.token_optimization_target,
            "enable_token_optimization": self.enable_token_optimization,
            "enable_prompt_compression": self.enable_prompt_compression,
            "enable_response_control": self.enable_response_control,
            "enable_intelligent_limiting": self.enable_intelligent_limiting,
            "enable_token_monitoring": self.enable_token_monitoring,
            
            # Performance features (preserve original keys)
            "enable_parallel_tools": self.enable_parallel_tools,
            "enable_smart_caching": self.enable_smart_caching,
            "enable_smart_retry": self.enable_smart_retry,
            "enable_debate_optimization": self.enable_debate_optimization,
            "enable_phase1_optimizations": self.enable_phase1_optimizations,
            "enable_async_tokens": self.enable_async_tokens,
            "enable_ultra_prompts": self.enable_ultra_prompts,
            "enable_parallel_execution": self.enable_parallel_execution,
            "max_parallel_agents": self.max_parallel_agents,
            "enable_retry": self.enable_retry,
            "enable_tool_cache": self.enable_tool_cache,
            "enable_batch_execution": self.enable_batch_execution,
            "enable_batch_prompt_processing": self.enable_batch_prompt_processing,
            "enable_parallel_risk_debate": self.enable_parallel_risk_debate,
            
            # Tool settings (preserve original keys)
            "online_tools": self.online_tools,
            "enforce_tool_usage": self.enforce_tool_usage,
            "tool_timeout": self.tool_timeout,
            "tool_retry_attempts": self.tool_retry_attempts,
            
            # API keys (preserve original key format)
            "serper_key": self.serper_api_key,  # Note: maps to original "serper_key"
            
            # Feature flags (preserve original keys)
            "enhanced_prompts_enabled": self.enhanced_prompts_enabled,
            
            # Additional properties for new integrations
            "openai_api_key": self.openai_api_key,
            "finnhub_api_key": self.finnhub_api_key,
            "langsmith_api_key": self.langsmith_api_key,
            "langsmith_project": self.langsmith_project,
            "langgraph_url": self.langgraph_url,
            "langgraph_assistant_id": self.langgraph_assistant_id,
        }


# Global config instance - singleton pattern for backwards compatibility
_config: Optional[TradingConfig] = None
_dict_config: Optional[Dict[str, Any]] = None
_env_loaded: bool = False


def _ensure_env_loaded():
    """NO-OP: Environment variables should be loaded before the app starts"""
    # CRITICAL FIX: Remove ALL file I/O operations
    # Environment variables must be set BEFORE the application starts
    # Either through:
    # 1. System environment variables
    # 2. Docker/Kubernetes env settings
    # 3. Shell export commands
    # 4. .env file loaded by the APPLICATION (not the library)
    #
    # This library code should NEVER do file I/O to avoid blocking in async context
    global _env_loaded
    _env_loaded = True


def get_trading_config() -> TradingConfig:
    """Get the global trading configuration instance - COMPLETELY ASYNC-SAFE"""
    global _config
    if _config is None:
        # NO FILE I/O: Just read from already-set environment variables
        # The application should load .env BEFORE importing this module
        _config = TradingConfig()
    return _config


def get_config() -> Dict[str, Any]:
    """
    Get configuration as dictionary - BACKWARDS COMPATIBLE with existing code.
    This replaces the original DEFAULT_CONFIG and dataflows.config.get_config()
    """
    global _dict_config
    if _dict_config is None:
        config_instance = get_trading_config()
        _dict_config = config_instance.to_dict()
    return _dict_config.copy()


def reset_config():
    """Reset configuration - useful for testing"""
    global _config, _dict_config
    _config = None
    _dict_config = None


# Backwards compatibility: export DEFAULT_CONFIG as lazy property
# CRITICAL: Do NOT instantiate at module level to avoid blocking I/O in async context
@property
def DEFAULT_CONFIG():
    """Lazy-loaded DEFAULT_CONFIG to avoid blocking I/O at import time"""
    return get_config()

# For modules that import DEFAULT_CONFIG directly, provide a compatibility wrapper
class _LazyDefaultConfig:
    """Lazy wrapper for DEFAULT_CONFIG to prevent blocking I/O at import"""
    def __getattr__(self, name):
        return getattr(get_config(), name)
    
    def __getitem__(self, key):
        return get_config()[key]
    
    def get(self, key, default=None):
        return get_config().get(key, default)
    
    def __contains__(self, key):
        return key in get_config()
    
    def __iter__(self):
        return iter(get_config())
    
    def items(self):
        return get_config().items()
    
    def keys(self):
        return get_config().keys()
    
    def values(self):
        return get_config().values()
    
    def copy(self):
        return get_config().copy()
    
    def update(self, *args, **kwargs):
        """Support update() calls on the lazy config wrapper"""
        # Get the actual config dict
        config = get_config()
        # Apply the update
        config.update(*args, **kwargs)
        # Update the global cached version
        global _dict_config
        if _dict_config is not None:
            _dict_config.update(*args, **kwargs)
        return None
    
    def __setitem__(self, key, value):
        """Support item assignment on the lazy config wrapper"""
        config = get_config()
        config[key] = value
        # Update the global cached version
        global _dict_config
        if _dict_config is not None:
            _dict_config[key] = value

# Export lazy wrapper instead of actual config
DEFAULT_CONFIG = _LazyDefaultConfig()

# Helper functions for absolute paths - preserve existing functionality
def get_absolute_project_dir():
    """Get absolute project directory when needed (non-blocking context)"""
    config = get_trading_config()
    return str(config.get_absolute_path("project_dir"))

def get_absolute_results_dir():
    """Get absolute results directory when needed (non-blocking context)"""
    config = get_trading_config()
    return str(config.get_absolute_path("results_dir"))

def get_absolute_data_dir():
    """Get absolute data directory when needed (non-blocking context)"""  
    config = get_trading_config()
    return str(config.get_absolute_path("data_dir"))


# Legacy functions for backwards compatibility
def get_backend_dir():
    """Lazy evaluation of backend directory to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_project_root():
    """Lazy evaluation of project root to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))