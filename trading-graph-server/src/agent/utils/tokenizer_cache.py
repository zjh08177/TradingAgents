#!/usr/bin/env python3
"""
Global Tokenizer Cache - Phase 2 Performance Optimization
Singleton pattern to prevent multiple tokenizer initializations
"""

import tiktoken
from typing import Dict, Optional
import threading
import logging
import asyncio

logger = logging.getLogger(__name__)

class TokenizerCache:
    """
    Singleton tokenizer cache to prevent multiple initializations
    Thread-safe implementation with async support
    """
    _instance = None
    _lock = threading.Lock()
    _tokenizers: Dict[str, tiktoken.Encoding] = {}
    _init_count = 0  # Track initialization count for debugging
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.debug("🔧 TokenizerCache singleton created")
        return cls._instance
    
    def __init__(self):
        # Prevent re-initialization of the singleton
        if not hasattr(self, '_initialized'):
            self._initialized = True
            logger.debug("🔧 TokenizerCache initialized")
    
    def get_tokenizer(self, model_name: str) -> tiktoken.Encoding:
        """
        Get tokenizer for a model (thread-safe)
        Caches tokenizer instances to prevent re-initialization
        """
        if model_name not in self._tokenizers:
            with self._lock:
                # Double-check pattern
                if model_name not in self._tokenizers:
                    try:
                        logger.debug(f"🔧 Loading tokenizer for {model_name}")
                        self._tokenizers[model_name] = tiktoken.encoding_for_model(model_name)
                        self._init_count += 1
                        logger.debug(f"✅ Tokenizer loaded for {model_name} (total: {self._init_count})")
                    except KeyError:
                        logger.debug(f"⚠️ Model {model_name} not found, using default")
                        self._tokenizers[model_name] = tiktoken.get_encoding("cl100k_base")
                        self._init_count += 1
        
        return self._tokenizers[model_name]
    
    async def get_tokenizer_async(self, model_name: str) -> tiktoken.Encoding:
        """
        Async version of get_tokenizer
        Uses thread pool for initialization to prevent blocking
        """
        if model_name not in self._tokenizers:
            # Run initialization in thread pool
            await asyncio.to_thread(self.get_tokenizer, model_name)
        
        return self._tokenizers[model_name]
    
    def clear_cache(self):
        """Clear all cached tokenizers (mainly for testing)"""
        with self._lock:
            self._tokenizers.clear()
            self._init_count = 0
            logger.debug("🔧 TokenizerCache cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_models": len(self._tokenizers),
            "total_initializations": self._init_count,
            "models": list(self._tokenizers.keys())
        }

# Global function for easy access
def get_global_tokenizer(model_name: str) -> tiktoken.Encoding:
    """Get tokenizer from global cache"""
    cache = TokenizerCache()
    return cache.get_tokenizer(model_name)

async def get_global_tokenizer_async(model_name: str) -> tiktoken.Encoding:
    """Get tokenizer from global cache (async)"""
    cache = TokenizerCache()
    return await cache.get_tokenizer_async(model_name)