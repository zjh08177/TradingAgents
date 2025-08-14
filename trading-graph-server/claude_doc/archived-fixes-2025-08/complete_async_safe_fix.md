# Complete Async-Safe Configuration Fix

## The Problem Evolution
1. **First attempt**: Removed `load_dotenv()` from line 16 ❌ Still failed
2. **Real issue**: `DEFAULT_CONFIG = get_config()` at line 224 was STILL causing blocking I/O

## Why First Fix Failed
Even after removing `load_dotenv()` and using pydantic's built-in `.env` loading:
- Line 224: `DEFAULT_CONFIG = get_config()` was still at module level
- This triggered `TradingConfig()` instantiation at import time
- Pydantic reads the `.env` file = blocking I/O in async context

## The Complete Solution

### 1. Created Lazy Wrapper Class
```python
class _LazyDefaultConfig:
    """Lazy wrapper for DEFAULT_CONFIG to prevent blocking I/O at import"""
    def __getattr__(self, name):
        return getattr(get_config(), name)
    
    def __getitem__(self, key):
        return get_config()[key]
    
    def get(self, key, default=None):
        return get_config().get(key, default)
    # ... other dict-like methods

# Export lazy wrapper instead of actual config
DEFAULT_CONFIG = _LazyDefaultConfig()
```

### 2. Fixed Both Files
- **config.py**: Replaced `DEFAULT_CONFIG = get_config()` with lazy wrapper
- **default_config.py**: Removed `DEFAULT_CONFIG = get_config()`, imported lazy wrapper

### 3. Key Pattern: Lazy Loading
- **Import time**: No I/O operations, just class definitions
- **First access**: Config loads `.env` file in appropriate context
- **Backwards compatible**: Wrapper implements dict interface

## Verification
```bash
# Test lazy loading
python3 test_no_blocking_import.py

# Test with LangGraph
./debug_local.sh AAPL
```

## Critical Lessons

### ❌ WRONG Pattern
```python
# Module level - executes at import!
DEFAULT_CONFIG = get_config()  # Reads .env file immediately
```

### ✅ CORRECT Pattern  
```python
# Lazy wrapper - defers I/O until access
class _LazyDefaultConfig:
    def __getitem__(self, key):
        return get_config()[key]  # Only loads on first access

DEFAULT_CONFIG = _LazyDefaultConfig()  # Just a wrapper, no I/O
```

## Key Takeaways
1. **Module-level code = import time = blocks async**
2. **Even pydantic's .env loading blocks if triggered at import**
3. **Use lazy loading patterns for all I/O in async codebases**
4. **Test in actual async environment (ASGI/LangGraph), not just sync scripts**
5. **Wrapper classes provide backwards compatibility while enabling lazy loading**

## Result
✅ No blocking I/O at import time
✅ Config loads lazily on first access
✅ Full backwards compatibility
✅ Works with LangGraph ASGI server
✅ All .env values load correctly