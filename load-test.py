#!/usr/bin/env python3
"""
LangGraph Load Testing Script for 5000 Concurrent Users
Based on production deployment verification
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import argparse
import statistics

@dataclass
class TestResult:
    status_code: int
    response_time: float
    success: bool
    error: str = ""
    user_id: int = 0

class LangGraphLoadTester:
    def __init__(self, base_url: str, max_concurrent: int = 5000):
        self.base_url = base_url.rstrip('/')
        self.max_concurrent = max_concurrent
        self.results: List[TestResult] = []
        
    async def health_check(self) -> bool:
        """Verify server is responding before load test"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Server healthy: {data}")
                        return True
                    else:
                        print(f"❌ Server unhealthy: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def single_analysis_request(self, session: aiohttp.ClientSession, user_id: int, ticker: str = "TSLA") -> TestResult:
        """Single trading analysis request"""
        start_time = time.time()
        
        try:
            # Use LangGraph streaming endpoint
            payload = {
                "input": {
                    "ticker": ticker,
                    "analysis_date": "2024-12-20"
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            
            async with session.post(
                f"{self.base_url}/threads",
                json={},
                timeout=timeout
            ) as thread_response:
                
                if thread_response.status != 201:
                    response_time = time.time() - start_time
                    return TestResult(
                        status_code=thread_response.status,
                        response_time=response_time,
                        success=False,
                        error=f"Failed to create thread: {thread_response.status}",
                        user_id=user_id
                    )
                
                thread_data = await thread_response.json()
                thread_id = thread_data["thread_id"]
            
            # Start analysis run
            async with session.post(
                f"{self.base_url}/threads/{thread_id}/runs",
                json={
                    "assistant_id": "trading_agent",
                    "input": payload["input"]
                },
                timeout=timeout
            ) as run_response:
                
                response_time = time.time() - start_time
                
                if run_response.status in [200, 201]:
                    run_data = await run_response.json()
                    return TestResult(
                        status_code=run_response.status,
                        response_time=response_time,
                        success=True,
                        user_id=user_id
                    )
                else:
                    error_text = await run_response.text()
                    return TestResult(
                        status_code=run_response.status,
                        response_time=response_time,
                        success=False,
                        error=f"Run failed: {error_text}",
                        user_id=user_id
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return TestResult(
                status_code=408,
                response_time=response_time,
                success=False,
                error="Request timeout",
                user_id=user_id
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                status_code=500,
                response_time=response_time,
                success=False,
                error=str(e),
                user_id=user_id
            )
    
    async def run_concurrent_test(self, num_users: int, ramp_up_seconds: int = 60):
        """Run concurrent load test with gradual ramp-up"""
        print(f"🚀 Starting load test: {num_users} concurrent users")
        print(f"📈 Ramp-up period: {ramp_up_seconds} seconds")
        
        connector = aiohttp.TCPConnector(
            limit=num_users * 2,  # Allow more connections than users
            limit_per_host=num_users * 2,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=300)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            # Create tasks with staggered start times
            tasks = []
            delay_per_user = ramp_up_seconds / num_users if num_users > 0 else 0
            
            for user_id in range(num_users):
                # Stagger requests to simulate realistic ramp-up
                delay = user_id * delay_per_user
                task = asyncio.create_task(
                    self._delayed_request(session, user_id, delay)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            print(f"⏳ Waiting for {len(tasks)} requests to complete...")
            start_time = time.time()
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            print(f"✅ All requests completed in {total_time:.2f} seconds")
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.results.append(TestResult(
                        status_code=500,
                        response_time=total_time,
                        success=False,
                        error=str(result),
                        user_id=i
                    ))
                else:
                    self.results.append(result)
    
    async def _delayed_request(self, session: aiohttp.ClientSession, user_id: int, delay: float) -> TestResult:
        """Execute request after specified delay"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        return await self.single_analysis_request(session, user_id)
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze test results and generate report"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        
        response_times = [r.response_time for r in self.results]
        
        # Status code breakdown
        status_codes = {}
        for result in self.results:
            code = result.status_code
            status_codes[code] = status_codes.get(code, 0) + 1
        
        # Error breakdown
        errors = {}
        for result in self.results:
            if not result.success and result.error:
                errors[result.error] = errors.get(result.error, 0) + 1
        
        analysis = {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests) * 100,
            },
            "performance": {
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99),
            },
            "status_codes": status_codes,
            "errors": errors
        }
        
        return analysis
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of response times"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_report(self, analysis: Dict[str, Any]):
        """Print detailed test report"""
        print("\n" + "="*60)
        print("🧪 LANGGRAPH LOAD TEST RESULTS")
        print("="*60)
        
        summary = analysis["summary"]
        performance = analysis["performance"]
        
        print(f"📊 SUMMARY:")
        print(f"   Total Requests: {summary['total_requests']:,}")
        print(f"   Successful: {summary['successful_requests']:,}")
        print(f"   Failed: {summary['failed_requests']:,}")
        print(f"   Success Rate: {summary['success_rate']:.2f}%")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Average Response Time: {performance['avg_response_time']:.2f}s")
        print(f"   Median Response Time: {performance['median_response_time']:.2f}s")
        print(f"   95th Percentile: {performance['p95_response_time']:.2f}s")
        print(f"   99th Percentile: {performance['p99_response_time']:.2f}s")
        print(f"   Min Response Time: {performance['min_response_time']:.2f}s")
        print(f"   Max Response Time: {performance['max_response_time']:.2f}s")
        
        print(f"\n📈 STATUS CODES:")
        for code, count in analysis["status_codes"].items():
            print(f"   {code}: {count:,} requests")
        
        if analysis["errors"]:
            print(f"\n❌ ERRORS:")
            for error, count in analysis["errors"].items():
                print(f"   {error}: {count:,} occurrences")
        
        # Capacity assessment
        print(f"\n🎯 CAPACITY ASSESSMENT:")
        success_rate = summary['success_rate']
        avg_response_time = performance['avg_response_time']
        
        if success_rate >= 95 and avg_response_time <= 180:  # 3 minutes
            print("   ✅ EXCELLENT - System can handle this load")
        elif success_rate >= 90 and avg_response_time <= 300:  # 5 minutes
            print("   ⚠️  ACCEPTABLE - System handling load with some stress")
        else:
            print("   ❌ OVERLOADED - System cannot handle this load")
        
        print("="*60)

async def main():
    parser = argparse.ArgumentParser(description="LangGraph Load Testing")
    parser.add_argument("--url", required=True, help="LangGraph server URL")
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    parser.add_argument("--ramp-up", type=int, default=60, help="Ramp-up time in seconds")
    parser.add_argument("--max-users", type=int, default=5000, help="Maximum users for capacity test")
    
    args = parser.parse_args()
    
    tester = LangGraphLoadTester(args.url, args.max_users)
    
    # Health check first
    if not await tester.health_check():
        print("❌ Server health check failed. Aborting load test.")
        return
    
    # Run progressive load tests
    test_levels = [10, 50, 100, 250, 500, 1000, 2000, args.users]
    if args.users not in test_levels:
        test_levels.append(args.users)
    
    for num_users in sorted(set(test_levels)):
        if num_users > args.users:
            break
            
        print(f"\n🧪 Testing with {num_users} concurrent users...")
        
        # Reset results for each test
        tester.results = []
        
        # Run test
        await tester.run_concurrent_test(num_users, args.ramp_up)
        
        # Analyze and report
        analysis = tester.analyze_results()
        tester.print_report(analysis)
        
        # Check if system is struggling
        if analysis["summary"]["success_rate"] < 80:
            print(f"⚠️  System struggling at {num_users} users. Consider this the capacity limit.")
            break
        
        # Brief pause between tests
        if num_users < args.users:
            print("😴 Cooling down for 30 seconds...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main()) 