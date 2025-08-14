#!/usr/bin/env python3
"""
Enhanced Price Target Collector with Multi-Source Fallback
Addresses Finnhub free tier limitations with intelligent data synthesis.
"""

import asyncio
import logging
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PriceTargetResult:
    """Enhanced price target result with confidence metrics"""
    current_price: float
    target_mean: float
    target_high: float
    target_low: float
    analyst_count: int
    confidence_level: str  # "HIGH", "MEDIUM", "LOW", "ESTIMATED"
    data_source: str
    last_updated: str
    intrinsic_estimate: Optional[float] = None

class EnhancedPriceTargetCollector:
    """Multi-source price target collector with Finnhub free tier workarounds"""
    
    def __init__(self, finnhub_key: str, alpha_vantage_key: Optional[str] = None):
        self.finnhub_key = finnhub_key
        self.alpha_vantage_key = alpha_vantage_key
        self.client = None
        
    async def setup(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=20)
        )
    
    async def get_price_targets(self, ticker: str) -> PriceTargetResult:
        """Get price targets with intelligent fallback chain"""
        
        # Strategy 1: Try Finnhub premium endpoint first
        result = await self._try_finnhub_price_targets(ticker)
        if result and result.analyst_count > 0:
            return result
            
        # Strategy 2: Extract from Finnhub recommendations 
        result = await self._extract_from_recommendations(ticker)
        if result and result.analyst_count > 0:
            return result
            
        # Strategy 3: Calculate intrinsic value estimate
        result = await self._calculate_intrinsic_estimate(ticker)
        if result:
            return result
            
        # Strategy 4: Return placeholder with clear limitations
        return self._create_limited_data_result(ticker)
    
    async def _try_finnhub_price_targets(self, ticker: str) -> Optional[PriceTargetResult]:
        """Try Finnhub price target endpoint (may be limited on free tier)"""
        try:
            url = f"https://finnhub.io/api/v1/stock/price-target"
            params = {"symbol": ticker, "token": self.finnhub_key}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            logger.info(f"🎯 FINNHUB PRICE TARGET RESPONSE for {ticker}: {data}")
            
            # Check if data is valid before using .get()
            if data is None or not isinstance(data, dict):
                logger.warning(f"⚠️ Invalid or null data from Finnhub price targets API for {ticker}")
                return None
            
            if (data.get("targetMean", 0) > 0 or 
                data.get("numberOfAnalysts", 0) > 0):
                
                return PriceTargetResult(
                    current_price=data.get("lastPrice", 0),
                    target_mean=data.get("targetMean", 0),
                    target_high=data.get("targetHigh", 0),
                    target_low=data.get("targetLow", 0),
                    analyst_count=data.get("numberOfAnalysts", 0),
                    confidence_level="HIGH",
                    data_source="Finnhub Premium",
                    last_updated=data.get("lastUpdated", "N/A")
                )
            else:
                logger.warning(f"🚨 Finnhub price targets empty for {ticker} (likely free tier limitation)")
                return None
                
        except Exception as e:
            logger.error(f"❌ Finnhub price target error for {ticker}: {e}")
            return None
    
    async def _extract_from_recommendations(self, ticker: str) -> Optional[PriceTargetResult]:
        """Extract price estimates from analyst recommendations"""
        try:
            url = f"https://finnhub.io/api/v1/stock/recommendation"
            params = {"symbol": ticker, "token": self.finnhub_key}
            
            response = await self.client.get(url, params=params)
            recommendations = response.json()
            
            # Check if recommendations is valid
            if (recommendations is None or 
                not isinstance(recommendations, list) or 
                len(recommendations) == 0):
                logger.warning(f"⚠️ Invalid or empty recommendations data for {ticker}")
                return None
                
            logger.info(f"📊 EXTRACTING from {len(recommendations)} recommendations for {ticker}")
            
            # Get latest recommendation and check it's a dict
            latest = recommendations[0]
            if not isinstance(latest, dict):
                logger.warning(f"⚠️ Invalid recommendation structure for {ticker}: {type(latest)}")
                return None
                
            total_analysts = (latest.get("strongBuy", 0) + latest.get("buy", 0) + 
                            latest.get("hold", 0) + latest.get("sell", 0) + 
                            latest.get("strongSell", 0))
            
            if total_analysts > 0:
                # Get current stock price for context
                current_price = await self._get_current_price(ticker)
                
                # Estimate price targets based on recommendation distribution
                bullish_ratio = (latest.get("strongBuy", 0) + latest.get("buy", 0)) / total_analysts
                bearish_ratio = (latest.get("sell", 0) + latest.get("strongSell", 0)) / total_analysts
                
                # Heuristic: Strong buy suggests 15-25% upside, Buy suggests 5-15%
                if bullish_ratio > 0.6:  # Majority bullish
                    estimated_upside = 0.20  # 20% upside
                elif bullish_ratio > 0.4:  # Somewhat bullish
                    estimated_upside = 0.10  # 10% upside
                elif bearish_ratio > 0.4:  # Bearish
                    estimated_upside = -0.05  # 5% downside
                else:  # Neutral
                    estimated_upside = 0.05  # 5% upside
                
                target_mean = current_price * (1 + estimated_upside)
                target_high = current_price * (1 + estimated_upside + 0.10)
                target_low = current_price * (1 + estimated_upside - 0.10)
                
                return PriceTargetResult(
                    current_price=current_price,
                    target_mean=target_mean,
                    target_high=target_high,
                    target_low=target_low,
                    analyst_count=total_analysts,
                    confidence_level="MEDIUM",
                    data_source="Analyst Recommendations (Derived)",
                    last_updated=latest.get("period", "N/A")
                )
                
        except Exception as e:
            logger.error(f"❌ Recommendations extraction error for {ticker}: {e}")
            return None
    
    async def _calculate_intrinsic_estimate(self, ticker: str) -> Optional[PriceTargetResult]:
        """Calculate intrinsic value estimate using fundamental metrics"""
        try:
            # Get basic metrics for calculation
            url = f"https://finnhub.io/api/v1/stock/metric"
            params = {"symbol": ticker, "metric": "all", "token": self.finnhub_key}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Check if data is valid before using .get()
            if data is None or not isinstance(data, dict):
                logger.warning(f"⚠️ Invalid or null data from metrics API for {ticker}")
                return None
            
            metrics = data.get("metric", {})
            if not metrics:
                return None
            
            current_price = await self._get_current_price(ticker)
            
            # Simple intrinsic value using P/E ratio normalization
            pe_ratio = metrics.get("peBasicExclExtraTTM")
            industry_avg_pe = 20  # Conservative industry average
            
            if pe_ratio and pe_ratio > 0:
                # If P/E is above average, suggest downside; if below, suggest upside
                fair_value_multiplier = industry_avg_pe / pe_ratio
                intrinsic_estimate = current_price * fair_value_multiplier
                
                # Cap extreme estimates
                intrinsic_estimate = max(current_price * 0.5, min(current_price * 2.0, intrinsic_estimate))
                
                return PriceTargetResult(
                    current_price=current_price,
                    target_mean=intrinsic_estimate,
                    target_high=intrinsic_estimate * 1.15,
                    target_low=intrinsic_estimate * 0.85,
                    analyst_count=1,  # Algorithmic estimate
                    confidence_level="LOW",
                    data_source="Intrinsic Value (P/E Based)",
                    last_updated="Real-time",
                    intrinsic_estimate=intrinsic_estimate
                )
                
        except Exception as e:
            logger.error(f"❌ Intrinsic calculation error for {ticker}: {e}")
            return None
    
    async def _get_current_price(self, ticker: str) -> float:
        """Get current stock price"""
        try:
            url = f"https://finnhub.io/api/v1/quote"
            params = {"symbol": ticker, "token": self.finnhub_key}
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Check if data is valid before using .get()
            if data is None or not isinstance(data, dict):
                logger.warning(f"⚠️ Invalid price data for {ticker}")
                return 0
            
            return data.get("c", 0)  # Current price
            
        except Exception:
            return 0
    
    def _create_limited_data_result(self, ticker: str) -> PriceTargetResult:
        """Create result indicating data limitations"""
        return PriceTargetResult(
            current_price=0,
            target_mean=0,
            target_high=0,
            target_low=0,
            analyst_count=0,
            confidence_level="LIMITED",
            data_source="Data Not Available (Free Tier)",
            last_updated="N/A"
        )

