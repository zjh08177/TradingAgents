# 📊 Trading Graph Execution Report

**Ticker:** UNH  
**Generated:** Wed Aug 13 19:11:53 PDT 2025  
**Session ID:** 20250813_191005  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** UNH
- **Execution Status:** ❌ FAILED
- **Total Runtime:** 108s

## 🔧 Configuration

- **Python Version:** Python 3.11.12
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_UNH_20250813_191005.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250813_191005.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250813_191005.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_UNH_20250813_191005.md

## 📊 Key Results

- No results available

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_UNH_20250813_191005.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_UNH_20250813_191005.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

