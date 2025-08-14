#!/usr/bin/env python3
"""
Market Analyst External API Debugging Tool

This script tests various external API access methods to debug why market data
fetching fails in the LangGraph environment.

Usage:
    python debug_external_apis.py AAPL
    python debug_external_apis.py --all-methods TSLA
    python debug_external_apis.py --test-connectivity
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExternalAPITester:
    """Test various external API access methods"""
    
    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker
        self.results = {}
        
    async def test_basic_connectivity(self) -> Dict[str, Any]:
        """Test basic internet connectivity"""
        logger.info("🔍 Testing basic connectivity...")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://httpbin.org/get")
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "headers": dict(response.headers)
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_httpx_yahoo(self) -> Dict[str, Any]:
        """Test Yahoo Finance with httpx (current implementation)"""
        logger.info("📊 Testing Yahoo Finance with httpx...")
        
        try:
            import httpx
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}"
            params = {'range': '5d', 'interval': '1d'}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response_time = time.time() - start_time
                
                data = response.json()
                
                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "data_size": len(response.text),
                    "has_chart": "chart" in data,
                    "has_result": data.get("chart", {}).get("result", []) != [],
                    "sample_data": str(data)[:200] + "..."
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_aiohttp_yahoo(self) -> Dict[str, Any]:
        """Test Yahoo Finance with aiohttp"""
        logger.info("📊 Testing Yahoo Finance with aiohttp...")
        
        try:
            import aiohttp
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}"
            params = {'range': '5d', 'interval': '1d'}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            start_time = time.time()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(url, params=params, headers=headers) as response:
                    response_time = time.time() - start_time
                    text = await response.text()
                    data = json.loads(text)
                    
                    return {
                        "status": "success",
                        "status_code": response.status,
                        "response_time": response_time,
                        "data_size": len(text),
                        "has_chart": "chart" in data,
                        "has_result": data.get("chart", {}).get("result", []) != [],
                        "sample_data": str(data)[:200] + "..."
                    }
        except Exception as e:
            return {
                "status": "failed", 
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def test_alternative_apis(self) -> Dict[str, Dict[str, Any]]:
        """Test alternative financial APIs"""
        logger.info("🔄 Testing alternative financial APIs...")
        
        apis = {
            "finnhub": {
                "url": f"https://finnhub.io/api/v1/quote?symbol={self.ticker}&token=demo",
                "headers": {}
            },
            "alpha_vantage": {
                "url": f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={self.ticker}&apikey=demo",
                "headers": {}
            },
            "yahoo_alternative": {
                "url": f"https://finance.yahoo.com/quote/{self.ticker}",
                "headers": {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            }
        }
        
        results = {}
        
        for api_name, config in apis.items():
            try:
                import httpx
                start_time = time.time()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(config["url"], headers=config["headers"])
                    response_time = time.time() - start_time
                    
                    results[api_name] = {
                        "status": "success",
                        "status_code": response.status_code,
                        "response_time": response_time,
                        "data_size": len(response.text),
                        "content_type": response.headers.get("content-type", ""),
                        "sample_data": response.text[:200] + "..."
                    }
            except Exception as e:
                results[api_name] = {
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        return results
    
    async def test_environment_detection(self) -> Dict[str, Any]:
        """Test LangGraph environment detection"""
        logger.info("🔍 Testing environment detection...")
        
        import os
        import sys
        
        return {
            "LANGGRAPH_ENV": os.getenv('LANGGRAPH_ENV'),
            "IS_LANGGRAPH_DEV": os.getenv('IS_LANGGRAPH_DEV'),
            "langgraph_in_modules": 'langgraph' in str(sys.modules.keys()),
            "python_version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info(f"🚀 Starting comprehensive API testing for {self.ticker}")
        start_time = datetime.now()
        
        results = {
            "ticker": self.ticker,
            "test_start": start_time.isoformat(),
            "environment": await self.test_environment_detection(),
            "tests": {}
        }
        
        # Test basic connectivity
        results["tests"]["basic_connectivity"] = await self.test_basic_connectivity()
        
        # Test Yahoo Finance with different methods
        results["tests"]["httpx_yahoo"] = await self.test_httpx_yahoo()
        results["tests"]["aiohttp_yahoo"] = await self.test_aiohttp_yahoo()
        
        # Test alternative APIs
        results["tests"]["alternative_apis"] = await self.test_alternative_apis()
        
        end_time = datetime.now()
        results["test_end"] = end_time.isoformat()
        results["total_duration"] = (end_time - start_time).total_seconds()
        
        return results
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print("\n" + "="*80)
        print(f"🔍 EXTERNAL API TEST RESULTS FOR {results['ticker']}")
        print("="*80)
        
        # Environment info
        print("\n🌍 ENVIRONMENT:")
        env = results["environment"]
        for key, value in env.items():
            print(f"  {key}: {value}")
        
        # Test results
        print("\n📊 TEST RESULTS:")
        tests = results["tests"]
        
        # Basic connectivity
        basic = tests["basic_connectivity"]
        status = "✅" if basic["status"] == "success" else "❌"
        print(f"  {status} Basic Connectivity: {basic['status']}")
        if basic["status"] == "success":
            print(f"     Response time: {basic['response_time']:.2f}s")
        else:
            print(f"     Error: {basic.get('error', 'Unknown')}")
        
        # Yahoo Finance tests
        for method in ["httpx_yahoo", "aiohttp_yahoo"]:
            if method in tests:
                test = tests[method]
                status = "✅" if test["status"] == "success" else "❌"
                method_name = method.replace("_yahoo", "").upper()
                print(f"  {status} Yahoo Finance ({method_name}): {test['status']}")
                if test["status"] == "success":
                    print(f"     Response time: {test['response_time']:.2f}s")
                    print(f"     Data size: {test['data_size']} bytes")
                    print(f"     Has market data: {test.get('has_result', False)}")
                else:
                    print(f"     Error: {test.get('error', 'Unknown')}")
        
        # Alternative APIs
        if "alternative_apis" in tests:
            print(f"\n🔄 ALTERNATIVE APIs:")
            for api_name, api_result in tests["alternative_apis"].items():
                status = "✅" if api_result["status"] == "success" else "❌"
                print(f"  {status} {api_name.title()}: {api_result['status']}")
                if api_result["status"] == "success":
                    print(f"     Response time: {api_result['response_time']:.2f}s")
                    print(f"     Status code: {api_result['status_code']}")
                else:
                    print(f"     Error: {api_result.get('error', 'Unknown')}")
        
        print(f"\n⏱️ Total test duration: {results['total_duration']:.2f}s")
        print("="*80)

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug external API access for market analyst")
    parser.add_argument("ticker", nargs="?", default="AAPL", help="Stock ticker to test")
    parser.add_argument("--all-methods", action="store_true", help="Test all HTTP methods")
    parser.add_argument("--test-connectivity", action="store_true", help="Test basic connectivity only")
    parser.add_argument("--save-results", help="Save results to JSON file")
    
    args = parser.parse_args()
    
    tester = ExternalAPITester(args.ticker)
    
    if args.test_connectivity:
        result = await tester.test_basic_connectivity()
        print(json.dumps(result, indent=2))
    else:
        results = await tester.run_all_tests()
        tester.print_results(results)
        
        if args.save_results:
            with open(args.save_results, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to {args.save_results}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)