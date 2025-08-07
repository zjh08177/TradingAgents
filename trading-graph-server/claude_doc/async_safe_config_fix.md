# Async-Safe Configuration Fix

## Problem
The unified configuration system caused a `BlockingError` when LangGraph ASGI server tried to import the module:
```
blockbuster.blockbuster.BlockingError: Blocking call to io.TextIOWrapper.read
```

This occurred because `load_dotenv()` was called at module import time (line 16 of `src/agent/config.py`), performing synchronous file I/O that blocks the async event loop.

## Root Cause
- **Insufficient Testing**: Only tested in synchronous scripts, not in the actual async ASGI environment
- **Module-level I/O**: Called `load_dotenv()` during module import
- **Async Incompatibility**: ASGI servers require all I/O to be async or run in separate threads

## Solution
Removed the blocking `load_dotenv()` call and leveraged pydantic-settings' built-in `.env` file loading:

```python
# BEFORE (blocking):
from dotenv import load_dotenv
load_dotenv()  # ❌ Blocks at import time

class TradingConfig(BaseSettings):
    ...

# AFTER (async-safe):
class TradingConfig(BaseSettings):
    ...
    model_config = {
        "env_file": ".env",  # ✅ Pydantic loads .env lazily
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
```

## Verification
1. **Async-Safe Import**: No blocking I/O at module level
2. **Environment Loading**: `.env` values still load correctly through pydantic
3. **LangGraph Compatibility**: Server starts without blocking errors
4. **Backwards Compatibility**: All existing code continues to work

## Testing Approach
```bash
# Test async-safe configuration
python3 test_async_safe_config.py

# Test with actual LangGraph server
./debug_local.sh AAPL
```

## Key Learnings
1. **Always test in target environment**: LangGraph/ASGI for async applications
2. **Avoid module-level I/O**: Never perform file operations at import time
3. **Use framework features**: Pydantic-settings handles .env loading internally
4. **Consider async constraints**: Design with async compatibility from the start

## Result
✅ Configuration system now works in both sync and async contexts
✅ No blocking I/O errors in LangGraph ASGI server
✅ All .env values load correctly
✅ Maintains 100% backwards compatibility