# Trading Graph Server Configuration Guide

## Overview

The Trading Graph Server uses a unified configuration system built on Pydantic Settings that provides:
- **Environment variable-based configuration** with `.env` file support
- **Async-safe implementation** to avoid blocking I/O in ASGI/LangGraph contexts
- **Backwards compatibility** with legacy code
- **Type validation** and automatic conversion
- **Centralized configuration management**

## Source of Truth

The configuration system's source of truth is located at:
```
src/agent/config.py
```

This file contains the `TradingConfig` class which defines all configuration options and their defaults.

## Configuration Hierarchy

Configuration values are loaded in the following priority order (highest to lowest):

1. **Environment Variables** - Set directly in the shell
2. **`.env` File** - Local environment file (not committed to git)
3. **Default Values** - Hardcoded defaults in `TradingConfig` class

## How Configuration Works

### 1. Configuration Loading Process

```python
# The configuration is loaded lazily to avoid blocking I/O
from src.agent.config import get_trading_config, DEFAULT_CONFIG

# Get configuration as Pydantic model
config = get_trading_config()  # Returns TradingConfig instance

# Get configuration as dictionary (backwards compatible)
config_dict = DEFAULT_CONFIG  # Returns dict with all settings
```

### 2. Async-Safe Implementation

The configuration system uses lazy loading to prevent `BlockingError` in async contexts:

- Configuration is NOT loaded at module import time
- `.env` file is loaded in a thread when first accessed
- Safe for use in ASGI applications and LangGraph

### 3. Environment Variable Mapping

Pydantic reads environment variables through explicit `env` parameter in Field definitions:
```python
# Correct - uses env parameter to map to environment variable
deep_think_model: str = Field(default="o1", env="DEEP_THINK_MODEL")

# Incorrect - will NOT read from environment (missing env parameter)
deep_think_model: str = Field(default="o1")  # ❌ Won't read DEEP_THINK_MODEL
```

### 4. Backwards Compatibility

The system maintains 100% backwards compatibility through:
- `DEFAULT_CONFIG` wrapper that behaves like a dictionary
- `to_dict()` method that maps new field names to legacy keys
- Support for all existing environment variable names

## Configuration Categories

### API Keys
```bash
# OpenAI (Required for LLM operations)
OPENAI_API_KEY=your_openai_key_here

# Serper (Required for web search)
SERPER_API_KEY=your_serper_key_here

# Finnhub (Optional - financial data)
FINNHUB_API_KEY=your_finnhub_key_here

# LangSmith (Optional - tracing)
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=trading-agent-graph
```

### LLM Configuration
```bash
# Model selection (FIXED: Now properly read by application)
DEEP_THINK_MODEL=o1              # Complex analysis (o1, o3, gpt-4o, etc.)
QUICK_THINK_MODEL=gpt-4o         # Routine tasks (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)
LLM_PROVIDER=openai              # Provider selection
BACKEND_URL=https://api.openai.com/v1

# Note: These map to both legacy keys (deep_think_llm) and 
# expected keys (reasoning_model) for full compatibility
```

### Paths & Directories
```bash
TRADINGAGENTS_PROJECT_DIR=.
TRADINGAGENTS_RESULTS_DIR=./results
TRADINGAGENTS_DATA_DIR=./data
TRADINGAGENTS_CACHE_DIR=./dataflows/data_cache
```

### Execution Limits
```bash
MAX_DEBATE_ROUNDS=3               # Bull/bear debate rounds
MAX_RISK_DISCUSS_ROUNDS=1         # Risk discussion rounds
MAX_RESEARCH_DEBATE_ROUNDS=3      # Research debate rounds
RECURSION_LIMIT=50                # LangGraph recursion limit
EXECUTION_TIMEOUT=1200            # Total timeout (seconds)
FORCE_CONSENSUS_THRESHOLD=7       # Force consensus if quality >= threshold
CIRCUIT_BREAKER_ENABLED=true      # Prevent infinite loops
```

### Token Management
```bash
MAX_TOKENS_PER_ANALYST=2000       # Per-analyst token limit
TOKEN_OPTIMIZATION_TARGET=40000   # Target for complete run
ENABLE_TOKEN_OPTIMIZATION=true    # Enable optimization
ENABLE_PROMPT_COMPRESSION=true    # 22%+ reduction
ENABLE_RESPONSE_CONTROL=true      # Length control
ENABLE_INTELLIGENT_LIMITING=true  # Predictive limiting
ENABLE_TOKEN_MONITORING=true      # Usage tracking
```

### Performance Features
```bash
ENABLE_PARALLEL_TOOLS=true        # Parallel tool execution
ENABLE_SMART_CACHING=true         # Cache tool results
ENABLE_SMART_RETRY=true           # Skip unnecessary retries
ENABLE_DEBATE_OPTIMIZATION=true   # Multi-round optimization
ENABLE_PHASE1_OPTIMIZATIONS=true  # 50% performance improvement
ENABLE_ASYNC_TOKENS=true          # 40% runtime reduction
ENABLE_ULTRA_PROMPTS=true         # 75% token reduction
ENABLE_PARALLEL_EXECUTION=true    # 2-3x speedup
MAX_PARALLEL_AGENTS=4             # Concurrent agents
```

### Tool Configuration
```bash
ONLINE_TOOLS=true                 # Enable web search/APIs
ENFORCE_TOOL_USAGE=true           # Require tool usage
TOOL_TIMEOUT=15                   # Individual tool timeout (seconds)
TOOL_RETRY_ATTEMPTS=2             # Retry failed tools
```

## How to Modify Configuration

### Method 1: Environment Variables (Recommended for Production)

Set environment variables before running the application:

