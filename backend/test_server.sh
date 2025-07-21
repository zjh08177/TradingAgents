#!/bin/bash

echo "Starting test server with dummy API keys..."
echo "Note: This uses test API keys that may not work for real analysis"
echo "For production, set real API keys in your environment"

# Set test API keys (these are dummy values for testing)
export OPENAI_API_KEY="sk-test-dummy-key-for-testing"
export FINNHUB_API_KEY="test-finnhub-key"
export SERPAPI_API_KEY="test-serpapi-key"

# Start the server
echo "Starting server on http://localhost:8000"
python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000