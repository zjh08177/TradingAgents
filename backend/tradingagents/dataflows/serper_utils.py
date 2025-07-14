import os
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def getNewsDataSerperAPI(query: str, start_date: str, end_date: str, serper_key: str = None) -> List[Dict[str, Any]]:
    """
    Get news data using Serper API (replacement for SerpAPI).
    
    Args:
        query: Search query string
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        serper_key: Serper API key (if not provided, will use environment variable)
    
    Returns:
        List of dictionaries with news data
    """
    if not serper_key:
        serper_key = os.getenv("SERPER_API_KEY")
    
    if not serper_key:
        logger.error("❌ Serper API key not found. Please set SERPER_API_KEY environment variable.")
        raise ValueError("Serper API key not found. Please set SERPER_API_KEY environment variable.")
    
    news_results = []
    start_time = time.time()
    
    try:
        # Serper API endpoint
        url = "https://google.serper.dev/news"
        
        # Headers
        headers = {
            'X-API-KEY': serper_key,
            'Content-Type': 'application/json'
        }
        
        # Construct time-based query for date filtering
        # Serper uses different date format, we'll include dates in the query
        date_query = f"{query} after:{start_date} before:{end_date}"
        
        # Request payload
        payload = {
            "q": date_query,
            "gl": "us",  # Country
            "hl": "en",  # Language
            "num": 100   # Number of results
        }
        
        logger.info(f"🔍 Serper API: Searching for '{query}' from {start_date} to {end_date}")
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        
        # Check for errors
        if "error" in results:
            logger.error(f"❌ Serper API Error: {results['error']}")
            raise Exception(f"Serper API Error: {results['error']}")
        
        # Extract news results - Serper API uses 'news' key
        news_items = results.get("news", [])
        
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
        logger.info(f"✅ Serper API: Retrieved {len(news_results)} news items in {duration:.2f}s")
        
        return news_results
        
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        logger.error(f"❌ Serper API Request Error after {duration:.2f}s: {str(e)}")
        
        # Fallback to empty results rather than crashing
        logger.info("🔄 Returning empty results as fallback")
        return []
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Serper API Error after {duration:.2f}s: {str(e)}")
        
        # Fallback to empty results rather than crashing
        logger.info("🔄 Returning empty results as fallback")
        return []


def getNewsDataSerperAPIWithPagination(query: str, start_date: str, end_date: str, 
                                       max_results: int = 300, serper_key: str = None) -> List[Dict[str, Any]]:
    """
    Get news data using Serper API with pagination support for more results.
    
    Args:
        query: Search query string
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_results: Maximum number of results to fetch
        serper_key: Serper API key (if not provided, will use environment variable)
    
    Returns:
        List of dictionaries with news data
    """
    if not serper_key:
        serper_key = os.getenv("SERPER_API_KEY")
    
    if not serper_key:
        logger.error("❌ Serper API key not found. Please set SERPER_API_KEY environment variable.")
        raise ValueError("Serper API key not found. Please set SERPER_API_KEY environment variable.")
    
    all_news_results = []
    start_time = time.time()
    page = 1
    
    try:
        while len(all_news_results) < max_results:
            # Serper API endpoint
            url = "https://google.serper.dev/news"
            
            # Headers
            headers = {
                'X-API-KEY': serper_key,
                'Content-Type': 'application/json'
            }
            
            # Construct time-based query for date filtering
            date_query = f"{query} after:{start_date} before:{end_date}"
            
            # Request payload with pagination
            payload = {
                "q": date_query,
                "gl": "us",  # Country
                "hl": "en",  # Language
                "num": min(100, max_results - len(all_news_results)),  # Results per page
                "page": page  # Page number for pagination
            }
            
            logger.info(f"🔍 Serper API: Page {page} - Searching for '{query}' from {start_date} to {end_date}")
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            results = response.json()
            
            # Check for errors
            if "error" in results:
                logger.error(f"❌ Serper API Error: {results['error']}")
                break
            
            # Extract news results
            news_items = results.get("news", [])
            
            if not news_items:
                logger.info(f"📭 No more results found on page {page}")
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
        logger.info(f"✅ Serper API: Retrieved {len(all_news_results)} news items in {duration:.2f}s across {page - 1} pages")
        
        return all_news_results[:max_results]  # Ensure we don't exceed max_results
        
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        logger.error(f"❌ Serper API Request Error after {duration:.2f}s: {str(e)}")
        
        # Return whatever we managed to collect
        logger.info(f"🔄 Returning {len(all_news_results)} partial results as fallback")
        return all_news_results
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Serper API Error after {duration:.2f}s: {str(e)}")
        
        # Return whatever we managed to collect
        logger.info(f"🔄 Returning {len(all_news_results)} partial results as fallback")
        return all_news_results


# Legacy function names for backward compatibility
def getNewsDataSerpAPI(query: str, start_date: str, end_date: str, serpapi_key: str = None) -> List[Dict[str, Any]]:
    """
    Legacy function name - redirects to Serper API implementation.
    """
    # Map the old parameter name to new one
    serper_key = serpapi_key if serpapi_key else os.getenv("SERPER_API_KEY")
    return getNewsDataSerperAPI(query, start_date, end_date, serper_key)


def getNewsDataSerpAPIWithPagination(query: str, start_date: str, end_date: str, 
                                     max_results: int = 300, serpapi_key: str = None) -> List[Dict[str, Any]]:
    """
    Legacy function name - redirects to Serper API implementation.
    """
    # Map the old parameter name to new one
    serper_key = serpapi_key if serpapi_key else os.getenv("SERPER_API_KEY")
    return getNewsDataSerperAPIWithPagination(query, start_date, end_date, max_results, serper_key) 