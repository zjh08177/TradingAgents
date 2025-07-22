# LangGraph Trading Server API Testing Documentation

## Overview
This document provides comprehensive technical instructions for testing the TradingAgents API endpoint of the trading-graph-server. The API provides AI-powered stock analysis using multiple trading agents in a LangGraph workflow.

## Environment Setup

### Prerequisites
1. **Trading Graph Server Running**
   - Server should be running on `http://localhost:8000` (development)
   - For production, use your deployed URL (e.g., `https://your-app.railway.app`)

2. **Required API Keys**
   The server requires the following environment variables:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   FINNHUB_API_KEY=your_finnhub_key_here  # For news & fundamentals
   SERPAPI_API_KEY=your_serpapi_key_here  # Optional but recommended
   ```

3. **Starting the Server (Development)**
   ```bash
   cd backend
   python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### 1. Health Check
**Endpoint:** `GET /health`  
**Purpose:** Verify server is running

**Example Request:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

### 2. Trading Analysis (Main Endpoint)
**Endpoint:** `POST /analyze`  
**Purpose:** Analyze a stock ticker and get trading recommendations

**Request Structure:**
```json
{
  "ticker": "TSLA"
}
```

**Response Structure:**
```json
{
  "ticker": "TSLA",
  "analysis_date": "2024-01-15",
  "market_report": "Technical analysis report...",
  "sentiment_report": "Social media sentiment analysis...",
  "news_report": "Recent news analysis...",
  "fundamentals_report": "Company fundamentals analysis...",
  "investment_plan": "Research manager's investment recommendation...",
  "trader_investment_plan": "Trader's specific trading plan...",
  "final_trade_decision": "Risk manager's final decision...",
  "processed_signal": "BUY/SELL/HOLD signal",
  "error": null
}
```

### 3. Streaming Analysis (Real-time Updates)
**Endpoint:** `GET /analyze/stream?ticker=TSLA`  
**Purpose:** Get real-time updates as analysis progresses (Server-Sent Events)

**Example Request:**
```bash
curl -N http://localhost:8000/analyze/stream?ticker=TSLA
```

**Event Types:**
- `status`: General status updates
- `agent_status`: Individual agent progress
- `progress`: Percentage completion
- `report`: Analysis reports as they complete
- `final_result`: Complete analysis result

## Testing Examples

### 1. Basic cURL Test
```bash
# Test analysis endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}' \
  | python3 -m json.tool
```

### 2. Postman Configuration
1. **Create new POST request**
   - URL: `http://localhost:8000/analyze`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON):
     ```json
     {
       "ticker": "TSLA"
     }
     ```

2. **Environment Variables (optional)**
   - `{{base_url}}`: `http://localhost:8000`
   - Use in URL: `{{base_url}}/analyze`

### 3. Python Test Script
```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TICKER = "TSLA"

# Test health endpoint
health_response = requests.get(f"{BASE_URL}/health")
print(f"Health Check: {health_response.json()}")

# Test analysis endpoint
analysis_payload = {"ticker": TICKER}
analysis_response = requests.post(
    f"{BASE_URL}/analyze",
    json=analysis_payload
)

if analysis_response.status_code == 200:
    result = analysis_response.json()
    print(f"\nAnalysis for {result['ticker']}:")
    print(f"Date: {result['analysis_date']}")
    print(f"Has Market Report: {'Yes' if result.get('market_report') else 'No'}")
    print(f"Has Final Decision: {'Yes' if result.get('final_trade_decision') else 'No'}")
    print(f"Signal: {result.get('processed_signal', 'N/A')}")
else:
    print(f"Error: {analysis_response.status_code}")
    print(analysis_response.text)
```

