import json
import httpx
import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def getNewsDataSerpAPI(query: str, start_date: str, end_date: str, serpapi_key: str = None) -> List[Dict[str, Any]]:
    """
    Get news data from SerpAPI using async httpx.
    """
    if not serpapi_key:
        logger.error("❌ SerpAPI key is required")
        return []

    all_news_results = []
    page = 1
    
    logger.info(f"🔍 Starting SerpAPI search for: {query}")
    logger.info(f"📅 Date range: {start_date} to {end_date}")
    
    try:
        while len(all_news_results) < 300:  # Max results limit
            logger.info(f"📄 Fetching page {page}...")
            
            # SerpAPI parameters
            params = {
                "engine": "google",
                "q": f"{query} after:{start_date} before:{end_date}",
                "tbm": "nws",
                "tbs": f"cdr:1,cd_min:{start_date},cd_max:{end_date}",
                "api_key": serpapi_key,
                "start": (page - 1) * 10,
                "num": 10,
                "hl": "en",
                "gl": "us"
            }
            
            url = "https://serpapi.com/search"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()
                
            data = response.json()
            
            # Check for errors
            if "error" in data:
                logger.error(f"❌ SerpAPI Error: {data['error']}")
                break
            
            # Extract news results
            news_results = data.get("news_results", [])
            
            logger.info(f"📄 Page {page}: Found {len(news_results)} items")
            
            if not news_results:
                logger.info(f"📄 No more results found at page {page}")
                break
            
            # Process news items
            for item in news_results:
                try:
                    news_result = {
                        "link": item.get("link", ""),
                        "title": item.get("title", "No title"),
                        "snippet": item.get("snippet", "No snippet"),
                        "date": item.get("date", "No date"),
                        "source": item.get("source", "Unknown source"),
                    }
                    all_news_results.append(news_result)
                    
                    if len(all_news_results) >= 300:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing news item: {e}")
                    continue
            
            page += 1
            
            # Add small delay between requests to be respectful
            await asyncio.sleep(0.5)
        
        logger.info(f"✅ SerpAPI: Retrieved {len(all_news_results)} news items across {page - 1} pages")
        
        return all_news_results
        
    except httpx.HTTPError as e:
        logger.error(f"❌ SerpAPI HTTP Error: {str(e)}")
        
        # Return whatever we managed to collect
        logger.info(f"🔄 Returning {len(all_news_results)} partial results as fallback")
        return all_news_results
        
    except Exception as e:
        logger.error(f"❌ SerpAPI Error: {str(e)}")
        
        # Return whatever we managed to collect
        logger.info(f"🔄 Returning {len(all_news_results)} partial results as fallback")
        return all_news_results 