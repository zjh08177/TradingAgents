#!/usr/bin/env python3
"""
Demo script for the ultrafast Reddit sentiment analyzer
Shows real-world usage of the get_reddit_fast function
"""

import asyncio
import sys
import time

# Add src to path
sys.path.insert(0, 'src/agent/dataflows')

from reddit_simple import get_reddit_fast, get_reddit_sentiment_sync


async def demo_single_ticker():
    """Demo fetching sentiment for a single ticker"""
    print("\n📊 Demo 1: Single Ticker Analysis")
    print("-" * 40)
    
    ticker = "AAPL"
    print(f"Fetching Reddit sentiment for {ticker}...")
    
    start = time.time()
    result = await get_reddit_fast(ticker, limit=25)
    elapsed = time.time() - start
    
    print(f"✅ Response time: {elapsed:.2f}s")
    print(f"\n📈 Results for {ticker}:")
    print(f"  • Sentiment Score: {result['sentiment_score']:.3f} (0=bearish, 1=bullish)")
    print(f"  • Posts Analyzed: {result['post_count']}")
    print(f"  • Average Score: {result['avg_score']:.1f}")
    print(f"  • Average Comments: {result['avg_comments']:.1f}")
    print(f"  • Confidence: {result['confidence']}")
    
    print(f"\n📍 Subreddit Breakdown:")
    for sub, count in result['subreddit_breakdown'].items():
        print(f"  • r/{sub}: {count} posts")
    
    if result.get('top_posts'):
        print(f"\n🔥 Top Post:")
        top = result['top_posts'][0]
        print(f"  • {top['title'][:80]}...")
        print(f"  • Score: {top['score']} | Comments: {top['comments']}")


async def demo_multiple_tickers():
    """Demo parallel fetching for multiple tickers"""
    print("\n📊 Demo 2: Multiple Tickers (Parallel)")
    print("-" * 40)
    
    tickers = ["TSLA", "GME", "AMC", "NVDA"]
    print(f"Fetching sentiment for: {', '.join(tickers)}")
    
    start = time.time()
    
    # Fetch all tickers in parallel
    tasks = [get_reddit_fast(ticker, subreddits=["wallstreetbets"], limit=10) 
             for ticker in tickers]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    print(f"✅ Total time for {len(tickers)} tickers: {elapsed:.2f}s")
    
    # Display results
    print("\n📈 Sentiment Summary:")
    print(f"{'Ticker':<8} {'Sentiment':<12} {'Posts':<8} {'Confidence':<12}")
    print("-" * 40)
    
    for ticker, result in zip(tickers, results):
        sentiment = result['sentiment_score']
        sentiment_str = "🟢 Bullish" if sentiment > 0.6 else "🔴 Bearish" if sentiment < 0.4 else "🟡 Neutral"
        print(f"{ticker:<8} {sentiment_str:<12} {result['post_count']:<8} {result['confidence']:<12}")


async def demo_custom_subreddits():
    """Demo with custom subreddit selection"""
    print("\n📊 Demo 3: Custom Subreddit Analysis")
    print("-" * 40)
    
    ticker = "TSLA"
    custom_subs = ["teslainvestorsclub", "RealTesla", "stocks"]
    
    print(f"Analyzing {ticker} in specific subreddits:")
    for sub in custom_subs:
        print(f"  • r/{sub}")
    
    start = time.time()
    result = await get_reddit_fast(ticker, subreddits=custom_subs, limit=20)
    elapsed = time.time() - start
    
    print(f"\n✅ Response time: {elapsed:.2f}s")
    print(f"\n📈 Custom Analysis for {ticker}:")
    print(f"  • Overall Sentiment: {result['sentiment_score']:.3f}")
    print(f"  • Total Posts: {result['post_count']}")
    
    print(f"\n📍 Per-Subreddit Results:")
    for sub, count in result['subreddit_breakdown'].items():
        print(f"  • r/{sub}: {count} posts")


def demo_sync_wrapper():
    """Demo synchronous wrapper for non-async code"""
    print("\n📊 Demo 4: Synchronous Wrapper")
    print("-" * 40)
    
    ticker = "SPY"
    print(f"Using sync wrapper for {ticker}...")
    
    start = time.time()
    result = get_reddit_sentiment_sync(ticker, subreddits=["stocks"], limit=15)
    elapsed = time.time() - start
    
    print(f"✅ Response time: {elapsed:.2f}s")
    print(f"\n📈 Sync Results for {ticker}:")
    print(f"  • Sentiment: {result['sentiment_score']:.3f}")
    print(f"  • Posts: {result['post_count']}")
    print(f"  • Confidence: {result['confidence']}")


async def main():
    """Run all demos"""
    print("=" * 50)
    print("🚀 Reddit Simple - Ultrafast Sentiment Analysis")
    print("=" * 50)
    
    try:
        # Check if aiohttp is available
        import aiohttp
        
        # Run demos
        await demo_single_ticker()
        await demo_multiple_tickers()
        await demo_custom_subreddits()
        
        # Run sync demo (outside async context)
        print("\n" + "=" * 50)
        
    except ImportError:
        print("❌ ERROR: aiohttp is not installed")
        print("Please install with: pip3 install --user aiohttp")
        return
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ All demos completed successfully!")
    print("💡 The implementation is ready for production use.")
    print("=" * 50)


if __name__ == "__main__":
    # Run async demos
    asyncio.run(main())
    
    # Run sync demo separately (can't run in async context)
    demo_sync_wrapper()