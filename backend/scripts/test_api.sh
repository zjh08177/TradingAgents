#!/bin/bash

# Test script for TradingAgents API

echo "🚀 Starting TradingAgents API Test"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API is running
echo -e "\n${YELLOW}1. Checking if API is running...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ API is running${NC}"
else
    echo -e "${RED}❌ API is not running. Starting it now...${NC}"
    # Start API in background
    cd backend
    python3 run_api.py &
    API_PID=$!
    echo "API started with PID: $API_PID"
    echo "Waiting for API to be ready..."
    sleep 5
fi

# Test health endpoint
echo -e "\n${YELLOW}2. Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "Response: $HEALTH_RESPONSE"

# Test root endpoint
echo -e "\n${YELLOW}3. Testing root endpoint...${NC}"
ROOT_RESPONSE=$(curl -s http://localhost:8000/)
echo "Response: $ROOT_RESPONSE"

# Test analysis endpoint
echo -e "\n${YELLOW}4. Testing analysis endpoint with ticker: UNH${NC}"
echo "This may take 30-60 seconds..."

# Make the API call and save response
START_TIME=$(date +%s)
ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "UNH"}')
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Check if response contains error
if echo "$ANALYSIS_RESPONSE" | grep -q '"error"'; then
    echo -e "${RED}❌ Analysis failed with error:${NC}"
    echo "$ANALYSIS_RESPONSE" | python3 -m json.tool | grep -A2 '"error"'
    EXIT_CODE=1
else
    echo -e "${GREEN}✅ Analysis completed successfully in ${DURATION} seconds${NC}"
    
    # Check for required fields
    echo -e "\n${YELLOW}Checking for required fields:${NC}"
    
    FIELDS=("ticker" "analysis_date" "market_report" "sentiment_report" "news_report" "fundamentals_report" "final_trade_decision" "processed_signal")
    
    for field in "${FIELDS[@]}"; do
        if echo "$ANALYSIS_RESPONSE" | grep -q "\"$field\""; then
            echo -e "${GREEN}✅ $field: present${NC}"
        else
            echo -e "${RED}❌ $field: missing${NC}"
        fi
    done
    
    # Extract signal
    SIGNAL=$(echo "$ANALYSIS_RESPONSE" | grep -o '"processed_signal":"[^"]*"' | cut -d'"' -f4)
    echo -e "\n${YELLOW}Trading Signal: ${GREEN}$SIGNAL${NC}"
    
    EXIT_CODE=0
fi

# Save response to file for debugging
echo "$ANALYSIS_RESPONSE" > test_api_response.json
echo -e "\n${YELLOW}Full response saved to: test_api_response.json${NC}"

# Summary
echo -e "\n${YELLOW}=================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
fi
echo -e "${YELLOW}==================================${NC}"

exit $EXIT_CODE