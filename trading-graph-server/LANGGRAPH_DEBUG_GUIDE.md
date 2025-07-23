# 🐛 **LangGraph Local Debug Guide**

## 📋 **Overview**

This guide provides comprehensive instructions for debugging LangGraph projects locally in the terminal. Based on successful debugging of the TradingAgents graph, these techniques can help identify and resolve common async, state management, and execution issues.

## 🛠️ **Prerequisites**

### Required Tools
- **Python 3.8+** with virtual environment
- **LangGraph CLI**: `pip install langgraph-cli`
- **Environment Variables**: API keys configured in `.env`
- **Terminal Access**: Command-line interface

### Required API Keys
```bash
# In your .env file
OPENAI_API_KEY=sk-your-key-here
FINNHUB_API_KEY=your-finnhub-key    # Optional
SERPER_API_KEY=your-serper-key      # Optional
```

---

## ⚡ **Quick Start: One-Command Debug**

For the fastest debugging experience, use our comprehensive debug script:

```bash
cd trading-graph-server
./debug_local.sh
```

This script will:
- ✅ Verify your environment
- ✅ Test all imports and dependencies
- ✅ Run comprehensive debug tests
- ✅ Analyze graph structure
- ✅ Generate detailed debug report
- ✅ Set up logging for issue identification

---

## 🔧 **Manual Debug Process**

### **Step 1: Enable Debug Environment**

```bash
cd trading-graph-server

# Essential debug settings
export PYTHONPATH=/Users/bytedance/Documents/TradingAgents/trading-graph-server/src:$PYTHONPATH
export LANGCHAIN_TRACING_V2=false
export LANGGRAPH_DEBUG=true
export PYTHON_LOG_LEVEL=DEBUG

# Load your environment
source venv/bin/activate
source .env
```

### **Verify Environment Setup**
```bash
# Check Python path
echo $PYTHONPATH

# Verify API keys (without exposing them)
python -c "import os; print('✅ OpenAI key:', 'sk-' in str(os.getenv('OPENAI_API_KEY', '')))"
```

---

## 🔍 **Advanced Logging System**

### **Node-Level Debug Logging**

All graph nodes now include comprehensive debug logging that captures:

#### **📋 What Gets Logged:**
- **Node Start/End**: Exact timing and execution flow
- **Input State**: Complete state summary with safe size limits
- **Output Results**: Detailed output analysis
- **Execution Time**: Performance monitoring
- **Error Details**: Full tracebacks with state at error
- **LLM Interactions**: Prompt/response lengths and timing
- **Data Fetches**: API calls, query details, and results
- **Memory Operations**: Query patterns and result counts

#### **🎯 Debug Decorator Usage:**

```python
from agent.utils.debug_logging import debug_node, log_llm_interaction, log_data_fetch

@debug_node("My_Node_Name")
async def my_node(state):
    # Your node logic here
    return result
```

#### **📊 Log Output Example:**
```
================================================================================
🚀 NODE START: Trader
📋 Node ID: Trader_1704127234567
⏰ Start Time: 2024-01-01T15:20:34.567890
================================================================================
📥 INPUT STATE SUMMARY:
   📊 Total Keys: 8
   🔑 Available Keys: ['company_of_interest', 'market_report', 'sentiment_report', ...]
   📝 company_of_interest: String(4 chars): TSLA
   📝 market_report: String(1247 chars): Technical analysis shows...
   📝 sentiment_report: String(856 chars): Social sentiment is...

⚡ EXECUTING: Trader

🧠 MEMORY GET: Technical analysis shows TSLA has strong...
📊 Results Count: 2

🤖 LLM CALL: trader_llm
📝 Prompt Length: 1456 chars
📤 Response Length: 234 chars
⏱️  LLM Time: 2.345 seconds

✅ NODE SUCCESS: Trader
⏱️  Execution Time: 3.678 seconds
📤 OUTPUT SUMMARY:
   📊 Output Keys: 3
   🔑 Result Keys: ['messages', 'trader_investment_plan', 'sender']
   📝 trader_investment_plan: String(234 chars): Based on comprehensive analysis...

================================================================================
🏁 NODE COMPLETE: Trader
================================================================================
```

