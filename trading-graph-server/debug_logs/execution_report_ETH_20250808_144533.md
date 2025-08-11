# 📊 Trading Graph Execution Report

**Ticker:** ETH  
**Generated:** Fri Aug  8 14:50:34 PDT 2025  
**Session ID:** 20250808_144533  
**Working Directory:** /Users/bytedance/Documents/TradingAgents/trading-graph-server

## 📋 Execution Summary

- **Target Ticker:** ETH
- **Execution Status:** ✅ SUCCESS
- **Total Runtime:** 301s

## 🔧 Configuration

- **Python Version:** Python 3.13.5
- **LangChain Tracing:** Enabled
- **Debug Logging:** Enabled

## 📂 Generated Files

- **Debug Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/debug_session_ETH_20250808_144533.log
- **Graph Log:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_ETH_20250808_144533.log  
- **Results JSON:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_ETH_20250808_144533.json
- **This Report:** /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/execution_report_ETH_20250808_144533.md

## 📊 Key Results

- **Decision:** BUY
- **Runtime:** 297.545832s
- **Trade Date:** 2025-08-08

## 🔍 Next Steps

1. **View detailed results:**
   ```bash
   cat /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/results_ETH_20250808_144533.json | jq .
   ```

2. **Monitor logs:**
   ```bash
   tail -f /Users/bytedance/Documents/TradingAgents/trading-graph-server/debug_logs/graph_execution_ETH_20250808_144533.log
   ```

3. **Run for different ticker:**
   ```bash
   ./debug_local.sh AAPL
   ```

4. **View in LangSmith (if tracing enabled):**
   Check https://smith.langchain.com for trace details

