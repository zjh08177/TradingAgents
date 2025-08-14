import httpx
import asyncio
import json
import logging
from typing import List, Dict, Any
from ..utils.debug_logging import log_data_fetch
import time

logger = logging.getLogger(__name__)


async def getNewsDataSerperAPI(query_or_company: str, start_date: str = None, end_date: str = None, serper_key: str = None, config: dict = None) -> List[Dict[str, Any]]:
    """
    Fetch news data from Serper API - backward compatible interface
    
    Args:
        query_or_company: Company name or search query
        start_date: Start date for news search (optional, for backward compatibility)
        end_date: End date for news search (optional, for backward compatibility)  
        serper_key: API key (optional, for backward compatibility)
        config: Configuration dictionary containing API keys (new interface)
        
    Returns:
        List of news articles
    """
    start_time = time.time()
    
    try:
        # Handle both old and new interface styles
        if config is not None:
            # New interface: getNewsDataSerperAPI(company, config)
            api_key = config.get("serper_api_key") or config.get("serper_key")
            company = query_or_company
            search_query = f"{company} stock news"
        else:
            # Old interface: getNewsDataSerperAPI(query, start_date, end_date, serper_key)
            api_key = serper_key
            search_query = query_or_company
            if start_date and end_date:
                search_query = f"{query_or_company} after:{start_date} before:{end_date}"
                
        if not api_key:
            logger.warning("No Serper API key provided")
            return []

        url = "https://google.serper.dev/news"
        
        payload = json.dumps({
            "q": search_query,
            "gl": "us",
            "hl": "en",
            "num": 10
        })
        
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=payload, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            news_articles = data.get("news", [])
            
            # Log the data fetch operation
            execution_time = time.time() - start_time
            log_data_fetch("serper_api", news_articles, logger)
            
            return news_articles
            
    except httpx.HTTPError as e:
        execution_time = time.time() - start_time
        log_data_fetch("serper_api", [], logger)
        logger.error(f"HTTP error occurred: {e}")
        return []
    except Exception as e:
        execution_time = time.time() - start_time
        log_data_fetch("serper_api", [], logger)
        logger.error(f"An error occurred: {e}")
        return []


async def getNewsDataSerperAPIWithPagination(query_or_company: str, start_date: str = None, end_date: str = None, max_pages: int = 3, serper_key: str = None, config: dict = None) -> List[Dict[str, Any]]:
    """
    Fetch news data from Serper API with pagination - backward compatible interface
    
    Args:
        query_or_company: Company name or search query
        start_date: Start date for news search (optional, for backward compatibility)
        end_date: End date for news search (optional, for backward compatibility)
        max_pages: Maximum number of pages to fetch
        serper_key: API key (optional, for backward compatibility)
        config: Configuration dictionary containing API keys (new interface)
        
    Returns:
        List of news articles from all pages
    """
    start_time = time.time()
    all_articles = []
    
    try:
        # Handle both old and new interface styles
        if config is not None:
            # New interface
            api_key = config.get("serper_api_key") or config.get("serper_key")
            company = query_or_company
            search_query = f"{company} stock news"
        else:
            # Old interface
            api_key = serper_key
            search_query = query_or_company
            if start_date and end_date:
                search_query = f"{query_or_company} after:{start_date} before:{end_date}"
                
        if not api_key:
            logger.warning("No Serper API key provided")
            return []

        url = "https://google.serper.dev/news"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            for page in range(max_pages):
                payload = json.dumps({
                    "q": search_query,
                    "gl": "us", 
                    "hl": "en",
                    "num": 10,
                    "start": page * 10
                })
                
                response = await client.post(url, headers=headers, data=payload, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                news_articles = data.get("news", [])
                
                if not news_articles:
                    break
                    
                all_articles.extend(news_articles)
                
                # Add delay between requests
                if page < max_pages - 1:
                    await asyncio.sleep(1)
            
            # Log the paginated data fetch operation
            execution_time = time.time() - start_time
            log_data_fetch("serper_api_paginated", all_articles, logger)
            
            return all_articles
            
    except httpx.HTTPError as e:
        execution_time = time.time() - start_time
        log_data_fetch("serper_api_paginated", all_articles, logger)
        logger.error(f"HTTP error occurred: {e}")
        return all_articles
    except Exception as e:
        execution_time = time.time() - start_time
        log_data_fetch("serper_api_paginated", all_articles, logger)
        logger.error(f"An error occurred: {e}")
        return all_articles 