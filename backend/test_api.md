# Testing the TradingAgents API

## 1. Start the API Server

First, make sure you're in the backend directory and have your environment activated:

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run_api.py
```

You should see:
```
🚀 Starting TradingAgents API server...
📍 Server will be available at http://localhost:8000
📚 API docs will be at http://localhost:8000/docs
```

## 2. Test Using FastAPI Interactive Docs

The easiest way to test is using FastAPI's built-in documentation:

1. Open your browser and go to: http://localhost:8000/docs
2. You'll see an interactive API documentation (Swagger UI)
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint

## 3. Test Individual Endpoints

### A. Test Root Endpoint
```bash
curl http://localhost:8000/
```

Expected response:
```json
{"message": "TradingAgents API is running"}
```

### B. Test Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### C. Test Analysis Endpoint (Main Functionality)
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

Expected response structure:
```json
{
  "ticker": "AAPL",
  "analysis_date": "2024-06-29",
  "market_report": "...",
  "sentiment_report": "...",
  "news_report": "...",
  "fundamentals_report": "...",
  "investment_plan": "...",
  "trader_investment_plan": "...",
  "final_trade_decision": "...",
  "processed_signal": "BUY/SELL/HOLD",
  "error": null
}
```

## 4. Test Using Python

Create a test script `test_api.py`:

```python
import requests
import json

# Test root endpoint
response = requests.get("http://localhost:8000/")
print("Root endpoint:", response.json())

# Test health check
response = requests.get("http://localhost:8000/health")
print("Health check:", response.json())

# Test analysis
data = {"ticker": "AAPL"}
response = requests.post(
    "http://localhost:8000/analyze",
    json=data
)
print("Analysis response status:", response.status_code)
if response.status_code == 200:
    result = response.json()
    print(f"Ticker: {result['ticker']}")
    print(f"Date: {result['analysis_date']}")
    print(f"Signal: {result.get('processed_signal', 'N/A')}")
    print(f"Error: {result.get('error', 'None')}")
```

## 5. Common Issues and Solutions

### Issue: Connection Refused
- **Solution**: Make sure the server is running (`python run_api.py`)

### Issue: Missing API Keys
- **Solution**: Ensure your `.env` file has:
  ```
  OPENAI_API_KEY=your_key_here
  FINNHUB_API_KEY=your_key_here
  ```

### Issue: Timeout or Slow Response
- **Solution**: The analysis can take 30-60 seconds as it involves multiple AI agents

## 6. Test from iOS App

1. Make sure the API server is running
2. Open the iOS app in Xcode
3. Run the app (⌘+R)
4. Enter a ticker and tap "Analyze"
5. Check Xcode console for any network errors 