#!/bin/bash

# Batch Reddit Analysis Script
# Usage: ./batch_reddit_analysis.sh TICKER1 TICKER2 TICKER3 ...
# Example: ./batch_reddit_analysis.sh AAPL TSLA GME NVDA
# Output: Comparative analysis saved to reddit_analysis_results/

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No ticker symbols provided${NC}"
    echo "Usage: $0 TICKER1 TICKER2 TICKER3 ..."
    echo "Example: $0 AAPL TSLA GME NVDA"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="reddit_analysis_results"
SUMMARY_FILE="${OUTPUT_DIR}/batch_summary_${TIMESTAMP}.txt"

mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 Batch Reddit Sentiment Analysis${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${CYAN}Analyzing tickers: $@${NC}"
echo ""

# Create summary header
{
    echo "================================================"
    echo "BATCH REDDIT SENTIMENT ANALYSIS"
    echo "Generated: $(date)"
    echo "================================================"
    echo ""
} > "$SUMMARY_FILE"

# Process each ticker
for TICKER in "$@"; do
    echo -e "${YELLOW}Processing ${TICKER}...${NC}"
    
    # Run the analysis
    ./test_reddit_api.sh "$TICKER" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${TICKER} complete${NC}"
        
        # Find the most recent file for this ticker
        LATEST_FILE=$(ls -t ${OUTPUT_DIR}/reddit_analysis_${TICKER}_*.json 2>/dev/null | head -1)
        
        if [ -f "$LATEST_FILE" ]; then
            # Extract summary data and append to summary file
            python3 -c "
import json

with open('$LATEST_FILE', 'r') as f:
    data = json.load(f)
    
print(f\"TICKER: {data['ticker']}\")
print('-' * 40)

summary = data.get('summary', {})
print(f\"Sentiment Score: {summary.get('average_sentiment', 0):.3f}\")
print(f\"Total Posts: {summary.get('total_posts_analyzed', 0)}\")
print(f\"Trend: {summary.get('sentiment_trend', 'unknown')}\")
print(f\"Recommendation: {summary.get('recommendation', 'N/A')}\")

# Time period breakdown
for period in ['day', 'week', 'month']:
    if period in data.get('analysis', {}):
        p = data['analysis'][period]
        if 'sentiment_score' in p:
            print(f\"  {period.capitalize()}: {p['sentiment_score']:.3f} ({p.get('post_count', 0)} posts)\")

print()
" >> "$SUMMARY_FILE"
        fi
    else
        echo -e "${RED}❌ ${TICKER} failed${NC}"
        echo "TICKER: $TICKER" >> "$SUMMARY_FILE"
        echo "ERROR: Analysis failed" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    fi
done

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Creating comparative analysis...${NC}"
echo -e "${BLUE}================================================${NC}"

# Create comparison table
python3 << EOF
import json
import os
from datetime import datetime

output_dir = '$OUTPUT_DIR'
tickers = """$@""".split()

# Collect all data
results = []
for ticker in tickers:
    # Find most recent file for ticker
    files = [f for f in os.listdir(output_dir) if f.startswith(f'reddit_analysis_{ticker}_') and f.endswith('.json')]
    if files:
        files.sort(reverse=True)
        latest = files[0]
        with open(os.path.join(output_dir, latest), 'r') as f:
            data = json.load(f)
            results.append(data)

if results:
    print('\n📊 COMPARATIVE ANALYSIS')
    print('=' * 70)
    print(f\"{'Ticker':<8} {'Sentiment':<12} {'Posts':<8} {'Trend':<10} {'Signal':<8}\")
    print('-' * 70)
    
    for data in sorted(results, key=lambda x: x.get('summary', {}).get('average_sentiment', 0), reverse=True):
        ticker = data['ticker']
        summary = data.get('summary', {})
        sentiment = summary.get('average_sentiment', 0)
        posts = summary.get('total_posts_analyzed', 0)
        trend = summary.get('sentiment_trend', 'unknown')
        
        # Determine signal emoji
        if sentiment > 0.7:
            signal = '🟢 BUY'
        elif sentiment > 0.55:
            signal = '🟡 HOLD'
        else:
            signal = '🔴 SELL'
        
        print(f\"{ticker:<8} {sentiment:<12.3f} {posts:<8} {trend:<10} {signal:<8}\")
    
    print('=' * 70)
    
    # Find best and worst
    if len(results) > 1:
        best = max(results, key=lambda x: x.get('summary', {}).get('average_sentiment', 0))
        worst = min(results, key=lambda x: x.get('summary', {}).get('average_sentiment', 0))
        
        print(f\"\n🏆 Most Bullish: {best['ticker']} ({best['summary']['average_sentiment']:.3f})\")
        print(f\"📉 Most Bearish: {worst['ticker']} ({worst['summary']['average_sentiment']:.3f})\")
    
    # Volume analysis
    total_posts = sum(r.get('summary', {}).get('total_posts_analyzed', 0) for r in results)
    print(f\"\n📈 Total Posts Analyzed: {total_posts}\")
    
    most_discussed = max(results, key=lambda x: x.get('summary', {}).get('total_posts_analyzed', 0))
    print(f"🔥 Most Discussed: {most_discussed['ticker']} ({most_discussed['summary']['total_posts_analyzed']} posts)")
EOF

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Batch analysis complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${CYAN}Summary saved to: ${SUMMARY_FILE}${NC}"
echo -e "${CYAN}Individual results in: ${OUTPUT_DIR}/${NC}"
echo ""
echo "View summary with:"
echo "  cat $SUMMARY_FILE"