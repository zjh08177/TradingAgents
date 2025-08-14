# 📊 Trading Graph Execution Report

**Ticker:** OPEN  
**Generated:** Mon Aug 11 18:16:09 PDT 2025  
**Session ID:** 20250811_181133  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** OPEN
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 276s

## 🔧 Configuration

- **Python Version:** Python 3.13.5
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_OPEN_20250811_181133.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_OPEN_20250811_181133.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_OPEN_20250811_181133.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_OPEN_20250811_181133.md

## 📊 Key Results

- **Decision:** HOLD
- **Runtime:** 275.214686s
- **Trade Date:** 2025-08-11

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_OPEN_20250811_181133.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_OPEN_20250811_181133.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