#### **💥 Error Logging Example:**
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
💥 NODE ERROR: Market_Analyst
📋 Node ID: Market_Analyst_1704127234567
⏱️  Failed After: 1.234 seconds
❌ Error Type: KeyError
💬 Error Message: 'sentiment_report'
📍 Error Location: market_analyst in agent.analysts.market_analyst
🔍 Full Traceback:
   Traceback (most recent call last):
     File "agent/analysts/market_analyst.py", line 45, in market_analyst
       sentiment = state["sentiment_report"]
   KeyError: 'sentiment_report'

🗂️  STATE AT ERROR:
   📝 company_of_interest: String(4 chars): TSLA
   📝 trade_date: String(10 chars): 2024-01-15
   📝 market_report: String(1247 chars): Technical analysis...
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

---

## 🧪 **Debug Test Framework**

### **Comprehensive Debug Test**

Run the enhanced debug test:

```bash
python debug_test.py
```

This test covers:
1. **Environment Verification** - API keys, paths
2. **Import Testing** - All modules and dependencies  
3. **LLM Connectivity** - Basic LLM functionality
4. **Memory System** - Memory initialization
5. **Graph Compilation** - Node/edge verification
6. **Debug Logging** - Decorator functionality
7. **Quick Execution** - End-to-end graph test

### **Expected Success Output:**
```
🚀 Starting enhanced debug test of trading graph
🔑 Testing environment...
✅ OpenAI API key found
📦 Testing imports...
✅ All imports successful
🤖 Testing LLM creation...
✅ LLM test result: LLM working
💾 Testing memory system...
✅ Memory system created successfully
🏗️ Testing graph compilation...
✅ Graph compiled with 21 nodes
🔍 Testing debug logging...
✅ Debug logging test: {'test': 'success', 'debug_working': True}
⚡ Testing quick graph execution...
✅ Quick graph execution completed in 45.32 seconds
📊 Final decision: HOLD

🎉 ENHANCED DEBUG TEST PASSED - Graph is working correctly!
```

---

## 🚀 **Server Debug Mode**

### **Start Server with Full Logging**
```bash
# Option 1: Production-ready (no --allow-blocking)
langgraph dev --port 8123 --no-browser

# Option 2: Development mode (if needed)
langgraph dev --port 8123 --allow-blocking --no-browser
```

### **Monitor Debug Logs in Real-Time**
```bash
# Watch graph debug logs
tail -f graph_debug.log

# Watch all debug output
tail -f debug_logs/debug_session_*.log
```

### **Test Server Endpoints**
```bash
# Health check
curl -s http://127.0.0.1:8123/assistants && echo "✅ Server responding"

# Create assistant
curl -X POST http://127.0.0.1:8123/assistants \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "trading_agents"}'

# Create thread for testing
curl -X POST http://127.0.0.1:8123/threads \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 🐛 **Issue Identification & Solutions**

### **🔍 How to Identify Issues with Debug Logs**

#### **1. Node Execution Issues**
**Look for:** Missing `🏁 NODE COMPLETE` messages
**Indicates:** Node crashed or hung
**Debug:** Check the last `⚡ EXECUTING` message and error logs

#### **2. State Access Problems**  
**Look for:** `KeyError` in state access
**Indicates:** Missing state keys or improper initialization
**Debug:** Check `📥 INPUT STATE SUMMARY` for available keys

#### **3. LLM Issues**
**Look for:** Long `⏱️ LLM Time` or LLM errors
**Indicates:** API issues, prompt problems, or network delays
**Debug:** Check `🤖 LLM CALL` logs for prompt/response details

#### **4. Data Fetch Problems**
**Look for:** `📡 DATA FETCH` errors or zero results
**Indicates:** API key issues, network problems, or rate limiting
**Debug:** Check data source logs and API responses

#### **5. Memory System Issues**
**Look for:** `🧠 MEMORY` operation failures
**Indicates:** Memory initialization or query problems  
**Debug:** Check memory logs and query patterns

### **Common Issues & Solutions**

#### **Issue 1: `CancelledError()` in Async Context**
**Symptoms in Logs:**
```
💥 NODE ERROR: Research_Manager
❌ Error Type: CancelledError
💬 Error Message: 
```

**Solution:**
```python
# ❌ Wrong - Sync operations
import time
import requests
result = llm.invoke(messages)
time.sleep(1)