```bash
export OPENAI_API_KEY="sk-..."
export DEEP_THINK_MODEL="o3"
export MAX_DEBATE_ROUNDS=5
python debug_local.sh AAPL
```

### Method 2: .env File (Recommended for Development)

1. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

2. Edit `.env` with your values:
```bash
# .env
OPENAI_API_KEY=sk-your-key-here
SERPER_API_KEY=your-serper-key
DEEP_THINK_MODEL=o1
QUICK_THINK_MODEL=gpt-4o-mini
MAX_DEBATE_ROUNDS=5
ENABLE_PARALLEL_EXECUTION=true
```

3. The configuration will automatically load from `.env`

### Method 3: Programmatic Override (For Testing)

```python
from src.agent.config import get_trading_config, DEFAULT_CONFIG

# Get config instance
config = get_trading_config()

# Override specific values (dictionary interface)
DEFAULT_CONFIG["max_debate_rounds"] = 5
DEFAULT_CONFIG["deep_think_llm"] = "o3"

# Or update multiple values
DEFAULT_CONFIG.update({
    "max_debate_rounds": 5,
    "enable_parallel_execution": False
})
```

## Configuration Validation

The system includes automatic validation at startup:

1. **Type Validation**: Pydantic automatically validates and converts types
2. **API Key Validation**: Checks for required API keys
3. **Path Validation**: Ensures directories exist or can be created
4. **Range Validation**: Ensures numeric values are within acceptable ranges

## Common Configuration Scenarios

### Development Setup
```bash
# Minimal .env for development
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
ENABLE_TOKEN_MONITORING=true
ENABLE_PHASE1_OPTIMIZATIONS=false  # Disable for debugging
```

### Production Setup
```bash
# Optimized .env for production
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
FINNHUB_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=production

# Performance settings
ENABLE_PHASE1_OPTIMIZATIONS=true
ENABLE_PARALLEL_EXECUTION=true
MAX_PARALLEL_AGENTS=8
ENABLE_SMART_CACHING=true

# Tighter limits
MAX_DEBATE_ROUNDS=2
EXECUTION_TIMEOUT=600
```

### Testing Setup
```bash
# .env for testing
OPENAI_API_KEY=sk-test-...
ONLINE_TOOLS=false  # Disable external APIs
ENABLE_RETRY=false  # Fail fast
EXECUTION_TIMEOUT=60  # Quick timeout
MAX_DEBATE_ROUNDS=1  # Minimal rounds
```

## Troubleshooting

### Issue: LLM model settings not being applied (e.g., DEEP_THINK_MODEL)
**Solution**: This has been fixed. The configuration now properly maps:
- `DEEP_THINK_MODEL` → `reasoning_model` (used by application)
- `QUICK_THINK_MODEL` → `quick_thinking_model` (used by application)

If still not working, verify:
1. Environment variable is set: `echo $DEEP_THINK_MODEL`
2. No typos in variable name (case-sensitive)
3. Restart application after changing .env

### Issue: BlockingError in async context
**Solution**: The configuration system is async-safe. Ensure you're using `get_trading_config()` or `DEFAULT_CONFIG` instead of directly instantiating `TradingConfig()`.

### Issue: Environment variables not being read
**Solution**: 
1. Check that `.env` file exists in project root
2. Verify variable names match exactly (case-sensitive)
3. Ensure no spaces around `=` in `.env` file
4. Check that values don't have quotes unless needed

### Issue: Configuration changes not taking effect
**Solution**:
1. Restart the application after changing `.env`
2. If using programmatic updates, ensure they happen before the code uses the values
3. Check that the correct configuration is being imported

## Configuration Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use `.env.example`** as a template with dummy values
3. **Set production values via environment variables**, not `.env` files
4. **Validate API keys at startup** to fail fast
5. **Use appropriate models** - `o1` for complex analysis, `gpt-4o-mini` for simple tasks
6. **Monitor token usage** with `ENABLE_TOKEN_MONITORING=true`
7. **Enable caching** in production with `ENABLE_SMART_CACHING=true`
8. **Set reasonable timeouts** to prevent hanging operations

## Advanced Configuration

### Custom Configuration Extensions

To add new configuration options:

1. Add field to `TradingConfig` class:
```python
class TradingConfig(BaseSettings):
    # Your new field
    my_new_setting: str = Field(default="default_value", env="MY_NEW_SETTING")
```

2. Update `to_dict()` method if needed for backwards compatibility:
```python
def to_dict(self):
    return {
        # ... existing fields ...
        "my_new_setting": self.my_new_setting,
    }
```

3. Use in your code:
```python
from src.agent.config import get_trading_config

config = get_trading_config()
value = config.my_new_setting
```

### Configuration Profiles

Create different configuration profiles for different environments:

```bash
# .env.development
DEEP_THINK_MODEL=gpt-4o  # Cheaper for development
ENABLE_PHASE1_OPTIMIZATIONS=false
MAX_DEBATE_ROUNDS=1

# .env.production  
DEEP_THINK_MODEL=o1  # Better quality
ENABLE_PHASE1_OPTIMIZATIONS=true
MAX_DEBATE_ROUNDS=3

# Load specific profile
cp .env.production .env
```

## Configuration Reference

For a complete list of all configuration options with descriptions and defaults, see:
- `.env.example` - Complete template with all options
- `src/agent/config.py` - Source code with type definitions

## Migration from Legacy Configuration

If migrating from the old configuration system:

1. The new system is 100% backwards compatible
2. `DEFAULT_CONFIG` still works as before
3. Old environment variable names are preserved
4. No code changes required for existing code

The main improvements are:
- Type safety with Pydantic
- Async-safe loading
- Better validation
- Centralized management