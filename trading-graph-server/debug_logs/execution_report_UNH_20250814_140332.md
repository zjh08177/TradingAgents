# 📊 Trading Graph Execution Report

**Ticker:** UNH  
**Generated:** Thu Aug 14 14:05:04 PDT 2025  
**Session ID:** 20250814_140332  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** UNH
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 92s

## 🔧 Configuration

- **Python Version:** Python 3.11.12
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_UNH_20250814_140332.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250814_140332.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250814_140332.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_UNH_20250814_140332.md

## 📊 Key Results

- **Decision:** BUY
- **Runtime:** 90.523985s
- **Trade Date:** 2025-08-14
- **Estimated Token Usage:** 4,068 tokens

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250814_140332.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250814_140332.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

