import os

# FIXED: Remove blocking os.path.abspath calls from module level
# Use environment variables with safe defaults to prevent blocking operations

# Note: For LangGraph Studio, we rely on environment variables being set externally
# rather than computing paths dynamically to avoid blocking async operations

def get_backend_dir():
    """Lazy evaluation of backend directory to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_project_root():
    """Lazy evaluation of project root to prevent blocking"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ASYNC-SAFE CONFIG: Use environment variables with safe fallbacks
DEFAULT_CONFIG = {
    # Use environment variables to avoid blocking path operations
    "project_dir": os.getenv("TRADINGAGENTS_PROJECT_DIR", "."),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", "./data"),
    "data_cache_dir": os.getenv("TRADINGAGENTS_CACHE_DIR", "./dataflows/data_cache"),
    
    # API Server settings
    "api_host": os.getenv("TRADINGAGENTS_API_HOST", "localhost"),
    "api_port": int(os.getenv("TRADINGAGENTS_API_PORT", "8000")),
    
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o1",
    "quick_think_llm": "gpt-4o",
    "backend_url": "https://api.openai.com/v1",
    
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_research_debate_rounds": 1,  # Default to 1 for performance (was 3)
    "max_recur_limit": 100,
    
    # Research debate is now always parallel - no timeout or waiting needed
    
    # Token limits
    "max_tokens_per_analyst": 2000,  # Task C4: Token limit per analyst
    "execution_timeout": 120,  # Task C3: Execution timeout in seconds
    
    # Token optimization settings
    "enable_token_optimization": True,  # Enable comprehensive token optimization
    "enable_prompt_compression": True,  # Enable prompt compression (22%+ reduction)
    "enable_response_control": True,  # Enable response word limits
    "enable_intelligent_limiting": True,  # Enable predictive token limiting
    "token_optimization_target": 40000,  # Target tokens per complete run
    "enable_token_monitoring": True,  # Track and report token usage
    
    # Feature toggles
    # Risk debate is now always parallel - sequential mode removed
    "enable_parallel_tools": True,  # Optimization 2: Enable parallel tool execution for all analysts
    "enable_smart_caching": True,  # Optimization 3: Enable smart caching for tool results (~10s savings)
    "enable_smart_retry": True,  # Optimization 4: Enable smart retry logic to skip unnecessary retries
    "enable_debate_optimization": True,  # Optimization 5: Enable multi-round debate optimization
    
    # Tool settings
    "online_tools": True,
    
    # Serper API settings
    "serper_key": os.getenv("SERPER_API_KEY", ""),
}

# Helper functions for when absolute paths are needed
def get_absolute_project_dir():
    """Get absolute project directory when needed (non-blocking context)"""
    base = DEFAULT_CONFIG["project_dir"]
    if os.path.isabs(base):
        return base
    return os.path.abspath(base)

def get_absolute_results_dir():
    """Get absolute results directory when needed (non-blocking context)"""
    base = DEFAULT_CONFIG["results_dir"]
    if os.path.isabs(base):
        return base
    return os.path.abspath(base)

def get_absolute_data_dir():
    """Get absolute data directory when needed (non-blocking context)"""
    base = DEFAULT_CONFIG["data_dir"]
    if os.path.isabs(base):
        return base
    return os.path.abspath(base)
