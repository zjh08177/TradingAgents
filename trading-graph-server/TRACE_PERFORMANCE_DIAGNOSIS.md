# Trace Performance Diagnosis & Solutions

## 🚨 Performance Issue
Execution times are 2-5x slower than the 120s target. The system has parallel infrastructure but LangGraph is executing nodes sequentially.

**Current vs Target Performance:**
| Current | Target | Gap |
|---------|--------|-----|
| 248-590s | 120s | 2-5x slower |

## 🎯 Action Items

### 🔴 Priority 1: Enable True Parallel Execution (Day 1)

**Task: Implement Send-based Parallel Dispatcher**
```python
# In dispatcher.py - Replace current dispatcher with:
from langgraph.prebuilt import Send

def create_parallel_dispatcher(selected_analysts):
    @debug_node("Parallel_Dispatcher")
    async def parallel_dispatcher_node(state):
        # Force parallel execution with Send
        sends = []
        for analyst_type in selected_analysts:
            sends.append(Send(f"{analyst_type}_analyst", state))
        return sends
    
    return parallel_dispatcher_node
```

**Task: Add Execution Timing Logs**
```python
# In each analyst node - Add timing:
logger.info(f"⏱️ {analyst_type} START: {time.time()}")
# ... analyst execution ...
logger.info(f"⏱️ {analyst_type} END: {time.time()} (duration: {duration}s)")
```

### 🟡 Priority 2: Optimize Tool Execution (Day 2-3)

**Task: Batch Tool Calls in Analysts**
```python
# In each analyst (e.g., market_analyst.py):
async def execute_tools_parallel(tools_to_call):
    """Execute multiple tool calls in parallel"""
    tasks = []
    for tool_call in tools_to_call:
        tasks.append(tool.ainvoke(tool_call.args))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Task: Create Async Market Data Fetcher**
```python
# In toolkit.py - Add parallel data fetching:
class AsyncToolkit:
    async def get_all_market_data(self, symbol, date):
        """Get all market data in parallel"""
        tasks = [
            self.get_YFin_data_async(symbol, date),
            self.get_stockstats_indicators_async(symbol, "close_50_sma", date),
            self.get_stockstats_indicators_async(symbol, "close_200_sma", date),
            self.get_stockstats_indicators_async(symbol, "macd", date),
            self.get_stockstats_indicators_async(symbol, "rsi", date),
        ]
        
        results = await asyncio.gather(*tasks)
        return self._combine_market_data(results)
```

### 🟢 Priority 3: Add Caching & Connection Pooling (Day 4-5)

**Task: Implement Tool Result Caching**
```python
# In toolkit.py:
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_market_data(symbol, date, indicator):
    # Cache frequently accessed data
    return self._fetch_market_data(symbol, date, indicator)
```

**Task: Add Connection Pooling**
```python
# In toolkit.py:
import aiohttp

class ToolkitWithPool:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
```

## 📊 Success Metrics

### Verification Checklist
- [ ] All analysts start within 1-2s of dispatcher
- [ ] Tool calls within analysts execute concurrently
- [ ] Total runtime < 120s for standard analysis
- [ ] LangSmith traces show overlapping execution spans

### Expected Performance Gains
| Implementation | Expected Runtime | Improvement |
|----------------|------------------|-------------|
| Current | 248-590s | Baseline |
| + Send Parallelism | 80-120s | 2-3x faster |
| + Async Tools | 60-90s | 3-4x faster |
| + Caching | 45-75s | 4-6x faster |

## 🔍 Monitoring Commands

```bash
# Watch for parallel execution patterns
grep "⏱️" logs/trading_graph.log | tail -20

# Check analyst start times
grep "START" logs/trading_graph.log | awk '{print $1, $2, $3, $NF}'

# Monitor total runtime
grep "Total execution time" logs/trading_graph.log
```