# Integration function for existing collector
async def enhance_price_targets_data(fundamental_data: Dict[str, Any], 
                                   ticker: str, 
                                   finnhub_key: str) -> Dict[str, Any]:
    """Enhance existing fundamental data with improved price targets"""
    
    collector = EnhancedPriceTargetCollector(finnhub_key)
    await collector.setup()
    
    try:
        enhanced_targets = await collector.get_price_targets(ticker)
        
        # Replace existing price_targets with enhanced data
        fundamental_data["price_targets"] = {
            "lastPrice": enhanced_targets.current_price,
            "targetMean": enhanced_targets.target_mean,
            "targetHigh": enhanced_targets.target_high,
            "targetLow": enhanced_targets.target_low,
            "numberOfAnalysts": enhanced_targets.analyst_count,
            "confidence": enhanced_targets.confidence_level,
            "source": enhanced_targets.data_source,
            "lastUpdated": enhanced_targets.last_updated
        }
        
        logger.info(f"✅ Enhanced price targets for {ticker}: "
                   f"Mean=${enhanced_targets.target_mean:.2f}, "
                   f"Analysts={enhanced_targets.analyst_count}, "
                   f"Source={enhanced_targets.data_source}")
        
    except Exception as e:
        logger.error(f"❌ Price target enhancement failed for {ticker}: {e}")
    
    return fundamental_data