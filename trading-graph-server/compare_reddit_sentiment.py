#!/usr/bin/env python3
"""
Compare Reddit sentiment for multiple tickers
Usage: python3 compare_reddit_sentiment.py TICKER1 TICKER2 ...
"""

import sys
import os
import json
import glob
from datetime import datetime

def load_latest_analysis(ticker, output_dir='reddit_analysis_results'):
    """Load the most recent analysis for a ticker"""
    pattern = os.path.join(output_dir, f'reddit_analysis_{ticker}_*.json')
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    
    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except:
        return None

def compare_tickers(tickers):
    """Create comparative analysis of multiple tickers"""
    results = []
    
    for ticker in tickers:
        data = load_latest_analysis(ticker)
        if data:
            results.append(data)
        else:
            print(f"⚠️  No data found for {ticker}")
    
    if not results:
        print("No data to compare")
        return
    
    # Print header
    print("\n" + "=" * 80)
    print("📊 REDDIT SENTIMENT COMPARISON")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tickers analyzed: {', '.join(tickers)}")
    print()
    
    # Create comparison table
    print(f"{'Ticker':<8} {'Sentiment':<12} {'Posts':<10} {'Trend':<12} {'Confidence':<12} {'Signal'}")
    print("-" * 80)
    
    # Sort by sentiment score
    results.sort(key=lambda x: x.get('summary', {}).get('average_sentiment', 0), reverse=True)
    
    for data in results:
        ticker = data['ticker']
        summary = data.get('summary', {})
        sentiment = summary.get('average_sentiment', 0)
        posts = summary.get('total_posts_analyzed', 0)
        trend = summary.get('sentiment_trend', 'unknown')
        
        # Get confidence from latest period
        confidence = 'low'
        for period in ['day', 'week', 'month']:
            if period in data.get('analysis', {}):
                confidence = data['analysis'][period].get('confidence', 'low')
                if confidence != 'low':
                    break
        
        # Determine signal
        if sentiment > 0.7:
            signal = '🟢 BUY'
        elif sentiment > 0.55:
            signal = '🟡 HOLD'
        else:
            signal = '🔴 SELL'
        
        print(f"{ticker:<8} {sentiment:<12.3f} {posts:<10} {trend:<12} {confidence:<12} {signal}")
    
    print("=" * 80)
    
    # Summary statistics
    if len(results) > 1:
        print("\n📈 SUMMARY STATISTICS")
        print("-" * 40)
        
        # Best and worst
        best = max(results, key=lambda x: x.get('summary', {}).get('average_sentiment', 0))
        worst = min(results, key=lambda x: x.get('summary', {}).get('average_sentiment', 0))
        
        print(f"🏆 Most Bullish: {best['ticker']} (sentiment: {best['summary']['average_sentiment']:.3f})")
        print(f"📉 Most Bearish: {worst['ticker']} (sentiment: {worst['summary']['average_sentiment']:.3f})")
        
        # Most discussed
        most_discussed = max(results, key=lambda x: x.get('summary', {}).get('total_posts_analyzed', 0))
        least_discussed = min(results, key=lambda x: x.get('summary', {}).get('total_posts_analyzed', 0))
        
        print(f"🔥 Most Discussed: {most_discussed['ticker']} ({most_discussed['summary']['total_posts_analyzed']} posts)")
        print(f"🤫 Least Discussed: {least_discussed['ticker']} ({least_discussed['summary']['total_posts_analyzed']} posts)")
        
        # Overall metrics
        total_posts = sum(r.get('summary', {}).get('total_posts_analyzed', 0) for r in results)
        avg_sentiment = sum(r.get('summary', {}).get('average_sentiment', 0) for r in results) / len(results)
        
        print(f"\n📊 Overall Metrics:")
        print(f"  • Total posts analyzed: {total_posts}")
        print(f"  • Average sentiment: {avg_sentiment:.3f}")
        
        # Trend analysis
        rising = [r['ticker'] for r in results if r.get('summary', {}).get('sentiment_trend') == 'rising']
        falling = [r['ticker'] for r in results if r.get('summary', {}).get('sentiment_trend') == 'falling']
        
        if rising:
            print(f"  • Rising trend: {', '.join(rising)}")
        if falling:
            print(f"  • Falling trend: {', '.join(falling)}")
    
    print("\n" + "=" * 80)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compare_reddit_sentiment.py TICKER1 TICKER2 ...")
        print("Example: python3 compare_reddit_sentiment.py AAPL TSLA GME NVDA")
        sys.exit(1)
    
    tickers = [t.upper() for t in sys.argv[1:]]
    compare_tickers(tickers)

if __name__ == "__main__":
    main()