"""
Smart Caching System for Tool Execution
Optimization 3: Implement Smart Caching to reduce redundant API calls
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached tool result"""
    value: Any
    timestamp: datetime
    tool_name: str
    hash_key: str
    hit_count: int = 0

class ToolCache:
    """Smart caching system for tool execution results"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttls = {
            # Market data changes slowly during market hours
            "get_YFin_data": 300,                    # 5 minutes
            "get_YFin_data_online": 300,             # 5 minutes
            "get_stockstats_indicators_report": 300, # 5 minutes
            
            # Fundamentals change quarterly
            "get_fundamentals_openai": 1800,         # 30 minutes
            "get_simfin_balance_sheet": 3600,        # 1 hour
            "get_simfin_income_stmt": 3600,          # 1 hour
            "get_simfin_cashflow": 3600,             # 1 hour
            
            # News is time-sensitive but can be cached briefly
            "get_global_news_openai": 300,           # 5 minutes
            "get_google_news": 300,                  # 5 minutes
            "get_finnhub_news": 300,                 # 5 minutes
            "get_reddit_news": 180,                  # 3 minutes
            
            # Social sentiment changes frequently
            "get_reddit_stock_info": 180,            # 3 minutes
            "get_stocktwits_sentiment": 120,         # 2 minutes
            "get_twitter_mentions": 120,             # 2 minutes
            
            # Insider data changes infrequently
            "get_finnhub_company_insider_sentiment": 1800,     # 30 minutes
            "get_finnhub_company_insider_transactions": 1800,  # 30 minutes
        }
        
        # Cache statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_calls": 0
        }
        
        logger.info("🧠 ToolCache initialized with smart TTL strategies")
    
    def _create_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Create a consistent cache key from tool name and arguments"""
        # Sort args to ensure consistent key generation
        sorted_args = json.dumps(args, sort_keys=True, default=str)
        key_data = f"{tool_name}:{sorted_args}"
        
        # Use hash for consistent, short keys
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_or_fetch(self, 
                     tool_name: str, 
                     args: Dict[str, Any], 
                     fetcher: Callable, 
                     ttl: Optional[int] = None) -> Any:
        """
        Get cached result or fetch new data
        
        Args:
            tool_name: Name of the tool being cached
            args: Tool arguments (used for cache key)
            fetcher: Function to call if cache miss
            ttl: Time-to-live in seconds (optional, uses defaults)
        
        Returns:
            Cached or freshly fetched result
        """
        self._stats["total_calls"] += 1
        cache_key = self._create_cache_key(tool_name, args)
        
        # Determine TTL
        if ttl is None:
            ttl = self._default_ttls.get(tool_name, 300)  # Default 5 minutes
        
        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            
            # Check if still valid
            if datetime.now() - entry.timestamp < timedelta(seconds=ttl):
                entry.hit_count += 1
                self._stats["hits"] += 1
                
                logger.info(f"✅ Cache HIT: {tool_name} (age: {(datetime.now() - entry.timestamp).seconds}s, hits: {entry.hit_count})")
                return entry.value
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                self._stats["evictions"] += 1
                logger.info(f"⏰ Cache EXPIRED: {tool_name} (age: {(datetime.now() - entry.timestamp).seconds}s)")
        
        # Cache miss - fetch new data
        self._stats["misses"] += 1
        logger.info(f"❌ Cache MISS: {tool_name} (fetching...)")
        
        try:
            result = fetcher()
            
            # Store in cache
            entry = CacheEntry(
                value=result,
                timestamp=datetime.now(),
                tool_name=tool_name,
                hash_key=cache_key,
                hit_count=0
            )
            self._cache[cache_key] = entry
            
            logger.info(f"💾 Cache STORE: {tool_name} (TTL: {ttl}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cache FETCH failed for {tool_name}: {e}")
            raise
    
    def invalidate(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Invalidate a specific cache entry"""
        cache_key = self._create_cache_key(tool_name, args)
        
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"🗑️ Cache INVALIDATED: {tool_name}")
            return True
        return False
    
    def clear_all(self) -> int:
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"🧹 Cache CLEARED: {count} entries removed")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "cached_entries": len(self._cache),
            "cache_size_mb": self._estimate_cache_size()
        }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB (rough approximation)"""
        if not self._cache:
            return 0.0
        
        # Sample a few entries to estimate average size
        sample_size = min(5, len(self._cache))
        sample_entries = list(self._cache.values())[:sample_size]
        
        total_size = 0
        for entry in sample_entries:
            # Rough estimate of entry size
            try:
                size = len(str(entry.value)) + len(entry.tool_name) + len(entry.hash_key)
                total_size += size
            except:
                total_size += 1000  # Fallback estimate
        
        avg_size = total_size / sample_size if sample_size > 0 else 1000
        total_estimated = avg_size * len(self._cache)
        
        return total_estimated / (1024 * 1024)  # Convert to MB
    
    def log_performance_summary(self):
        """Log cache performance summary"""
        stats = self.get_stats()
        
        logger.info(f"""
🧠 CACHE PERFORMANCE SUMMARY:
   📊 Total Calls: {stats['total_calls']}
   ✅ Cache Hits: {stats['hits']} ({stats['hit_rate']:.1f}%)
   ❌ Cache Misses: {stats['misses']}
   ⏰ Evictions: {stats['evictions']}
   💾 Cached Entries: {stats['cached_entries']}
   📏 Cache Size: {stats['cache_size_mb']:.2f} MB
   🎯 Performance: {'EXCELLENT' if stats['hit_rate'] > 40 else 'GOOD' if stats['hit_rate'] > 20 else 'NEEDS IMPROVEMENT'}
        """)

# Global cache instance
_global_cache: Optional[ToolCache] = None

def get_tool_cache() -> ToolCache:
    """Get the global tool cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ToolCache()
    return _global_cache

def clear_tool_cache():
    """Clear the global tool cache"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_all()
        _global_cache = None