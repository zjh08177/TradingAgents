# Configuration Key Mapping Fix

## Problem Summary
When setting `DEEP_THINK_MODEL=o3-mini` in environment variables or .env file, langgraph dev was still using the default `o3` model instead of the configured value.

## Root Cause Analysis

### Configuration Key Mismatch
There was a mismatch between the configuration keys provided by `config.py` and what the application code expected:

#### Configuration System (config.py):
```python
# Environment Variable → Pydantic Field → Dictionary Key
DEEP_THINK_MODEL → deep_think_model → deep_think_llm
QUICK_THINK_MODEL → quick_think_model → quick_think_llm
```

#### Application Code (trading_graph.py):
```python
# Expected keys that didn't exist:
self.config.get("reasoning_model", "o3")  # Looking for 'reasoning_model'
self.config.get("quick_thinking_model", "gpt-4o")  # Looking for 'quick_thinking_model'
```

### Why It Failed
1. User sets `DEEP_THINK_MODEL=o3-mini` in .env
2. Config correctly reads it into `deep_think_model` field
3. Config maps it to `deep_think_llm` in dictionary
4. BUT trading_graph.py looks for `reasoning_model` (doesn't exist)
5. Falls back to hardcoded default: `"o3"`

## The Fix

Updated `config.py` to provide BOTH sets of keys for full compatibility:

```python
# In config.py to_dict() method:
"deep_think_llm": self.deep_think_model,  # Legacy key for backward compatibility
"quick_think_llm": self.quick_think_model,  # Legacy key for backward compatibility
"reasoning_model": self.deep_think_model,  # Key expected by trading_graph.py
"quick_thinking_model": self.quick_think_model,  # Key expected by trading_graph.py
```

## How It Works Now

### Configuration Flow
```
DEEP_THINK_MODEL=o3-mini (env var)
    ↓
deep_think_model field (Pydantic)
    ↓
Dictionary provides:
  - deep_think_llm: "o3-mini" (legacy)
  - reasoning_model: "o3-mini" (expected by app)
    ↓
trading_graph.py gets correct model!
```

## Testing the Fix

### 1. Via Environment Variable
```bash
export DEEP_THINK_MODEL=o3-mini
export QUICK_THINK_MODEL=gpt-4o-mini
python3 debug_local.sh AAPL
```

### 2. Via .env File
```bash
# In .env file:
DEEP_THINK_MODEL=o3-mini
QUICK_THINK_MODEL=gpt-4o-mini

# Run application
python3 debug_local.sh AAPL
```

### 3. Verification
The configuration will now correctly use:
- `o3-mini` for deep thinking (debates, decisions)
- `gpt-4o-mini` for quick thinking (analysts, tools)

## Impact

### Before Fix
- Environment variables for LLM models were ignored
- Always used hardcoded defaults (`o3`, `gpt-4o`)
- Configuration changes had no effect

### After Fix
- Environment variables work correctly
- .env file settings are properly applied
- Both legacy and new code paths work
- Full backward compatibility maintained

## Files Modified
- `src/agent/config.py` - Added dual key mapping in `to_dict()` method

## Related Configuration Keys

### Working Mappings
These environment variables were already working correctly:
- `MAX_DEBATE_ROUNDS` → `max_debate_rounds`
- `ENABLE_PARALLEL_EXECUTION` → `enable_parallel_execution`
- All other settings with explicit `env=` parameters

### Fixed Mappings
These now work correctly:
- `DEEP_THINK_MODEL` → `reasoning_model` (for app code)
- `QUICK_THINK_MODEL` → `quick_thinking_model` (for app code)
- `LLM_PROVIDER` → `llm_provider`
- `BACKEND_URL` → `backend_url`

## Recommendations

1. **Always use environment variables** for model configuration:
   ```bash
   DEEP_THINK_MODEL=o3-mini  # or o1, o3, gpt-4o, etc.
   QUICK_THINK_MODEL=gpt-4o-mini  # or gpt-4o, gpt-3.5-turbo, etc.
   ```

2. **Check active configuration** by looking at startup logs

3. **For cost optimization**:
   - Development: `DEEP_THINK_MODEL=gpt-4o` (cheaper)
   - Production: `DEEP_THINK_MODEL=o1` or `o3` (better quality)

4. **Verify configuration** is being read:
   ```python
   from src.agent.config import DEFAULT_CONFIG
   print(DEFAULT_CONFIG['reasoning_model'])  # Should show your configured value
   ```