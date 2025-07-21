# LangGraph Integration Verification Checklist

## Overview
This checklist provides step-by-step verification items to ensure the LangGraph client integration is functioning correctly in the Flutter app. Each item must be checked and verified before considering the integration complete.

## Pre-Flight Checks

### 1. Environment Setup
- [ ] **Trading Graph Server is running**
  - Command: `cd backend && python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000`
  - Verify: Server starts without errors
  - Check: `curl http://localhost:8000/health` returns `{"status":"healthy"}`

- [ ] **Required API Keys are set in server environment**
  - OPENAI_API_KEY is configured
  - FINNHUB_API_KEY is configured (optional but recommended)
  - SERPAPI_API_KEY is configured (optional but recommended)

- [ ] **Flutter app dependencies are installed**
  - Run: `cd trading_dummy && flutter pub get`
  - Verify: No dependency errors

## App Launch Verification

### 2. Initial App State
- [ ] **App launches successfully**
  - No crash on startup
  - Main screen loads

- [ ] **LangGraph Status Card shows**
  - Green status card visible
  - Text: "Connected to LangGraph server at http://localhost:8000"
  - Check mark icon displayed

- [ ] **Server health check passes**
  - Log shows: "✅ LangGraph server is healthy and ready"
  - No connection errors in console

### 3. Automated Test Execution
- [ ] **2-second delay timer starts**
  - Log shows: "⏰ Scheduling automated test with TSLA in 2 seconds..."

- [ ] **Automated test triggers**
  - After 2 seconds, log shows: "🤖 AUTOMATED TEST: Starting analysis for TSLA"
  - Text field automatically populates with "TSLA"
  - Analysis starts automatically

- [ ] **Status message updates**
  - Shows: "Connecting to LangGraph server..."
  - Then: "Analyzing TSLA with LangGraph agents..."

## LangGraph Client Verification

### 4. Request Flow Logging
- [ ] **Request initialization logged**
  ```
  ==================== LANGGRAPH ANALYSIS START ====================
  Step 1: Preparing to analyze ticker: TSLA
  Target endpoint: http://localhost:8000/analyze
  Request ID: [timestamp]
  ```

- [ ] **Input validation logged**
  ```
  Step 2: Validating input
  Normalized ticker: TSLA
  ```

- [ ] **HTTP request preparation logged**
  ```
  Step 3: Preparing HTTP request
  Request URI: http://localhost:8000/analyze
  Request body: {"ticker":"TSLA"}
  ```

- [ ] **Request sending logged**
  ```
  Step 4: Sending POST request to LangGraph server
  ```

### 5. Server Communication
- [ ] **Response received**
  - Log shows: "Response received in [X]ms"
  - Log shows: "Response status code: 200"

- [ ] **Response parsing**
  - Log shows: "Step 5: Parsing server response"
  - Log shows: "Success! Parsing response body"
  - Response data keys listed

- [ ] **Report availability logged**
  ```
  - market_report: ✅ Present
  - sentiment_report: ✅ Present
  - news_report: ✅ Present
  - fundamentals_report: ✅ Present
  - investment_plan: ✅ Present
  - trader_investment_plan: ✅ Present
  - final_trade_decision: ✅ Present
  - processed_signal: ✅ Present
  ```

### 6. Result Processing
- [ ] **Result object creation**
  - Log shows: "Step 6: Creating TradingAnalysisResult object"

- [ ] **Result validation**
  - Log shows: "Step 7: Validating analysis result"
  - Log shows: "Result validation: ✅ All checks passed"

- [ ] **Analysis completion**
  ```
  ==================== LANGGRAPH ANALYSIS SUCCESS ====================
  Analysis completed successfully for TSLA
  Final signal: [BUY/SELL/HOLD]
  Total processing time: [X]s
  ```

## UI Verification

### 7. Result Display
- [ ] **Loading indicator disappears**
  - Progress spinner stops
  - Status message clears

- [ ] **Results card appears**
  - Green background color
  - Title: "LangGraph Analysis Results"
  - Cloud sync icon displayed

- [ ] **Result content shows**
  - Trading analysis results section
  - Ticker: TSLA
  - Date: [current date]
  - Signal: [BUY/SELL/HOLD]
  - Final decision text
  - Trading plan (if available)
  - Investment research (if available)

### 8. E2E Testing Information Card
- [ ] **Debug card visible**
  - Shows at bottom of screen
  - Gray background

- [ ] **Status indicators show**
  - LangGraph Client: Initialized ✅
  - Server URL: http://localhost:8000
  - Automated Test: Executed ✅
  - "Check logs for detailed trace" message

## Error Handling Verification

### 9. Network Error Handling
- [ ] **Server offline test**
  - Stop the server
  - Restart app
  - Error message: "LangGraph server is not responding..."
  - Orange warning card shown

- [ ] **Timeout handling**
  - Simulate slow network or long analysis
  - Appropriate timeout error message
  - App remains responsive

### 10. Invalid Input Handling
- [ ] **Empty ticker test**
  - Clear text field and tap GO
  - Error: "Please enter a ticker symbol"

- [ ] **Server error handling**
  - Test with invalid ticker
  - Error displayed in red error card
  - App doesn't crash

## Complete Integration Test

### 11. Manual Test After Automated Test
- [ ] **Manual analysis works**
  - Enter different ticker (e.g., "AAPL")
  - Tap GO button
  - Analysis completes successfully
  - New results displayed

- [ ] **Multiple analyses**
  - Run 3+ different tickers
  - Each completes successfully
  - Results update correctly each time

### 12. Log Verification Summary
- [ ] **No error logs during success path**
- [ ] **All step logs present (1-7)**
- [ ] **Timing information logged**
- [ ] **Request IDs tracked**

## Performance Metrics

### 13. Timing Verification
- [ ] **Health check < 1 second**
- [ ] **Analysis request 30-120 seconds**
  - Logged processing time reasonable
  - UI remains responsive during analysis

### 14. Memory and Resources
- [ ] **No memory leaks**
  - Run 5+ analyses
  - App performance doesn't degrade
- [ ] **Proper cleanup**
  - LangGraphClient disposal logged on app close

## Server-Side Verification

### 15. Server Logs
- [ ] **Request received on server**
  - Check backend logs for incoming request
  - Analysis stages logged

- [ ] **Results saved to disk**
  - Check `backend/results/TSLA/[date]/` directory
  - JSON results file exists
  - Individual report files created

## Final Verification

### 16. Complete E2E Flow
- [ ] **Automated test completes without intervention**
- [ ] **All logs show expected flow**
- [ ] **UI updates correctly at each stage**
- [ ] **Results are meaningful and complete**
- [ ] **No manual input required for test**

## Sign-Off

**Date:** _______________  
**Tester:** _______________  
**All items verified:** Yes [ ] No [ ]  
**Notes:** _________________________________

---

## Troubleshooting Guide

If any item fails, check:

1. **Server Issues**
   - Is the server running?
   - Are API keys configured?
   - Check server logs for errors

2. **Network Issues**
   - Can you reach http://localhost:8000/health from browser?
   - Firewall blocking connections?
   - Correct port (8000)?

3. **App Issues**
   - Flutter dependencies installed?
   - Console errors?
   - Debug logs enabled?

4. **Timing Issues**
   - Server taking too long?
   - Increase timeout in LangGraphClient
   - Check server performance