# 📊 Trading Graph Execution Report

**Ticker:** UNH  
**Generated:** Thu Aug 14 12:15:34 PDT 2025  
**Session ID:** 20250814_121408  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** UNH
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 86s

## 🔧 Configuration

- **Python Version:** Python 3.11.12
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_UNH_20250814_121408.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250814_121408.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250814_121408.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_UNH_20250814_121408.md

## 📊 Key Results

- **Decision:** BUY
- **Runtime:** 85.581717s
- **Trade Date:** 2025-08-14
- **Estimated Token Usage:** 3,033 tokens

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250814_121408.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250814_121408.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