### 4. Flutter/Dart Test Code
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> testTradingAPI() async {
  final baseUrl = 'http://localhost:8000';
  
  // Test health
  final healthResponse = await http.get(Uri.parse('$baseUrl/health'));
  print('Health: ${healthResponse.body}');
  
  // Test analysis
  final analysisResponse = await http.post(
    Uri.parse('$baseUrl/analyze'),
    headers: {'Content-Type': 'application/json'},
    body: json.encode({'ticker': 'TSLA'}),
  );
  
  if (analysisResponse.statusCode == 200) {
    final result = json.decode(analysisResponse.body);
    print('Analysis completed for ${result['ticker']}');
    print('Signal: ${result['processed_signal']}');
  } else {
    print('Error: ${analysisResponse.statusCode}');
  }
}
```

## Expected Response Times
- **Health Check**: < 100ms
- **Full Analysis**: 30-120 seconds (depends on model and complexity)
- **Stream Events**: Real-time updates every 1-5 seconds

## Common Response Scenarios

### 1. Successful Analysis
```json
{
  "ticker": "TSLA",
  "analysis_date": "2024-01-15",
  "market_report": "Technical indicators show...",
  "sentiment_report": "Social media sentiment is positive...",
  "news_report": "Recent news highlights...",
  "fundamentals_report": "P/E ratio of 45.2...",
  "investment_plan": "Based on comprehensive analysis...",
  "trader_investment_plan": "Entry at $185, Stop loss at $175...",
  "final_trade_decision": "Moderate BUY recommendation...",
  "processed_signal": "BUY",
  "error": null
}
```

### 2. Invalid Ticker
```json
{
  "ticker": "",
  "analysis_date": "2024-01-15",
  "error": "Ticker cannot be empty"
}
```

### 3. Server Error
```json
{
  "ticker": "TSLA",
  "analysis_date": "2024-01-15",
  "error": "Failed to fetch market data: Connection timeout"
}
```

## Debugging Tips

### 1. Check Server Logs
The server provides detailed logging:
```
🚀 Starting Trading Analysis for TSLA on 2024-01-15
📋 Dispatcher: Initializing analysis workflow...
🔄 Running 4 Analysts in Parallel...
📊 Aggregator: Combining analyst reports...
⚖️ Research Debate: Bull vs Bear...
💼 Trader: Creating trading plan...
🛡️ Running 3 Risk Analysts in Parallel...
🎯 Risk Manager: Making final decision...
✅ Trading Analysis Complete
```

### 2. Common Issues

**Issue: "Connection refused"**
- Solution: Ensure server is running on correct port
- Check: `ps aux | grep uvicorn`

**Issue: "401 Unauthorized" or API errors**
- Solution: Verify API keys are set correctly
- Check: Environment variables in server

**Issue: "Timeout" errors**
- Solution: Analysis can take 30-120 seconds
- Consider: Using streaming endpoint for real-time updates

**Issue: Empty reports**
- Solution: Check if all required APIs are accessible
- Verify: FINNHUB_API_KEY for news/fundamentals

### 3. Validate Individual Components
Test each analyst separately by checking logs:
- Market Analyst: Should fetch Yahoo Finance data
- News Analyst: Requires FINNHUB_API_KEY
- Fundamentals Analyst: Requires FINNHUB_API_KEY
- Social Media Analyst: Works without external API

## Performance Monitoring

### Response Time Breakdown (typical):
- Market Analysis: 5-10s
- News Analysis: 3-5s
- Fundamentals Analysis: 3-5s
- Social Media Analysis: 2-3s
- Research Debate: 10-20s
- Trading Plan: 5-10s
- Risk Analysis: 15-25s
- Final Decision: 5-10s

**Total: 48-93 seconds average**

## Security Considerations

1. **API Keys**: Never expose API keys in client code
2. **CORS**: Server allows all origins in development (`*`)
3. **Rate Limiting**: Not implemented - consider for production
4. **Input Validation**: Server validates ticker format

## Integration Testing Checklist

- [ ] Server starts successfully
- [ ] Health endpoint returns 200 OK
- [ ] Analysis endpoint accepts POST request
- [ ] Valid ticker returns complete analysis
- [ ] Invalid ticker returns error message
- [ ] All report fields are populated
- [ ] Processing takes < 2 minutes
- [ ] Streaming endpoint sends real-time updates
- [ ] Error handling works correctly
- [ ] Results are saved to disk (check `backend/results/`)