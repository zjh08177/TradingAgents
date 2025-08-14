# 📊 Trading Graph Execution Report

**Ticker:** TSLA  
**Generated:** Thu Aug 14 12:55:32 PDT 2025  
**Session ID:** 20250814_125347  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** TSLA
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 105s

## 🔧 Configuration

- **Python Version:** Python 3.11.12
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_TSLA_20250814_125347.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_TSLA_20250814_125347.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_TSLA_20250814_125347.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_TSLA_20250814_125347.md

## 📊 Key Results

- **Decision:** BUY
- **Runtime:** 103.952291s
- **Trade Date:** 2025-08-14
- **Estimated Token Usage:** 4,217 tokens

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_TSLA_20250814_125347.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_TSLA_20250814_125347.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

