# 📊 Trading Graph Execution Report

**Ticker:** GME  
**Generated:** Sun Aug  3 01:18:40 PDT 2025  
**Session ID:** 20250803_011642  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** GME
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 118s

## 🔧 Configuration

- **Python Version:** Python 3.13.5
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_GME_20250803_011642.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_GME_20250803_011642.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_GME_20250803_011642.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_GME_20250803_011642.md

## 📊 Key Results

- **Decision:** SELL
- **Runtime:** 113.919955s
- **Trade Date:** 2025-08-03

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_GME_20250803_011642.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_GME_20250803_011642.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

