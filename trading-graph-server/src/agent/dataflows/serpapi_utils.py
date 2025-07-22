import os
import time
from datetime import datetime
from typing import List, Dict, Any
from serpapi import GoogleSearch
import logging

logger = logging.getLogger(__name__)

def getNewsDataSerpAPI(query: str, start_date: str, end_date: str, serpapi_key: str = None) -> List[Dict[str, Any]]:
    """
    Get news data using SerpAPI (much faster than web scraping).
    
    Args:
        query: Search query string
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        serpapi_key: SerpAPI key (if not provided, will use environment variable)
    
    Returns:
        List of dictionaries with news data
    """
    if not serpapi_key:
        serpapi_key = os.getenv("SERPAPI_API_KEY")
    
    if not serpapi_key:
        logger.error("❌ SerpAPI key not found. Please set SERPAPI_API_KEY environment variable.")
        raise ValueError("SerpAPI key not found. Please set SERPAPI_API_KEY environment variable.")
    
    # Convert dates to Google News format if needed
    if "-" in start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_dt.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_dt.strftime("%m/%d/%Y")
    
    news_results = []
    start_time = time.time()
    
    try:
        # SerpAPI parameters for Google News search
        params = {
            "engine": "google",
            "q": query,
            "tbm": "nws",  # News search
            "tbs": f"cdr:1,cd_min:{start_date},cd_max:{end_date}",  # Date range
            "api_key": serpapi_key,
            "num": 100,  # Get up to 100 results
            "hl": "en",  # Language
            "gl": "us",  # Country
        }
        
        logger.info(f"🔍 SerpAPI: Searching for '{query}' from {start_date} to {end_date}")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check for errors
        if "error" in results:
            logger.error(f"❌ SerpAPI Error: {results['error']}")
            raise Exception(f"SerpAPI Error: {results['error']}")
        
        # Extract news results
        news_items = results.get("news_results", [])
        
        for item in news_items:
            try:
                news_result = {
                    "link": item.get("link", ""),
                    "title": item.get("title", "No title"),
                    "snippet": item.get("snippet", "No snippet"),
                    "date": item.get("date", "No date"),
                    "source": item.get("source", "Unknown source"),
                }
                news_results.append(news_result)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing news item: {e}")
                continue
        
        duration = time.time() - start_time
        logger.info(f"✅ SerpAPI: Retrieved {len(news_results)} news items in {duration:.2f}s")
        
        return news_results
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ SerpAPI Error after {duration:.2f}s: {str(e)}")
        
        # Fallback to empty results rather than crashing
        logger.info("🔄 Returning empty results as fallback")
        return []


def getNewsDataSerpAPIWithPagination(query: str, start_date: str, end_date: str, 
                                     max_results: int = 300, serpapi_key: str = None) -> List[Dict[str, Any]]:
    """
    Get news data using SerpAPI with pagination support for more results.
    
    Args:
        query: Search query string
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_results: Maximum number of results to fetch
        serpapi_key: SerpAPI key (if not provided, will use environment variable)
    
    Returns:
        List of dictionaries with news data
    """
    if not serpapi_key:
        serpapi_key = os.getenv("SERPAPI_API_KEY")
    
    if not serpapi_key:
        logger.error("❌ SerpAPI key not found. Please set SERPAPI_API_KEY environment variable.")
        raise ValueError("SerpAPI key not found. Please set SERPAPI_API_KEY environment variable.")
    
    # Convert dates to Google News format if needed
    if "-" in start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_dt.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_dt.strftime("%m/%d/%Y")
    
    all_news_results = []
    start_time = time.time()
    page = 0
    
    try:
        while len(all_news_results) < max_results:
            # SerpAPI parameters for Google News search
            params = {
                "engine": "google",
                "q": query,
                "tbm": "nws",  # News search
                "tbs": f"cdr:1,cd_min:{start_date},cd_max:{end_date}",  # Date range
                "api_key": serpapi_key,
                "num": 100,  # Get up to 100 results per page
                "start": page * 100,  # Pagination offset
                "hl": "en",  # Language
                "gl": "us",  # Country
            }
            
            logger.info(f"🔍 SerpAPI: Page {page + 1} - Searching for '{query}' from {start_date} to {end_date}")
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for errors
            if "error" in results:
                logger.error(f"❌ SerpAPI Error: {results['error']}")
                break
            
            # Extract news results
            news_items = results.get("news_results", [])
            
            if not news_items:
                logger.info(f"📭 No more results found on page {page + 1}")
                break
            
            for item in news_items:
                try:
                    news_result = {
                        "link": item.get("link", ""),
                        "title": item.get("title", "No title"),
                        "snippet": item.get("snippet", "No snippet"),
                        "date": item.get("date", "No date"),
                        "source": item.get("source", "Unknown source"),
                    }
                    all_news_results.append(news_result)
                    
                    if len(all_news_results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing news item: {e}")
                    continue
            
            page += 1
            
            # Add small delay between requests to be respectful
            time.sleep(0.5)
        
        duration = time.time() - start_time
        logger.info(f"✅ SerpAPI: Retrieved {len(all_news_results)} news items in {duration:.2f}s across {page} pages")
        
        return all_news_results[:max_results]  # Ensure we don't exceed max_results
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ SerpAPI Error after {duration:.2f}s: {str(e)}")
        
        # Return whatever we managed to collect
        logger.info(f"🔄 Returning {len(all_news_results)} partial results as fallback")
        return all_news_results 