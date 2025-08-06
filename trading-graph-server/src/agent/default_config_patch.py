# Configuration updates to fix graph execution issues
# Add these to your default_config.py or config files

GRAPH_EXECUTION_CONFIG = {
    # Graph execution limits
    "recursion_limit": 50,  # Increase from default 25 to handle complex debates
    "execution_timeout": 1200,  # 20 minutes for complex analysis with multiple LLM calls and parallel processing
    
    # Tool enforcement
    "enforce_tool_usage": True,  # Force analysts to use tools
    "tool_timeout": 15,  # Timeout for individual tool calls
    "tool_retry_attempts": 2,  # Retry failed tool calls
    
    # Research debate configuration  
    "max_debate_rounds": 3,  # Maximum rounds before forcing consensus
    "force_consensus_threshold": 7,  # Force consensus if quality score >= 7
    "circuit_breaker_enabled": True,  # Enable circuit breaker for infinite loops
    "circuit_breaker_max_attempts": 5,  # Max attempts before forcing exit
    
    # Performance optimization
    "enable_send_api": True,  # Use enhanced graph builder by default
    "enable_enhanced_monitoring": True,  # Enhanced performance monitoring
    "enable_fallback": True,  # Fallback strategies for failures
    
    # Token and performance targets
    "max_tokens_per_analyst": 4000,
    "max_total_tokens": 40000,
    "target_runtime_seconds": 1200,
}

# Update existing DEFAULT_CONFIG
DEFAULT_CONFIG.update(GRAPH_EXECUTION_CONFIG)

# Alternative: Merge into existing config
# DEFAULT_CONFIG = {
#     **DEFAULT_CONFIG,
#     **GRAPH_EXECUTION_CONFIG
# }