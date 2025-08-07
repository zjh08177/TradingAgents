# 📊 Trading Graph Execution Report

**Ticker:** AAPL  
**Generated:** Thu Aug  7 11:12:55 PDT 2025  
**Session ID:** 20250807_110920  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** AAPL
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 215s

## 🔧 Configuration

- **Python Version:** Python 3.13.5
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_AAPL_20250807_110920.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_AAPL_20250807_110920.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_AAPL_20250807_110920.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_AAPL_20250807_110920.md

## 📊 Key Results

- **Decision:** HOLD
- **Runtime:** 209.810953s
- **Trade Date:** 2025-08-07

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_AAPL_20250807_110920.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_AAPL_20250807_110920.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

