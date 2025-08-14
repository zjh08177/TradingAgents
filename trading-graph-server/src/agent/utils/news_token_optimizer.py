#!/usr/bin/env python3
"""
News Token Optimizer - Reduces news report tokens by 92.6%
Following the architecture from claude_doc/agent_improvement_plans/token-optimization/news_optimization_architecture.md
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsTokenOptimizer:
    """
    Optimize news data for minimal token consumption
    Target: <1000 tokens for entire news report (92.6% reduction)
    """
    
    MAX_ARTICLES = 15
    MAX_SNIPPET_LENGTH = 150
    MAX_TITLE_LENGTH = 100
    
    def __init__(self):
        """Initialize the optimizer with trading keywords"""
        self.trading_keywords = [
            'earnings', 'revenue', 'profit', 'price target', 
            'upgrade', 'downgrade', 'guidance', 'outlook',
            'beat', 'miss', 'exceed', 'growth', 'decline',
            'merger', 'acquisition', 'partnership', 'deal',
            'ceo', 'lawsuit', 'investigation', 'sec', 'fda'
        ]
        
        self.positive_words = [
            'beat', 'exceed', 'growth', 'upgrade', 'strong', 'gain',
            'outperform', 'success', 'breakthrough', 'approval', 'expand'
        ]
        
        self.negative_words = [
            'miss', 'decline', 'downgrade', 'weak', 'loss', 'fall',
            'underperform', 'failure', 'lawsuit', 'investigation', 'recall'
        ]
    
    def optimize_news_data(self, serper_articles: List[Dict], finnhub_articles: List[Dict]) -> List[Dict[str, Any]]:
        """
        Optimize news articles for token efficiency
        Target: <1000 tokens for entire news report
        
        Args:
            serper_articles: Articles from Serper API
            finnhub_articles: Articles from Finnhub API
            
        Returns:
            List of optimized articles with minimal token usage
        """
        optimized_articles = []
        
        # Log optimization start
        logger.critical("🔥 NEWS TOKEN OPTIMIZER: Starting optimization")
        logger.critical(f"🔥 Input: {len(serper_articles)} Serper + {len(finnhub_articles)} Finnhub articles")
        
        # Process Serper articles (prioritized for relevance)
        for article in serper_articles[:12]:  # Leave room for Finnhub
            optimized_article = {
                'title': self.truncate_text(article.get('title', ''), self.MAX_TITLE_LENGTH),
                'snippet': self.extract_key_snippet(article.get('snippet', ''), self.MAX_SNIPPET_LENGTH),
                'source': self.truncate_text(article.get('source', 'Unknown'), 30),
                'sentiment': self.quick_sentiment(article)
            }
            optimized_articles.append(optimized_article)
        
        # Add top Finnhub articles
        remaining_slots = self.MAX_ARTICLES - len(optimized_articles)
        for article in finnhub_articles[:remaining_slots]:
            optimized_article = {
                'title': self.truncate_text(article.get('headline', ''), self.MAX_TITLE_LENGTH),
                'snippet': self.extract_key_snippet(article.get('summary', ''), self.MAX_SNIPPET_LENGTH),
                'source': 'Finnhub',
                'sentiment': self.quick_sentiment(article)
            }
            optimized_articles.append(optimized_article)
        
        # Calculate token savings
        original_chars = sum([
            len(str(article.get('title', ''))) + 
            len(str(article.get('snippet', '') or article.get('summary', ''))) + 
            len(str(article.get('source', '')))
            for article in (serper_articles + finnhub_articles)
        ])
        
        optimized_chars = sum([
            len(a['title']) + len(a['snippet']) + len(a['source']) + len(a['sentiment'])
            for a in optimized_articles
        ])
        
        reduction_pct = (1 - optimized_chars/max(original_chars, 1)) * 100
        
        logger.critical(f"🔥 TOKEN OPTIMIZATION COMPLETE:")
        logger.critical(f"🔥 Articles: {len(optimized_articles)} (limited to {self.MAX_ARTICLES})")
        logger.critical(f"🔥 Original size: {original_chars} chars")
        logger.critical(f"🔥 Optimized size: {optimized_chars} chars")
        logger.critical(f"🔥 Reduction: {reduction_pct:.1f}%")
        logger.critical(f"🔥 Estimated tokens saved: {int((original_chars - optimized_chars) / 4)}")
        
        return optimized_articles
    
    def extract_key_snippet(self, text: str, max_length: int) -> str:
        """
        Extract most relevant portion of snippet
        Prioritizes sentences with trading keywords
        """
        if not text:
            return ""
        
        text = str(text)  # Ensure string type
        
        # Look for sentences with trading keywords
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in self.trading_keywords):
                # Found a high-value sentence, use it
                return self.truncate_text(sentence.strip(), max_length)
        
        # No keyword sentences found, use beginning of text
        return self.truncate_text(text, max_length)
    
    def quick_sentiment(self, article: Dict) -> str:
        """
        Quick sentiment classification based on keywords
        Returns: POSITIVE, NEGATIVE, or NEUTRAL
        """
        # Combine title and snippet for analysis
        text = (
            str(article.get('title', '') or article.get('headline', '')) + ' ' + 
            str(article.get('snippet', '') or article.get('summary', ''))
        ).lower()
        
        # Count sentiment indicators
        pos_score = sum(1 for word in self.positive_words if word in text)
        neg_score = sum(1 for word in self.negative_words if word in text)
        
        # Determine sentiment
        if pos_score > neg_score:
            return "POSITIVE"
        elif neg_score > pos_score:
            return "NEGATIVE"
        return "NEUTRAL"
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text to max length, preserving word boundaries
        """
        if not text:
            return ""
        
        text = str(text)  # Ensure string type
        
        if len(text) <= max_length:
            return text.strip()
        
        # Truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we have a reasonable word boundary
            truncated = truncated[:last_space]
        
        return truncated.strip()


def generate_optimized_news_report(company: str, optimized_articles: List[Dict], timestamp: str) -> str:
    """
    Generate token-optimized news report
    Target: <4000 characters total (<1000 tokens)
    """
    
    report = f"""# NEWS SUMMARY - {company}
Generated: {timestamp}

## METRICS
Articles: {len(optimized_articles)} | Token-Optimized

## NEWS HEADLINES
"""
    
    for i, article in enumerate(optimized_articles, 1):
        report += f"""
{i}. {article['title']}
   Source: {article['source']} | Sentiment: {article['sentiment']}
   {article['snippet']}
"""
    
    # Add sentiment summary
    sentiments = [a['sentiment'] for a in optimized_articles]
    positive = sentiments.count('POSITIVE')
    negative = sentiments.count('NEGATIVE')
    neutral = sentiments.count('NEUTRAL')
    
    # Determine overall signal
    if positive > negative:
        signal = 'BULLISH'
    elif negative > positive:
        signal = 'BEARISH'
    else:
        signal = 'NEUTRAL'
    
    report += f"""

## SENTIMENT OVERVIEW
Positive: {positive} | Negative: {negative} | Neutral: {neutral}
Signal: {signal}
"""
    
    # Log final report size
    logger.critical(f"🔥 OPTIMIZED REPORT SIZE: {len(report)} chars (~{len(report)//4} tokens)")
    
    return report