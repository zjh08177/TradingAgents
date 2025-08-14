#!/usr/bin/env python3
"""
Ultra-Fast News Analyst Implementation
Bypasses LLM calls for direct news data fetching and analysis.
Similar to market_analyst_ultra_fast.py and fundamentals_analyst_ultra_fast.py.
"""

import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import verification logging
from ..utils.verification_logging import global_tracker, verify_analyst_completion

# Import Universal Validator for comprehensive monitoring
from ..monitoring.universal_validator import validate, ValidationSeverity

# Import News Token Optimizer for 92.6% token reduction
from ..utils.news_token_optimizer import NewsTokenOptimizer, generate_optimized_news_report

logger = logging.getLogger(__name__)

# TOKEN OPTIMIZATION FLAG - Set to False to rollback to original behavior
USE_TOKEN_OPTIMIZATION = True

def create_news_analyst_ultra_fast(llm, toolkit):
    """Create ultra-fast news analyst node (bypasses LLM for direct API calls)"""
    
    async def news_analyst_ultra_fast_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Ultra-fast news analyst with direct API calls"""
        analyst_name = "news"
        start_time = time.time()
        
        # 🚨 RUNTIME VERIFICATION: Confirm ultra-fast version is running
        logger.critical("🔥🔥🔥 RUNTIME VERIFICATION: news_analyst_ultra_fast.py VERSION ACTIVE 🔥🔥🔥")
        logger.critical(f"🔥 TOKEN REDUCTION ENABLED: MAX_ARTICLES=15 limit is ACTIVE")
        logger.critical(f"🔥 Code version timestamp: 2025-01-14 - Ultra-fast with token limits")
        
        logger.info(f"📰 NEWS_ANALYST_ULTRA_FAST: Starting analysis")
        
        try:
            # Extract state parameters
            company = state.get("company_of_interest", "UNKNOWN")
            current_date = state.get("trade_date", "")
            
            logger.info(f"📰 NEWS_ANALYST_ULTRA_FAST: Analyzing {company} on {current_date}")
            
            # 🔍 UNIVERSAL VALIDATION: Tool call start validation for news gathering
            news_tool_validation = validate("tool_call_start", 
                                           tool_name="gather_news_data", 
                                           tool_args={"company": company, "current_date": current_date}, 
                                           context=f"news_data_gathering_{company}")
            if news_tool_validation.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                logger.error(f"🚨 NEWS TOOL CALL START VALIDATION FAILED: {news_tool_validation.message}")
            
            # Phase 1: Gather news data from multiple sources
            news_data_start = time.time()
            news_data = await gather_news_data(company, toolkit, start_time)
            news_data_time = time.time() - news_data_start
            
            # 🔍 UNIVERSAL VALIDATION: Tool call response validation for news data
            news_response_validation = validate("tool_call_response",
                                              tool_name="gather_news_data",
                                              response=news_data,
                                              execution_time=news_data_time,
                                              context=f"news_gather_{company}")
            if news_response_validation.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                logger.error(f"🚨 NEWS RESPONSE VALIDATION FAILED: {news_response_validation.message}")
            
            # 🔍 UNIVERSAL VALIDATION: Data completeness validation for news data
            if isinstance(news_data, dict):
                data_completeness_validation = validate("api_response",
                                                       response=news_data,
                                                       expected_schema={"serper_articles": list, "finnhub_articles": list},
                                                       context=f"news_data_structure_{company}")
                if data_completeness_validation.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    logger.error(f"🚨 NEWS DATA STRUCTURE VALIDATION FAILED: {data_completeness_validation.message}")
            
            # Phase 2: Analyze and generate structured report
            report = generate_news_report(company, news_data, current_date)
            
            # Phase 3: Log completion
            execution_time = time.time() - start_time
            verify_analyst_completion(analyst_name, "completed", execution_time, report)
            
            logger.info(f"📰 NEWS_ANALYST_ULTRA_FAST: Completed in {execution_time:.3f}s")
            logger.info(f"📊 NEWS_ANALYST_ULTRA_FAST: Report length: {len(report)} chars")
            
            # Prepare new state for validation
            new_state = {
                "news_report": report,
                "news_messages": [],  # No LLM messages needed
                "sender": "News Analyst (Ultra-Fast)"
            }
            
            # 🔍 UNIVERSAL VALIDATION: State transition validation
            state_validation = validate("state_transition",
                                      old_state=state,
                                      new_state={**state, **new_state},
                                      transition="news_analysis_complete")
            if state_validation.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                logger.error(f"🚨 NEWS STATE TRANSITION VALIDATION FAILED: {state_validation.message}")
            
            # 🔍 FINAL VALIDATION SUMMARY
            logger.info("🛡️ NEWS VALIDATION COMPLETE - All checks performed")
            
            return new_state
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"❌ NEWS_ANALYST_ULTRA_FAST: Error during analysis: {e}"
            logger.error(error_msg, exc_info=True)
            
            verify_analyst_completion(analyst_name, "error", execution_time, error_msg)
            
            # Return fallback report
            fallback_report = f"""⚠️ NEWS ANALYSIS ERROR