# ✅ Correct - Async operations  
import asyncio
import httpx
result = await llm.ainvoke(messages)
await asyncio.sleep(1)
```

#### **Issue 2: `KeyError` in State Access**
**Symptoms in Logs:**
```
💥 NODE ERROR: Trader
❌ Error Type: KeyError
💬 Error Message: 'sentiment_report'
🗂️  STATE AT ERROR:
   📝 company_of_interest: String(4 chars): TSLA
   📝 market_report: String(1247 chars): Technical analysis...
   # No sentiment_report key!
```

**Solution:**
```python
# ❌ Wrong - Direct access
sentiment_report = state["sentiment_report"]

# ✅ Correct - Safe access with defaults
sentiment_report = state.get("sentiment_report", "")
```

#### **Issue 3: LLM Message Format Errors**
**Symptoms in Logs:**
```
💥 NODE ERROR: News_Analyst
❌ Error Type: AttributeError
💬 Error Message: 'coroutine' object has no attribute 'get'
```

**Solution:**
```python
# ❌ Wrong - Raw string to LLM
result = await llm.ainvoke(prompt_string)

# ✅ Correct - Proper message format
messages = [{"role": "user", "content": prompt_string}]
result = await llm.ainvoke(messages)
```

---

## 📊 **Debug Report Analysis**

### **Generated Debug Files**

After running `./debug_local.sh`, you'll get:

```
debug_logs/
├── debug_session_20240115_142030.log    # Full debug session
├── graph_debug_20240115_142030.log      # Graph execution logs  
└── debug_report_20240115_142030.md      # Comprehensive report
```

### **Reading the Debug Report**

The generated report includes:
- **Environment Status** - Python, paths, keys
- **Test Results** - All debug test outcomes
- **Next Steps** - Specific commands to run
- **Debug Commands** - Useful debugging commands

### **Key Sections to Check:**

1. **Environment Status** - Ensure all prerequisites met
2. **Test Results** - Identify which tests failed
3. **Graph Analysis** - Verify node count and structure
4. **Debug Commands** - Use for ongoing debugging

---

## 🎯 **Advanced Debugging Techniques**

### **Real-Time Log Monitoring**

```bash
# Monitor all debug activity
tail -f debug_logs/debug_session_*.log

# Monitor specific node execution
grep "NODE START\|NODE ERROR" debug_logs/graph_debug_*.log

# Monitor LLM interactions
grep "LLM CALL" debug_logs/graph_debug_*.log

# Monitor data fetches
grep "DATA FETCH" debug_logs/graph_debug_*.log
```

### **Performance Analysis**

```bash
# Find slowest nodes
grep "Execution Time" debug_logs/graph_debug_*.log | sort -k5 -nr

# Find LLM performance issues
grep "LLM Time" debug_logs/graph_debug_*.log | sort -k5 -nr

# Find data fetch delays
grep "Fetch Time" debug_logs/graph_debug_*.log | sort -k6 -nr
```

### **Error Pattern Analysis**

```bash
# Find all errors
grep "NODE ERROR" debug_logs/graph_debug_*.log

# Find specific error types
grep "KeyError\|CancelledError\|AttributeError" debug_logs/debug_session_*.log

