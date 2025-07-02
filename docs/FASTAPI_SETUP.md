# TradingAgents FastAPI Setup Guide

## Overview
This guide explains how to run TradingAgents as a FastAPI server and integrate it with your Swift app.

## Prerequisites
- Python 3.8+
- API keys for OpenAI (or other LLM providers)
- Swift/SwiftUI project with ReSwift

## Python Server Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in the project root:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (defaults shown)
DEEP_THINK_MODEL=gpt-4o-mini
QUICK_THINK_MODEL=gpt-4o-mini
BACKEND_URL=https://api.openai.com/v1
```

### 3. Run the FastAPI Server
```bash
python run_api.py
```

The server will start at `http://localhost:8000`

### 4. Test the API
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test analysis endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

## Swift Integration

### 1. Add ReSwift to Your Project
In Xcode, go to File → Add Package Dependencies and add:
```
https://github.com/ReSwift/ReSwift
```

### 2. Copy Swift Files
Copy these files to your Swift project:
- `TradingAgents_Swift_Integration.swift` - Redux architecture and networking
- `TradingAnalysisView.swift` - SwiftUI views

### 3. Update Your App
In your main app file, initialize the store and show the view:

```swift
import SwiftUI
import ReSwift

@main
struct YourApp: App {
    var body: some Scene {
        WindowGroup {
            TradingAnalysisView()
        }
    }
}
```

### 4. Configure API URL
If running on a real device or different network, update the base URL in `TradingAgentsAPIService`:
```swift
private let baseURL = "http://your-server-ip:8000"
```

## API Endpoints

### POST /analyze
Analyzes a stock ticker.

**Request:**
```json
{
  "ticker": "AAPL"
}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "analysis_date": "2024-01-15",
  "market_report": "Technical analysis...",
  "sentiment_report": "Social sentiment analysis...",
  "news_report": "Recent news analysis...",
  "fundamentals_report": "Fundamental analysis...",
  "investment_plan": "Research team recommendation...",
  "trader_investment_plan": "Trading strategy...",
  "final_trade_decision": "Final decision...",
  "processed_signal": "BUY"
}
```

## Production Deployment

### Docker (Recommended)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t tradingagents-api .
docker run -p 8000:8000 --env-file .env tradingagents-api
```

### Security Considerations
1. Use HTTPS in production
2. Add API authentication
3. Implement rate limiting
4. Validate and sanitize inputs
5. Use environment-specific configurations

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure all dependencies are installed
2. **API key errors**: Check your `.env` file
3. **Connection refused**: Verify the server is running and accessible
4. **CORS errors**: Check CORS configuration matches your Swift app's needs

### Performance Tips
- The analysis can take 30-60 seconds depending on the LLM models
- Consider implementing caching for repeated requests
- Use background processing for long-running analyses