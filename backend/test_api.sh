#!/bin/bash

# TradingAgents API Test Script
# Usage: ./test_api.sh TICKER [OPTIONS]
# Example: ./test_api.sh TSLA
# Example: ./test_api.sh AAPL --limit 20
# Example: ./test_api.sh META --timeout 60

# Default values
TICKER=${1:-AAPL}
LIMIT=""
TIMEOUT=""
BASE_URL="http://localhost:8000"

# Parse additional arguments
shift
while [[ $# -gt 0 ]]; do
  case $1 in
    --limit)
      LIMIT="| head -n $2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="timeout $2"
      shift 2
      ;;
    --health)
      echo "🏥 Testing health endpoint..."
      curl -s "$BASE_URL/health" && echo
      exit 0
      ;;
    --help)
      echo "Usage: $0 TICKER [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --limit N     Show only first N events"
      echo "  --timeout N   Stop after N seconds"
      echo "  --health      Test health endpoint only"
      echo "  --help        Show this help"
      echo ""
      echo "Examples:"
      echo "  $0 TSLA"
      echo "  $0 AAPL --limit 20"
      echo "  $0 META --timeout 60"
      echo "  $0 --health"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Testing TradingAgents API${NC}"
echo -e "${YELLOW}📊 Ticker: $TICKER${NC}"
echo -e "${YELLOW}🌐 URL: $BASE_URL/analyze/stream?ticker=$TICKER${NC}"
echo ""

# Test health first
echo -e "${BLUE}🏥 Checking server health...${NC}"
if curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Server is healthy${NC}"
else
    echo -e "${RED}❌ Server is not responding${NC}"
    echo -e "${YELLOW}💡 Make sure to start the server first:${NC}"
    echo -e "${YELLOW}   cd backend && source venv/bin/activate && python run_api.py${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📡 Starting streaming analysis...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Build the command
CMD="curl -N -H \"Accept: text/event-stream\" -H \"Connection: keep-alive\" -H \"Cache-Control: no-cache\" \"$BASE_URL/analyze/stream?ticker=$TICKER\""

if [[ -n "$TIMEOUT" ]]; then
    CMD="$TIMEOUT $CMD"
fi

if [[ -n "$LIMIT" ]]; then
    CMD="$CMD $LIMIT"
fi

# Execute the command
eval $CMD 