# Find state-related issues
grep "STATE AT ERROR" -A 10 debug_logs/graph_debug_*.log
```

---

## ✅ **Verification Checklist**

### **🔧 Environment Setup**
- [ ] Virtual environment activated
- [ ] API keys configured in `.env`
- [ ] PYTHONPATH set correctly
- [ ] Debug environment variables set
- [ ] All dependencies installed

### **📝 Code Quality**
- [ ] All nodes have `@debug_node()` decorators
- [ ] All functions are `async def` where needed
- [ ] All LLM calls use `await llm.ainvoke()`
- [ ] All HTTP calls use `httpx` instead of `requests`
- [ ] All `time.sleep()` replaced with `await asyncio.sleep()`
- [ ] All state access uses `.get()` with defaults

### **🧪 Execution Tests**
- [ ] `./debug_local.sh` passes all phases
- [ ] Graph compiles without errors
- [ ] Server starts without `--allow-blocking`
- [ ] Full execution completes successfully
- [ ] No `CancelledError` or `KeyError` exceptions
- [ ] Debug logs show complete node execution

### **📊 Integration Tests**
- [ ] LangGraph Studio shows all nodes
- [ ] API endpoints respond correctly
- [ ] State flows properly between nodes
- [ ] Final decision is generated
- [ ] All logging captures expected detail

---

## 🚀 **Production Deployment**

Once debugging is complete:

```bash
# Start production server (no --allow-blocking needed)
langgraph dev --port 8123

# Verify production readiness
curl -X POST http://127.0.0.1:8123/assistants \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "trading_agents"}'
```

---

## 📚 **Debug Resources**

### **🛠️ Debug Tools**
- **LangGraph Studio**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123`
- **Debug Script**: `./debug_local.sh`
- **Debug Logs**: `tail -f debug_logs/graph_debug_*.log`
- **Server Docs**: `http://127.0.0.1:8123/docs`

### **🔧 Common Commands**
```bash
# Run comprehensive debug
./debug_local.sh

# Kill all LangGraph processes
pkill -f "langgraph dev"

# Check what's running on port 8123
lsof -i :8123

# Monitor server health
watch -n 5 'curl -s http://127.0.0.1:8123/assistants | head -1'

# Analyze debug logs
grep -E "NODE (START|ERROR|COMPLETE)" debug_logs/graph_debug_*.log

# Check for async issues
grep -E "CancelledError|coroutine.*attribute" debug_logs/debug_session_*.log
```

---

## 🎉 **Success Indicators**

Your LangGraph debug session is successful when:

1. **✅ Debug script passes** - All 7 phases complete
2. **✅ Server starts without flags** - No `--allow-blocking` needed
3. **✅ Full graph execution** - Complete trading analysis
4. **✅ All nodes visible** - 21+ nodes in LangGraph Studio
5. **✅ No blocking operations** - Pure async execution
6. **✅ Comprehensive logging** - Detailed node execution logs
7. **✅ Error-free execution** - No `CancelledError` or `KeyError`

---

## 🔧 **Troubleshooting FAQ**

### **Q: Debug script fails in Phase 1**
**A:** Check Python installation and virtual environment setup
```bash
python3 --version
which python3
```

### **Q: Import errors in Phase 2**  
**A:** Verify PYTHONPATH and dependencies
```bash
echo $PYTHONPATH
pip list | grep langchain
```

### **Q: LLM test fails in Phase 3**
**A:** Check API key configuration
```bash
echo $OPENAI_API_KEY | head -c 10  # Should show "sk-proj-" or "sk-"
```

### **Q: Server won't start in Phase 4**
**A:** Check port availability and LangGraph CLI
```bash
lsof -i :8123
langgraph --version
```

### **Q: Graph execution incomplete**
**A:** Check debug logs for specific node failures
```bash
grep "NODE ERROR" debug_logs/graph_debug_*.log
```

---

**🎯 Remember**: The key to successful LangGraph debugging is systematic testing, comprehensive logging, and ensuring full async compatibility throughout your graph. Use the debug script for quick verification and the detailed logs for deep issue analysis! 