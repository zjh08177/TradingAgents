# Performance Optimization Implementation Plan

## Overview
This plan addresses the runtime increase from 106s to 215s while maintaining the successful token reduction from 48,783 to 41,097 tokens.

## Current Status
- ✅ Token optimization achieved: 15.8% reduction
- ❌ Runtime degraded: 102% increase (106s → 215s)
- 🎯 Goal: Reduce runtime to <140s while maintaining token benefits

## Root Cause Summary
1. Synchronous token operations blocking async execution
2. Multiple tokenizer initializations
3. Sequential prompt processing per agent
4. Extensive debug logging overhead

## Implementation Tasks

### Phase 1: Async Token Operations (Priority: HIGH)

#### Task 1.1: Create Async Token Counter
**Files to modify:**
- `src/agent/utils/token_optimizer.py`

**Implementation:**
```python
async def count_tokens_async(self, text: str) -> int:
    """Async token counting to prevent blocking"""
    tokenizer = await self._get_tokenizer()
    # Run CPU-intensive operation in thread pool
    return await asyncio.to_thread(tokenizer.encode, text)
```

**Verification:**
```bash
# Create test script
echo "Testing async token operations..."
./debug_local.sh --test-async-tokens
```

#### Task 1.2: Update Token Optimizer with Async Methods
**Files to modify:**
- `src/agent/utils/token_optimizer.py`
- `src/agent/utils/enhanced_token_optimizer.py`

**Changes:**
- Add async versions of all token operations
- Maintain backward compatibility with sync methods
- Use thread pool for CPU-intensive operations

**Verification:**
```bash
# Run performance comparison
./debug_local.sh --compare-token-performance
```

### Phase 2: Global Tokenizer Cache (Priority: HIGH)

#### Task 2.1: Implement Singleton Tokenizer
**Create new file:**
- `src/agent/utils/tokenizer_cache.py`

**Implementation:**
```python
import tiktoken
from typing import Dict, Optional
import threading

class TokenizerCache:
    _instance = None
    _lock = threading.Lock()
    _tokenizers: Dict[str, tiktoken.Encoding] = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_tokenizer(self, model_name: str) -> tiktoken.Encoding:
        if model_name not in self._tokenizers:
            with self._lock:
                if model_name not in self._tokenizers:
                    try:
                        self._tokenizers[model_name] = tiktoken.encoding_for_model(model_name)
                    except KeyError:
                        self._tokenizers[model_name] = tiktoken.get_encoding("cl100k_base")
        return self._tokenizers[model_name]
```

**Verification:**
```bash
# Test singleton behavior
python3 -c "from src.agent.utils.tokenizer_cache import TokenizerCache; \
    c1 = TokenizerCache(); c2 = TokenizerCache(); \
    print(f'Singleton works: {c1 is c2}')"

# Run full test
./debug_local.sh --test-tokenizer-cache
```

#### Task 2.2: Update All Token Operations to Use Cache
**Files to modify:**
- `src/agent/utils/token_optimizer.py`
- `src/agent/utils/enhanced_token_optimizer.py`
- `src/agent/utils/intelligent_token_limiter.py`
- `src/agent/utils/token_limiter.py`

**Verification:**
```bash
# Verify no duplicate tokenizer initializations
./debug_local.sh --trace-tokenizer-init
```

### Phase 3: Parallel Prompt Processing (Priority: MEDIUM)

#### Task 3.1: Create Batch Prompt Processor
**Create new file:**
- `src/agent/utils/batch_optimizer.py`

**Implementation:**
```python
import asyncio
from typing import List, Dict, Tuple

class BatchPromptOptimizer:
    def __init__(self, optimizer, compressor, enhancer):
        self.optimizer = optimizer
        self.compressor = compressor
        self.enhancer = enhancer
    
    async def process_prompts_parallel(
        self, 
        prompts: List[Tuple[str, str]]  # [(prompt, agent_type), ...]
    ) -> List[str]:
        """Process multiple prompts in parallel"""
        tasks = []
        for prompt, agent_type in prompts:
            task = self._process_single_prompt(prompt, agent_type)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def _process_single_prompt(self, prompt: str, agent_type: str) -> str:
        # Compress
        compressed = await self.compressor.compress_prompt_async(prompt)
        # Enhance
        enhanced = await self.enhancer.enhance_prompt_async(compressed, agent_type)
        return enhanced
```

**Verification:**
```bash
# Test parallel processing performance
./debug_local.sh --test-parallel-prompts
```

#### Task 3.2: Integrate Batch Processing in Graph Setup
**Files to modify:**
- `src/agent/graph/setup.py`
- `src/agent/graph/trading_graph.py`

**Implementation:**
- Collect all agent prompts at graph initialization
- Process them in batch before execution
- Cache processed prompts for reuse

**Verification:**
```bash
# Run full graph with batch processing
./debug_local.sh --enable-batch-processing
```

