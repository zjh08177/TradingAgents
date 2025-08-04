# 📊 Trading Graph Execution Report

**Ticker:** NVDA  
**Generated:** Sun Aug  3 10:10:53 PDT 2025  
**Session ID:** 20250803_100814  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** NVDA
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 159s

## 🔧 Configuration

- **Python Version:** Python 3.13.5
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_NVDA_20250803_100814.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_NVDA_20250803_100814.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250803_100814.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_NVDA_20250803_100814.md

## 📊 Key Results

- **Decision:** HOLD
- **Runtime:** 157.270408s
- **Trade Date:** 2025-08-03

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_NVDA_20250803_100814.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_NVDA_20250803_100814.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

