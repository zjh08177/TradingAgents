#!/usr/bin/env python
"""
Run all TradingAgents tests and provide comprehensive summary
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import json


class TestRunner:
    """Run and track all tests"""
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.log_file = f"test_results/all_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        Path("test_results").mkdir(exist_ok=True)
        
    def log(self, message):
        """Log message to console and file"""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(message + '\n')
    
    def run_test(self, test_name, test_file, description):
        """Run a single test file"""
        self.log(f"\n{'='*80}")
        self.log(f"Running: {test_name}")
        self.log(f"Description: {description}")
        self.log(f"File: {test_file}")
        self.log("="*80)
        
        start_time = time.time()
        
        try:
            # Run the test
            result = subprocess.run(
                ['python3', test_file],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Log output
            if result.stdout:
                self.log("\nSTDOUT:")
                self.log(result.stdout)
            
            if result.stderr:
                self.log("\nSTDERR:")
                self.log(result.stderr)
            
            # Track result
            self.results.append({
                'test': test_name,
                'file': test_file,
                'success': success,
                'duration': duration,
                'return_code': result.returncode
            })
            
            status = "✅ PASSED" if success else "❌ FAILED"
            self.log(f"\n{status} - {test_name} ({duration:.2f}s)")
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log(f"\n⏱️ TIMEOUT - {test_name} exceeded 5 minutes")
            self.results.append({
                'test': test_name,
                'file': test_file,
                'success': False,
                'duration': duration,
                'error': 'Timeout'
            })
        except Exception as e:
            duration = time.time() - start_time
            self.log(f"\n💥 ERROR - {test_name}: {str(e)}")
            self.results.append({
                'test': test_name,
                'file': test_file,
                'success': False,
                'duration': duration,
                'error': str(e)
            })
    
    def print_summary(self):
        """Print test summary"""
        total_duration = time.time() - self.start_time
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        self.log("\n" + "="*80)
        self.log("TEST SUMMARY")
        self.log("="*80)
        self.log(f"\nTotal Tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")
        self.log(f"Total Duration: {total_duration:.2f}s")
        
        self.log("\nIndividual Results:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            self.log(f"  {status} {result['test']} ({result['duration']:.2f}s)")
            if 'error' in result:
                self.log(f"     Error: {result['error']}")
        
        # Save summary to JSON
        summary_file = Path("test_results/test_summary.json")
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': total,
                'passed': passed,
                'failed': total - passed,
                'total_duration': total_duration,
                'results': self.results
            }, f, indent=2)
        
        self.log(f"\n📁 Log saved to: {self.log_file}")
        self.log(f"📊 Summary saved to: {summary_file}")
        
        return passed == total


def main():
    """Run all tests"""
    runner = TestRunner()
    
    runner.log("🚀 TradingAgents Comprehensive Test Suite")
    runner.log(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define tests to run
    tests = [
        {
            'name': 'Main.py Comprehensive Test',
            'file': 'test_main_comprehensive.py',
            'description': 'Tests main.py with continuous logging and parallel execution verification'
        },
        {
            'name': 'API Comprehensive Test',
            'file': 'test_api_comprehensive.py',
            'description': 'Tests FastAPI endpoints, streaming, and concurrent requests'
        },
        {
            'name': 'Parallel Execution Test',
            'file': 'test_parallel_execution.py',
            'description': 'Specifically verifies agents run in parallel when expected'
        },
        {
            'name': 'Basic API Test',
            'file': 'test_api.py',
            'description': 'Basic API endpoint tests'
        }
    ]
    
    # Check which test files exist
    runner.log("\n📂 Checking for test files...")
    available_tests = []
    
    for test in tests:
        if Path(test['file']).exists():
            runner.log(f"  ✅ Found: {test['file']}")
            available_tests.append(test)
        else:
            runner.log(f"  ❌ Missing: {test['file']}")
    
    if not available_tests:
        runner.log("\n❌ No test files found!")
        return False
    
    # Run available tests
    runner.log(f"\n🧪 Running {len(available_tests)} tests...")
    
    for test in available_tests:
        runner.run_test(test['name'], test['file'], test['description'])
    
    # Print summary
    all_passed = runner.print_summary()
    
    if all_passed:
        runner.log("\n✅ All tests passed!")
        return True
    else:
        runner.log("\n❌ Some tests failed. Please check the logs.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)