### Phase 4: Performance Monitoring (Priority: MEDIUM)

#### Task 4.1: Add Performance Decorators
**Create new file:**
- `src/agent/utils/performance_monitor.py`

**Implementation:**
```python
import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def performance_monitor(operation_name: str):
    """Decorator to monitor operation performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"⏱️ {operation_name}: {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ {operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"⏱️ {operation_name}: {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ {operation_name} failed after {duration:.3f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
```

**Verification:**
```bash
# Test performance monitoring
./debug_local.sh --trace-performance
```

#### Task 4.2: Add Monitoring to Critical Operations
**Files to modify:**
- All token optimization operations
- All prompt processing operations
- All LLM invocations

**Verification:**
```bash
# Generate performance report
./debug_local.sh --performance-report
```

### Phase 5: Quick Wins (Priority: HIGH)

#### Task 5.1: Reduce Debug Logging
**Files to modify:**
- `src/agent/utils/token_optimizer.py`
- `src/agent/utils/enhanced_token_optimizer.py`
- `src/agent/utils/intelligent_token_limiter.py`

**Changes:**
- Change logger.info to logger.debug for verbose messages
- Add log level configuration
- Remove redundant logging

**Verification:**
```bash
# Compare runtime with reduced logging
./debug_local.sh --log-level ERROR
```

#### Task 5.2: Implement Token Count Caching
**Files to modify:**
- `src/agent/utils/token_optimizer.py`

**Implementation:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def _cached_token_count(self, text_hash: int, model_name: str) -> int:
    """Cache token counts for repeated texts"""
    # Implementation
```

**Verification:**
```bash
# Test cache hit rate
./debug_local.sh --trace-cache-stats
```

### Phase 6: Verification Suite

#### Task 6.1: Create Comprehensive Test Script
**Create new file:**
- `scripts/test_performance_optimizations.py`

**Implementation:**
```python
#!/usr/bin/env python3
"""
Comprehensive performance optimization test suite
"""

import asyncio
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_async_token_operations():
    """Test async token counting performance"""
    # Implementation
    
async def test_tokenizer_cache():
    """Test global tokenizer cache"""
    # Implementation
    
async def test_parallel_processing():
    """Test parallel prompt processing"""
    # Implementation
    
async def run_all_tests():
    """Run all performance tests"""
    tests = [
        test_async_token_operations,
        test_tokenizer_cache,
        test_parallel_processing
    ]
    
    for test in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test.__name__}")
        print(f"{'='*50}")
        await test()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
```

**Verification:**
```bash
# Run all performance tests
python3 scripts/test_performance_optimizations.py
```

#### Task 6.2: Update debug_local.sh with Performance Tests
**File to modify:**
- `debug_local.sh`

**Add new test phases:**
```bash
# Phase 8: Performance Optimization Tests
echo -e "${BLUE}📋 Phase 8: Performance Optimization Tests${NC}"
echo "================================"

# Test 1: Async Token Operations
echo -e "${CYAN}🧪 Test 1: Async Token Operations${NC}"
python3 -c "
import asyncio
from agent.utils.token_optimizer import TokenOptimizer
# Test implementation
"

# Test 2: Tokenizer Cache
echo -e "${CYAN}🧪 Test 2: Global Tokenizer Cache${NC}"
# Test implementation

# Test 3: Parallel Processing
echo -e "${CYAN}🧪 Test 3: Parallel Prompt Processing${NC}"
# Test implementation
```

## Success Metrics

### Performance Targets
- Runtime: <140s (from current 215s)
- Token usage: Maintain <42,000 (current 41,097)
- Success rate: Maintain 100%
- Quality grade: Maintain A+

### Verification Checklist
- [ ] All async operations tested
- [ ] Tokenizer cache working (single instance)
- [ ] Parallel processing verified
- [ ] Performance monitoring active
- [ ] Debug logging reduced
- [ ] Full debug_local.sh passes
- [ ] LangSmith trace shows improvement

## Implementation Timeline

### Week 1
- Phase 1: Async Token Operations
- Phase 2: Global Tokenizer Cache
- Phase 5: Quick Wins

### Week 2
- Phase 3: Parallel Prompt Processing
- Phase 4: Performance Monitoring
- Phase 6: Verification Suite

## Risk Mitigation

### Potential Issues
1. **Async compatibility**: Some operations may not support async
   - Mitigation: Maintain sync fallbacks
   
2. **Memory usage**: Caching may increase memory
   - Mitigation: Implement cache size limits
   
3. **Complexity**: Parallel processing adds complexity
   - Mitigation: Comprehensive testing and monitoring

## Rollback Plan

If performance degrades:
1. Disable features via config flags
2. Revert to synchronous operations
3. Clear caches
4. Restore original implementation

## Conclusion

This plan addresses the root causes of the performance degradation while maintaining the successful token optimization. The phased approach allows for incremental improvements with verification at each step.