ERROR: Failed to fetch current news data for {company}
REASON: {str(e)}
STATUS: Using fallback analysis

RECOMMENDATION: Manual review required for {company} news sentiment.
"""
            
            return {
                "news_report": fallback_report,
                "news_messages": [],
                "sender": "News Analyst (Ultra-Fast - Error)"
            }
    
    return news_analyst_ultra_fast_node


async def gather_news_data(company: str, toolkit, start_time: float) -> Dict[str, Any]:
    """Gather news data from multiple sources with direct API calls"""
    
    news_data = {
        "serper_articles": [],
        "finnhub_articles": [],
        "total_articles": 0,
        "sources_attempted": 0,
        "sources_successful": 0,
        "data_fetch_time": 0
    }
    
    # Data collection start time
    data_start = time.time()
    
    # Try Serper API for Google News
    try:
        news_data["sources_attempted"] += 1
        logger.info("🔍 NEWS_ANALYST_ULTRA_FAST: Fetching Serper news data")
        
        # Direct import of serper utils
        from ..dataflows.serper_utils import getNewsDataSerperAPIWithPagination
        
        # Get API configuration
        config = getattr(toolkit, 'config', {})
        
        # Call Serper API directly
        serper_start = time.time()
        serper_articles = await getNewsDataSerperAPIWithPagination(
            query_or_company=company,
            max_pages=2,  # TOKEN OPTIMIZATION: Reduced from 5 to 2 pages to prevent token explosion
            config=config
        )
        serper_time = time.time() - serper_start
        
        if serper_articles:
            news_data["serper_articles"] = serper_articles
            news_data["sources_successful"] += 1
            news_data["total_articles"] += len(serper_articles)
            logger.info(f"✅ NEWS_ANALYST_ULTRA_FAST: Serper data fetched - {len(serper_articles)} articles in {serper_time:.3f}s")
        else:
            logger.warning("⚠️ NEWS_ANALYST_ULTRA_FAST: Serper API returned no results")
            
    except Exception as e:
        logger.error(f"❌ NEWS_ANALYST_ULTRA_FAST: Serper API error: {e}")
    
    # Try Finnhub API for financial news
    try:
        news_data["sources_attempted"] += 1
        logger.info("🔍 NEWS_ANALYST_ULTRA_FAST: Fetching Finnhub news data")
        
        # Use the Finnhub news tool
        if hasattr(toolkit, 'get_finnhub_news'):
            finnhub_start = time.time()
            
            # Calculate date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Call Finnhub news tool - use invoke method 
            finnhub_result = toolkit.get_finnhub_news.invoke({
                "ticker": company,  
                "start_date": start_date.strftime('%Y-%m-%d'), 
                "end_date": end_date.strftime('%Y-%m-%d')  
            })
            
            finnhub_time = time.time() - finnhub_start
            
            # Parse the result - it's typically a formatted string, we need to extract articles
            if finnhub_result and "No news" not in finnhub_result:
                # Convert the string result to a list format for consistency
                finnhub_articles = parse_finnhub_result(finnhub_result)
                news_data["finnhub_articles"] = finnhub_articles
                news_data["sources_successful"] += 1
                news_data["total_articles"] += len(finnhub_articles)
                logger.info(f"✅ NEWS_ANALYST_ULTRA_FAST: Finnhub data fetched - {len(finnhub_articles)} articles in {finnhub_time:.3f}s")
            else:
                logger.warning("⚠️ NEWS_ANALYST_ULTRA_FAST: Finnhub API returned no results")
        else:
            logger.warning("⚠️ NEWS_ANALYST_ULTRA_FAST: get_finnhub_news tool not available in toolkit")
                
    except Exception as e:
        logger.error(f"❌ NEWS_ANALYST_ULTRA_FAST: Finnhub API error: {e}")
    
    # Calculate total data fetch time
    news_data["data_fetch_time"] = time.time() - data_start
    
    logger.info(f"📊 NEWS_ANALYST_ULTRA_FAST: Data gathering complete")
    logger.info(f"   📰 Total articles: {news_data['total_articles']}")
    logger.info(f"   🎯 Sources successful: {news_data['sources_successful']}/{news_data['sources_attempted']}")
    logger.info(f"   ⏱️ Data fetch time: {news_data['data_fetch_time']:.3f}s")
    
    return news_data


def generate_news_report(company: str, news_data: Dict[str, Any], current_date: str) -> str:
    """Generate pure data collection report"""
    import json
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # TOKEN OPTIMIZATION: Use optimizer if enabled
    if USE_TOKEN_OPTIMIZATION:
        logger.critical("🔥🔥🔥 TOKEN OPTIMIZATION ENABLED 🔥🔥🔥")
        logger.critical(f"🔥 Using NewsTokenOptimizer for 92.6% token reduction")
        
        # Initialize the optimizer
        optimizer = NewsTokenOptimizer()
        
        # Get the raw articles
        serper_articles = news_data.get("serper_articles", [])
        finnhub_articles = news_data.get("finnhub_articles", [])
        
        # Optimize the articles
        optimized_articles = optimizer.optimize_news_data(serper_articles, finnhub_articles)
        
        # Generate optimized report
        optimized_report = generate_optimized_news_report(company, optimized_articles, timestamp)
        
        # Log comparison
        logger.critical(f"🔥 OPTIMIZATION COMPLETE:")
        logger.critical(f"🔥 Report size: {len(optimized_report)} chars (~{len(optimized_report)//4} tokens)")
        logger.critical(f"🔥 This replaces reports that would be 50,000+ chars")
        
        return optimized_report
    
    # CRITICAL: Apply token-aware filtering to prevent massive prompt tokens
    MAX_ARTICLES = 15  # Token optimization: limit to top 15 most relevant articles
    
    # 🚨 RUNTIME VERIFICATION: Log article limiting behavior
    total_available = len(news_data.get("serper_articles", [])) + len(news_data.get("finnhub_articles", []))
    logger.critical(f"🔥🔥🔥 ARTICLE LIMIT VERIFICATION 🔥🔥🔥")
    logger.critical(f"🔥 MAX_ARTICLES limit: {MAX_ARTICLES}")
    logger.critical(f"🔥 Total articles available: {total_available}")
    logger.critical(f"🔥 Articles will be limited to: {min(total_available, MAX_ARTICLES)}")
    
    # Prepare structured data
    all_articles = []
    
    # Add Serper articles (limited to prevent token explosion)
    serper_articles = news_data.get("serper_articles", [])[:MAX_ARTICLES]
    logger.critical(f"🔥 SERPER: Using {len(serper_articles)} of {len(news_data.get('serper_articles', []))} articles")
    logger.info(f"📰 TOKEN OPTIMIZATION: Using {len(serper_articles)} of {len(news_data.get('serper_articles', []))} Serper articles")
    
    for idx, article in enumerate(serper_articles):
        all_articles.append({
            "index": idx + 1,
            "api_source": "serper",
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "date": article.get("date", ""),
            "url": article.get("link", ""),
            "full_content": article.get("snippet", ""),
            "metadata": {
                "position": article.get("position", 0),
                "image_url": article.get("imageUrl", "")
            }
        })
    
    # Add Finnhub articles (limited to prevent token explosion)
    remaining_slots = max(0, MAX_ARTICLES - len(all_articles))
    finnhub_articles = news_data.get("finnhub_articles", [])[:remaining_slots]
    logger.critical(f"🔥 FINNHUB: Using {len(finnhub_articles)} of {len(news_data.get('finnhub_articles', []))} articles (remaining slots: {remaining_slots})")
    logger.info(f"📰 TOKEN OPTIMIZATION: Using {len(finnhub_articles)} of {len(news_data.get('finnhub_articles', []))} Finnhub articles")
    
    base_idx = len(serper_articles)
    for idx, article in enumerate(finnhub_articles):
        all_articles.append({
            "index": base_idx + idx + 1,
            "api_source": "finnhub",
            "title": article.get("headline", ""),
            "source": article.get("source", "Finnhub"),
            "date": article.get("date", ""),
            "url": article.get("url", ""),
            "full_content": article.get("summary", ""),
            "metadata": {
                "category": article.get("category", ""),
                "id": article.get("id", "")
            }
        })
    
    # 🚨 FINAL VERIFICATION: Confirm article count in final report
    logger.critical(f"🔥🔥🔥 FINAL ARTICLE COUNT VERIFICATION 🔥🔥🔥")
    logger.critical(f"🔥 TOTAL ARTICLES IN REPORT: {len(all_articles)}")
    logger.critical(f"🔥 This should be ≤ {MAX_ARTICLES} (current limit)")
    if len(all_articles) > MAX_ARTICLES:
        logger.critical(f"🚨🚨🚨 ERROR: Article count exceeds limit! {len(all_articles)} > {MAX_ARTICLES}")
        logger.critical(f"🚨 This indicates the token reduction is NOT working!")
    else:
        logger.critical(f"✅ Article count within limit: {len(all_articles)} ≤ {MAX_ARTICLES}")
    
    # Build data-only report
    report = f"""# NEWS DATA COLLECTION - {company}

