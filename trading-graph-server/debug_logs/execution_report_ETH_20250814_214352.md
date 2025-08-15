# 📊 Trading Graph Execution Report

**Ticker:** ETH  
**Generated:** Thu Aug 14 21:45:16 PDT 2025  
**Session ID:** 20250814_214352  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** ETH
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 85s

## 🔧 Configuration

- **Python Version:** Python 3.11.12
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_ETH_20250814_214352.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_ETH_20250814_214352.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_ETH_20250814_214352.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_ETH_20250814_214352.md

## 📊 Key Results

- **Decision:** BUY
- **Runtime:** 72.160299s
- **Trade Date:** 2025-08-14
- **Estimated Token Usage:** 3,304 tokens

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_ETH_20250814_214352.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_ETH_20250814_214352.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

