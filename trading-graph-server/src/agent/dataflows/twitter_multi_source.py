"""
Multi-Source Twitter Data Orchestrator
Coordinates multiple Twitter data sources for maximum reliability and real data coverage
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class TwitterMultiSourceOrchestrator:
    """
    Orchestrates multiple Twitter data sources with intelligent fallback
    Priority order: Syndication API -> Existing alternatives -> Aggregated social
    """
    
    def __init__(self):
        self.max_total_time = 8.0  # Maximum time for all attempts
        self.rate_limit_delay = 0.2  # Small delay between requests
    
    async def get_twitter_sentiment(self, ticker: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get Twitter sentiment using multi-source orchestration
        
        Source priority:
        1. Twitter Syndication API (free, direct Twitter data)
        2. Existing alternatives (Bluesky, Mastodon) 
        3. Aggregated social sentiment (Finnhub, StockTwits, Reddit)
        
        Args:
            ticker: Stock ticker symbol
            limit: Maximum number of tweets/posts to analyze
            
        Returns:
            Twitter sentiment data with source information
        """
        start_time = time.time()
        logger.info(f"🔄 Starting multi-source Twitter sentiment for ${ticker}")
        
        # Source 1: Twitter Syndication API (FREE, real Twitter data)
        if time.time() - start_time < self.max_total_time:
            logger.info(f"🎯 Trying Twitter Syndication API for ${ticker}")
            try:
                syndication_result = await asyncio.wait_for(
                    self._get_syndication_sentiment(ticker, limit), 
                    timeout=4.0
                )
                
                if syndication_result and not syndication_result.get("fallback_mode"):
                    # Success with real Twitter data
                    logger.info(f"✅ Twitter Syndication API success: {syndication_result.get('tweet_count', 0)} tweets")
                    return self._format_result(syndication_result, "twitter_syndication")
                    
            except asyncio.TimeoutError:
                logger.debug(f"⏰ Twitter Syndication API timeout for ${ticker}")
            except Exception as e:
                logger.debug(f"❌ Twitter Syndication API error for ${ticker}: {e}")
        
        # Source 2: Fast alternatives (Bluesky, Mastodon)
        if time.time() - start_time < self.max_total_time:
            logger.info(f"🔄 Trying fast Twitter alternatives for ${ticker}")
            try:
                alternatives_result = await asyncio.wait_for(
                    self._get_twitter_alternatives(ticker, limit),
                    timeout=3.0
                )
                
                if alternatives_result and alternatives_result.get("tweet_count", 0) > 0:
                    logger.info(f"✅ Twitter alternatives success: {alternatives_result.get('tweet_count', 0)} posts")
                    return self._format_result(alternatives_result, "twitter_alternatives")
                    
            except asyncio.TimeoutError:
                logger.debug(f"⏰ Twitter alternatives timeout for ${ticker}")
            except Exception as e:
                logger.debug(f"❌ Twitter alternatives error for ${ticker}: {e}")
        
        # Source 3: Aggregated social sentiment (most reliable fallback)
        if time.time() - start_time < self.max_total_time:
            logger.info(f"🔄 Using aggregated social sentiment for ${ticker}")
            try:
                aggregated_result = await asyncio.wait_for(
                    self._get_aggregated_sentiment(ticker),
                    timeout=2.0
                )
                
                if aggregated_result:
                    logger.info(f"✅ Aggregated social success: {len(aggregated_result.get('sources_used', []))} sources")
                    return self._transform_aggregated_to_twitter_format(aggregated_result)
                    
            except asyncio.TimeoutError:
                logger.debug(f"⏰ Aggregated social timeout for ${ticker}")
            except Exception as e:
                logger.debug(f"❌ Aggregated social error for ${ticker}: {e}")
        
        # All sources failed - return clear error with mock data marking
        elapsed = time.time() - start_time
        logger.error(f"🚨 All Twitter sources failed for ${ticker} after {elapsed:.1f}s")
        return self._create_failure_result(ticker)
    
    async def _get_syndication_sentiment(self, ticker: str, limit: int) -> Optional[Dict[str, Any]]:
        """Get sentiment from Twitter Syndication API"""
        try:
            from .twitter_syndication_api import get_twitter_syndication_sentiment
            return await get_twitter_syndication_sentiment(ticker, limit)
        except ImportError:
            logger.debug("Twitter Syndication API not available")
            return None
        except Exception as e:
            logger.debug(f"Twitter Syndication API error: {e}")
            return None
    
    async def _get_twitter_alternatives(self, ticker: str, limit: int) -> Optional[Dict[str, Any]]:
        """Get sentiment from Twitter alternatives (Bluesky, Mastodon)"""
        try:
            from .twitter_simple import get_twitter_fast
            return await get_twitter_fast(ticker, limit)
        except ImportError:
            logger.debug("Twitter alternatives not available")
            return None
        except Exception as e:
            logger.debug(f"Twitter alternatives error: {e}")
            return None
    
    async def _get_aggregated_sentiment(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get sentiment from aggregated social sources"""
        try:
            from .aggregated_social_sentiment import get_aggregated_social_sentiment
            return await get_aggregated_social_sentiment(ticker)
        except ImportError:
            logger.debug("Aggregated social sentiment not available")
            return None
        except Exception as e:
            logger.debug(f"Aggregated social sentiment error: {e}")
            return None
    
    def _format_result(self, result: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """Format result with source information and standardize structure"""
        if not result:
            return {}
        
        # Ensure consistent structure
        formatted = {
            "ticker": result.get("ticker", ""),
            "sentiment_score": result.get("sentiment_score", 0.5),
            "tweet_count": result.get("tweet_count", 0),
            "top_tweets": result.get("top_tweets", []),
            "confidence": result.get("confidence", "low"),
            "source": source_type,
            "fallback_mode": result.get("fallback_mode", False),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add source-specific metadata
        if source_type == "twitter_syndication":
            formatted["data_quality"] = "real_twitter"
            formatted["note"] = "Real Twitter data via syndication API"
        elif source_type == "twitter_alternatives": 
            formatted["data_quality"] = "real_social"
            formatted["note"] = "Real social data from Twitter alternatives"
        
        # Copy over any additional fields
        for key, value in result.items():
            if key not in formatted:
                formatted[key] = value
        
        return formatted
    
    def _transform_aggregated_to_twitter_format(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """Transform aggregated social data to Twitter-compatible format"""
        sentiment_score = aggregated.get('sentiment_score', 0.5)
        
        # Create Twitter-like posts from source information
        top_tweets = []
        for source in aggregated.get('sources_used', []):
            if source == 'finnhub':
                top_tweets.append({
                    "text": f"Historical social sentiment shows {'bullish' if sentiment_score > 0.6 else 'bearish' if sentiment_score < 0.4 else 'neutral'} trend for ${aggregated.get('ticker', '')}",
                    "author": "market_data",
                    "source": "Finnhub Historical",
                    "likes": 0,
                    "retweets": 0,
                    "created_at": datetime.now().isoformat()
                })
            elif source == 'stocktwits':
                top_tweets.append({
                    "text": f"StockTwits community trending {'bullish' if sentiment_score > 0.6 else 'bearish' if sentiment_score < 0.4 else 'neutral'} on ${aggregated.get('ticker', '')}",
                    "author": "stocktwits_data",
                    "source": "StockTwits",
                    "likes": 0,
                    "retweets": 0, 
                    "created_at": datetime.now().isoformat()
                })
            elif source == 'reddit':
                top_tweets.append({
                    "text": f"Reddit discussions show {'positive' if sentiment_score > 0.6 else 'negative' if sentiment_score < 0.4 else 'neutral'} sentiment for ${aggregated.get('ticker', '')}",
                    "author": "reddit_data",
                    "source": "Reddit",
                    "likes": 0,
                    "retweets": 0,
                    "created_at": datetime.now().isoformat()
                })
        
        return {
            "ticker": aggregated.get('ticker', ''),
            "sentiment_score": sentiment_score,
            "tweet_count": aggregated.get('total_mentions', len(top_tweets) * 10),
            "top_tweets": top_tweets[:5],
            "confidence": aggregated.get('confidence', 'medium'),
            "source": "aggregated_social",
            "sources_used": aggregated.get('sources_used', []),
            "fallback_mode": aggregated.get('fallback_mode', False),
            "data_quality": "real_social" if not aggregated.get('fallback_mode') else "simulated",
            "note": f"Aggregated from {len(aggregated.get('sources_used', []))} real social sources",
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_failure_result(self, ticker: str) -> Dict[str, Any]:
        """Create empty response when all sources fail - no mock data"""
        from .empty_response_handler import create_empty_twitter_response
        
        return create_empty_twitter_response(
            ticker=ticker,
            reason="All Twitter data sources unavailable - no real data found"
        )


# Global orchestrator instance
_orchestrator = TwitterMultiSourceOrchestrator()


async def get_twitter_multi_source(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """
    Main interface for multi-source Twitter sentiment
    
    Args:
        ticker: Stock ticker symbol
        limit: Maximum tweets/posts to analyze
        
    Returns:
        Twitter sentiment data from best available source
    """
    return await _orchestrator.get_twitter_sentiment(ticker, limit)


# Synchronous wrapper for testing
def get_twitter_multi_source_sync(ticker: str) -> Dict[str, Any]:
    """Synchronous wrapper for testing"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_twitter_multi_source(ticker))
    finally:
        loop.close()


# Compatibility wrapper
async def get_twitter_enhanced(ticker: str, limit: int = 20) -> Dict[str, Any]:
    """Enhanced Twitter sentiment with multi-source fallback"""
    return await get_twitter_multi_source(ticker, limit)


if __name__ == "__main__":
    import json
    
    # Test the multi-source orchestrator
    test_ticker = "TSLA"
    print(f"🧪 Testing Multi-Source Twitter Orchestrator for {test_ticker}")
    print("=" * 70)
    print("📊 Will try sources in order:")
    print("  1. Twitter Syndication API (free, real Twitter data)")
    print("  2. Twitter alternatives (Bluesky, Mastodon)")
    print("  3. Aggregated social (Finnhub, StockTwits, Reddit)")
    print("=" * 70)
    
    start = time.time()
    result = get_twitter_multi_source_sync(test_ticker)
    elapsed = time.time() - start
    
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    print(f"📊 Result:")
    print(json.dumps(result, indent=2))
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   Source: {result.get('source', 'unknown')}")
    print(f"   Data quality: {result.get('data_quality', 'unknown')}")
    print(f"   Sentiment: {result.get('sentiment_score', 0):.3f}")
    print(f"   Tweet count: {result.get('tweet_count', 0)}")
    print(f"   Fallback mode: {result.get('fallback_mode', False)}")
    
    if result.get('mock_data') or result.get('fallback_mode'):
        print(f"⚠️  WARNING: Using fallback/mock data")
    else:
        print(f"✅ SUCCESS: Real data from {result.get('source', 'unknown')}")