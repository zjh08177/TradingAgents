#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 TradingAgents API Verification"
echo "================================"

# Check if server is running
echo -n "Checking if API server is running... "
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running${NC}"
    echo -e "${YELLOW}Please start the server with: python run_api.py${NC}"
    exit 1
fi

# Test root endpoint
echo -n "Testing root endpoint... "
ROOT_RESPONSE=$(curl -s http://localhost:8000/)
if [[ $ROOT_RESPONSE == *"TradingAgents API is running"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

# Test health endpoint
echo -n "Testing health endpoint... "
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

# Check environment variables
echo ""
echo "Checking environment variables:"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OPENAI_API_KEY not set${NC}"
else
    echo -e "${GREEN}✓ OPENAI_API_KEY is set${NC}"
fi

if [ -z "$FINNHUB_API_KEY" ]; then
    echo -e "${RED}✗ FINNHUB_API_KEY not set${NC}"
else
    echo -e "${GREEN}✓ FINNHUB_API_KEY is set${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}API verification complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:8000/docs for interactive API docs"
echo "2. Run 'python test_api.py' for comprehensive testing"
echo "3. Test from iOS app or use curl commands" 