Generated: {timestamp}
Trade Date: {current_date}

## COLLECTION METRICS (TOKEN OPTIMIZED)
- Articles Used: {len(all_articles)} (filtered for optimal token usage)
- Serper: {len(serper_articles)} articles (from {len(news_data.get('serper_articles', []))} available)
- Finnhub: {len(finnhub_articles)} articles (from {len(news_data.get('finnhub_articles', []))} available)
- Collection Time: {news_data.get('data_fetch_time', 0):.3f}s
- Token Optimization: Active (max {MAX_ARTICLES} articles)

## RAW ARTICLE DATA

"""
    
    # Add all articles without processing
    for article in all_articles:
        report += f"""### Article {article['index']}
Title: {article['title']}
Source: {article['source']}
Date: {article['date']}
URL: {article['url']}
Content: {article['full_content']}

"""
    
    # Add JSON for agents
    report += f"""## STRUCTURED DATA

```json
{json.dumps({
    "company": company,
    "date": current_date,
    "total": len(all_articles),
    "articles": all_articles
}, indent=2, default=str)}
```
"""
    
    return report


def extract_key_headlines(news_data: Dict[str, Any], company: str) -> List[Dict[str, Any]]:
    """Extract and rank key headlines from news data"""
    
    all_headlines = []
    
    # Process Serper articles
    for article in news_data.get("serper_articles", []):
        all_headlines.append({
            'title': article.get('title', ''),
            'source': article.get('source', ''),
            'snippet': article.get('snippet', ''),
            'url': article.get('link', ''),
            'date': article.get('date', ''),
            'priority': calculate_headline_priority(article, company),
            'type': 'serper'
        })
    
    # Process Finnhub articles
    for article in news_data.get("finnhub_articles", []):
        all_headlines.append({
            'title': article.get('headline', ''),
            'source': article.get('source', 'Finnhub'),
            'snippet': article.get('summary', ''),
            'url': article.get('url', ''),
            'date': datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d') if article.get('datetime') else '',
            'priority': calculate_headline_priority(article, company),
            'type': 'finnhub'
        })
    
    # Sort by priority (highest first)
    all_headlines.sort(key=lambda x: x['priority'], reverse=True)
    
    return all_headlines


def calculate_headline_priority(article: Dict[str, Any], company: str) -> int:
    """Calculate priority score for headlines (higher = more important)"""
    
    priority = 0
    title = (article.get('title') or article.get('headline', '')).lower()
    snippet = (article.get('snippet') or article.get('summary', '')).lower()
    source = article.get('source', '').lower()
    
    # Company name mention
    if company.lower() in title:
        priority += 10
    if company.lower() in snippet:
        priority += 5
    
    # High-impact keywords
    high_impact_keywords = [
        'earnings', 'revenue', 'profit', 'loss', 'merger', 'acquisition',
        'ceo', 'lawsuit', 'investigation', 'sec', 'fda', 'approval',
        'partnership', 'contract', 'deal', 'breakthrough', 'launch'
    ]
    
    for keyword in high_impact_keywords:
        if keyword in title:
            priority += 8
        if keyword in snippet:
            priority += 4
    
    # Source credibility
    tier1_sources = ['reuters', 'bloomberg', 'wall street journal', 'wsj']
    tier2_sources = ['cnbc', 'marketwatch', 'yahoo finance', 'forbes']
    
    if any(t1 in source for t1 in tier1_sources):
        priority += 6
    elif any(t2 in source for t2 in tier2_sources):
        priority += 3
    
    return priority


def parse_finnhub_result(finnhub_result: str) -> List[Dict[str, Any]]:
    """Parse Finnhub tool result string into article list format"""
    articles = []
    
    try:
        # The finnhub tool returns a formatted string, we need to extract the articles
        # Look for lines that contain article information
        lines = finnhub_result.split('\n')
        current_article = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for patterns like "Title: ..." or "Summary: ..."
            if line.startswith('Title:') or line.startswith('Headline:'):
                if current_article:
                    articles.append(current_article)
                    current_article = {}
                current_article['headline'] = line.split(':', 1)[1].strip()
                current_article['title'] = current_article['headline']
            elif line.startswith('Summary:') or line.startswith('Description:'):
                current_article['summary'] = line.split(':', 1)[1].strip()
            elif line.startswith('Source:'):
                current_article['source'] = line.split(':', 1)[1].strip()
            elif line.startswith('Date:') or line.startswith('Published:'):
                current_article['date'] = line.split(':', 1)[1].strip()
            elif line.startswith('URL:') or line.startswith('Link:'):
                current_article['url'] = line.split(':', 1)[1].strip()
        
        # Add the last article if exists
        if current_article:
            articles.append(current_article)
            
        # If no structured parsing worked, create a single article with the full text
        if not articles and finnhub_result.strip():
            articles.append({
                'headline': 'Financial News',
                'title': 'Financial News',
                'summary': finnhub_result.strip()[:500],  # First 500 chars
                'source': 'Finnhub',
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            
    except Exception as e:
        logger.warning(f"⚠️ Error parsing Finnhub result: {e}")
        # Fallback: create a single article with the raw result
        if finnhub_result.strip():
            articles.append({
                'headline': 'Financial News',
                'title': 'Financial News', 
                'summary': finnhub_result.strip()[:500],
                'source': 'Finnhub',
                'date': datetime.now().strftime('%Y-%m-%d')
            })
    
    return articles


def analyze_news_sentiment(news_data: Dict[str, Any], company: str) -> Dict[str, Any]:
    """Analyze overall news sentiment and generate trading implications"""
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    # Sentiment keywords
    positive_keywords = [
        'growth', 'profit', 'revenue', 'success', 'launch', 'expansion',
        'partnership', 'deal', 'approval', 'breakthrough', 'strong',
        'gains', 'beat', 'exceed', 'outperform', 'upgrade', 'buy'
    ]
    
    negative_keywords = [
        'loss', 'decline', 'fall', 'drop', 'concern', 'warning',
        'lawsuit', 'investigation', 'recall', 'failure', 'weak',
        'miss', 'disappoint', 'downgrade', 'sell', 'risk', 'issue'
    ]
    
    # Analyze all articles
    total_articles = 0
    for article in news_data.get("serper_articles", []) + news_data.get("finnhub_articles", []):
        total_articles += 1
        
        text_to_analyze = " ".join([
            (article.get('title') or article.get('headline', '')).lower(),
            (article.get('snippet') or article.get('summary', '')).lower()
        ])
        
        # Count sentiment indicators
        pos_score = sum(1 for keyword in positive_keywords if keyword in text_to_analyze)
        neg_score = sum(1 for keyword in negative_keywords if keyword in text_to_analyze)
        
        if pos_score > neg_score:
            positive_count += 1
        elif neg_score > pos_score:
            negative_count += 1
        else:
            neutral_count += 1
    
    # Determine overall sentiment
    if positive_count > negative_count:
        overall_sentiment = "POSITIVE"
        trading_signal = "BUY"
        confidence = "HIGH" if positive_count > negative_count * 1.5 else "MEDIUM"
        risk_level = "LOW"
        rationale = f"Positive news sentiment with {positive_count} positive vs {negative_count} negative indicators"
    elif negative_count > positive_count:
        overall_sentiment = "NEGATIVE"
        trading_signal = "SELL"
        confidence = "HIGH" if negative_count > positive_count * 1.5 else "MEDIUM"
        risk_level = "HIGH"
        rationale = f"Negative news sentiment with {negative_count} negative vs {positive_count} positive indicators"
    else:
        overall_sentiment = "NEUTRAL"
        trading_signal = "HOLD"
        confidence = "MEDIUM"
        risk_level = "MEDIUM"
        rationale = f"Mixed news sentiment with balanced positive/negative indicators"
    
    # Adjust confidence based on data quality
    if total_articles < 5:
        confidence = "LOW"
        rationale += " (Limited news data available)"
    
    return {
        "overall_sentiment": overall_sentiment,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "trading_signal": trading_signal,
        "confidence": confidence,
        "risk_level": risk_level,
        "rationale": rationale
    }


def classify_source_tier(source: str) -> str:
    """Factual classification of source authority"""
    source_lower = source.lower()
    
    tier_map = {
        "tier1": ["reuters", "bloomberg", "wsj", "wall street journal", "financial times"],
        "tier2": ["cnbc", "marketwatch", "forbes", "yahoo finance", "barron"],
        "tier3": ["seeking alpha", "motley fool", "investorplace"],
    }
    
    for tier, sources in tier_map.items():
        if any(s in source_lower for s in sources):
            return tier
    
    return "tier4"