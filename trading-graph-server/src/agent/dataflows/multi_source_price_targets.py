#!/usr/bin/env python3
"""
Multi-Source Price Target Collector
Aggregates price targets from multiple APIs with intelligent fallback.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
import yfinance as yf
import httpx
import os

logger = logging.getLogger(__name__)

@dataclass
class PriceTargetData:
    """Unified price target data structure"""
    ticker: str
    current_price: float
    target_mean: float
    target_high: float
    target_low: float
    target_median: float
    analyst_count: int
    confidence: str  # HIGH, MEDIUM, LOW
    source: str
    raw_data: Dict[str, Any]

class MultiSourcePriceTargets:
    """
    Multi-source price target aggregator with intelligent fallback chain.
    
    Priority Order:
    1. yfinance (free, reliable)
    2. FMP (if API key available)
    3. Finnhub (fallback, often empty)
    4. Calculated estimate (last resort)
    """
    
    def __init__(self, finnhub_key: Optional[str] = None, fmp_key: Optional[str] = None):
        self.finnhub_key = finnhub_key
        self.fmp_key = fmp_key or os.environ.get('FMP_API_KEY')
        self.client = None
        
    async def setup(self):
        """Initialize HTTP client for API calls"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20)
        )
    
    async def cleanup(self):
        """Cleanup HTTP client"""
        if self.client:
            await self.client.aclose()
    
    async def get_price_targets(self, ticker: str) -> PriceTargetData:
        """
        Get price targets with multi-source fallback.
        
        Returns best available data from multiple sources.
        """
        logger.info(f"🎯 Fetching price targets for {ticker} from multiple sources...")
        
        # Strategy 1: Try yfinance first (most reliable free source)
        result = await self._get_yfinance_targets(ticker)
        if result and result.target_mean > 0:
            logger.info(f"✅ Got price targets from yfinance for {ticker}")
            return result
        
        # Strategy 2: Try FMP if API key available
        if self.fmp_key:
            result = await self._get_fmp_targets(ticker)
            if result and result.target_mean > 0:
                logger.info(f"✅ Got price targets from FMP for {ticker}")
                return result
        
        # Strategy 3: Try Finnhub (often empty on free tier)
        if self.finnhub_key:
            result = await self._get_finnhub_targets(ticker)
            if result and result.target_mean > 0:
                logger.info(f"✅ Got price targets from Finnhub for {ticker}")
                return result
        
        # Strategy 4: Calculate estimate based on fundamentals
        result = await self._calculate_estimate(ticker)
        logger.warning(f"⚠️ Using calculated estimate for {ticker} (no API data)")
        return result
    
    async def _get_yfinance_targets(self, ticker: str) -> Optional[PriceTargetData]:
        """Get price targets from yfinance (FREE, no API key needed)"""
        try:
            # Run yfinance in thread to avoid blocking
            def fetch_yfinance():
                stock = yf.Ticker(ticker)
                info = stock.info
                targets = stock.analyst_price_targets
                return info, targets
            
            import asyncio
            loop = asyncio.get_event_loop()
            info, targets = await loop.run_in_executor(None, fetch_yfinance)
            
            if targets and isinstance(targets, dict):
                # yfinance provides: current, mean, median, high, low
                return PriceTargetData(
                    ticker=ticker,
                    current_price=info.get('currentPrice', 0) or targets.get('current', 0),
                    target_mean=targets.get('mean', 0) or 0,
                    target_high=targets.get('high', 0) or 0,
                    target_low=targets.get('low', 0) or 0,
                    target_median=targets.get('median', 0) or 0,
                    analyst_count=info.get('numberOfAnalystOpinions', 0) or 0,
                    confidence="HIGH" if targets.get('mean', 0) > 0 else "LOW",
                    source="yfinance",
                    raw_data=targets
                )
            
        except Exception as e:
            logger.error(f"❌ yfinance error for {ticker}: {e}")
        
        return None
    
    async def _get_fmp_targets(self, ticker: str) -> Optional[PriceTargetData]:
        """Get price targets from Financial Modeling Prep"""
        if not self.fmp_key:
            return None
            
        try:
            url = f"https://financialmodelingprep.com/api/v4/price-target"
            params = {"symbol": ticker, "apikey": self.fmp_key}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data and len(data) > 0:
                # FMP returns array of analyst targets
                latest = data[0]
                
                # Calculate aggregates from analyst data
                all_targets = [d.get('priceTarget', 0) for d in data if d.get('priceTarget')]
                if all_targets:
                    return PriceTargetData(
                        ticker=ticker,
                        current_price=latest.get('adjClose', 0),
                        target_mean=sum(all_targets) / len(all_targets),
                        target_high=max(all_targets),
                        target_low=min(all_targets),
                        target_median=sorted(all_targets)[len(all_targets)//2],
                        analyst_count=len(all_targets),
                        confidence="HIGH",
                        source="FMP",
                        raw_data=data
                    )
                    
        except Exception as e:
            logger.error(f"❌ FMP error for {ticker}: {e}")
        
        return None
    
    async def _get_finnhub_targets(self, ticker: str) -> Optional[PriceTargetData]:
        """Get price targets from Finnhub (often empty on free tier)"""
        if not self.finnhub_key:
            return None
            
        try:
            url = "https://finnhub.io/api/v1/stock/price-target"
            params = {"symbol": ticker, "token": self.finnhub_key}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if data and data.get('targetMean', 0) > 0:
                return PriceTargetData(
                    ticker=ticker,
                    current_price=data.get('lastPrice', 0),
                    target_mean=data.get('targetMean', 0),
                    target_high=data.get('targetHigh', 0),
                    target_low=data.get('targetLow', 0),
                    target_median=data.get('targetMedian', 0),
                    analyst_count=data.get('numberOfAnalysts', 0),
                    confidence="MEDIUM",  # Often incomplete
                    source="Finnhub",
                    raw_data=data
                )
                
        except Exception as e:
            logger.error(f"❌ Finnhub error for {ticker}: {e}")
        
        return None
    
    async def _calculate_estimate(self, ticker: str) -> PriceTargetData:
        """Calculate price target estimate using simple valuation metrics"""
        try:
            # Use yfinance for basic data even if targets not available
            def fetch_info():
                stock = yf.Ticker(ticker)
                return stock.info
            
            import asyncio
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, fetch_info)
            
            current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
            pe_ratio = info.get('trailingPE', 0) or info.get('forwardPE', 0)
            
            if current_price > 0:
                # Simple sector-based P/E normalization
                sector = info.get('sector', '')
                target_pe = self._get_sector_target_pe(sector)
                
                if pe_ratio > 0:
                    # Adjust price based on P/E vs sector average
                    multiplier = target_pe / pe_ratio
                    estimated_target = current_price * multiplier
                    
                    # Cap extreme estimates
                    estimated_target = max(current_price * 0.5, 
                                         min(current_price * 2.0, estimated_target))
                else:
                    # No P/E, use conservative 10% upside
                    estimated_target = current_price * 1.1
                
                return PriceTargetData(
                    ticker=ticker,
                    current_price=current_price,
                    target_mean=estimated_target,
                    target_high=estimated_target * 1.15,
                    target_low=estimated_target * 0.85,
                    target_median=estimated_target,
                    analyst_count=0,
                    confidence="LOW",
                    source="Calculated",
                    raw_data={"method": "P/E normalization", "pe": pe_ratio}
                )
                
        except Exception as e:
            logger.error(f"❌ Calculation error for {ticker}: {e}")
        
        # Ultimate fallback - no data available
        return PriceTargetData(
            ticker=ticker,
            current_price=0,
            target_mean=0,
            target_high=0,
            target_low=0,
            target_median=0,
            analyst_count=0,
            confidence="NONE",
            source="No Data",
            raw_data={}
        )
    
    def _get_sector_target_pe(self, sector: str) -> float:
        """Get target P/E ratio by sector"""
        sector_pe = {
            "Technology": 25,
            "Healthcare": 22,
            "Financial Services": 15,
            "Consumer Cyclical": 20,
            "Consumer Defensive": 18,
            "Industrials": 18,
            "Energy": 12,
            "Utilities": 16,
            "Real Estate": 20,
            "Basic Materials": 15,
            "Communication Services": 20
        }
        return sector_pe.get(sector, 18)  # Default to 18

# Integration function for existing code
async def get_enhanced_price_targets(ticker: str, finnhub_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get enhanced price targets from multiple sources.
    
    This is the main entry point for the existing codebase.
    """
    collector = MultiSourcePriceTargets(finnhub_key=finnhub_key)
    await collector.setup()
    
    try:
        result = await collector.get_price_targets(ticker)
        
        # Convert to format expected by existing code
        return {
            "lastPrice": result.current_price,
            "targetMean": result.target_mean,
            "targetHigh": result.target_high,
            "targetLow": result.target_low,
            "targetMedian": result.target_median,
            "numberOfAnalysts": result.analyst_count,
            "confidence": result.confidence,
            "source": result.source,
            "lastUpdated": "real-time"
        }
        
    finally:
        await collector.cleanup()