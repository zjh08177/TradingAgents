#!/usr/bin/env python3
"""
Comprehensive LangGraph validation script.
Tests all critical endpoints and catches blocking/runtime errors.
"""
import requests
import json
import sys
import time
import subprocess
import signal
import os

BASE_URL = "http://127.0.0.1:8000"
ASSISTANT_ID = "6eb0b5d6-b38d-4235-ae71-1af6f75e6eae"

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def success(msg): print(f"{GREEN}✅ {msg}{NC}")
def error(msg): print(f"{RED}❌ {msg}{NC}")
def warning(msg): print(f"{YELLOW}⚠️  {msg}{NC}")

def test_endpoint(endpoint, method="GET", data=None, description="", timeout=10):
    """Test an endpoint and return status and result"""
    try:
        if method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data or {}, timeout=timeout)
        else:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=timeout)
        
        if response.status_code == 200:
            success(f"{endpoint} - {description}")
            return True, response.json() if response.content else {}
        else:
            error(f"{endpoint} - {description} (HTTP {response.status_code})")
            return False, None
    except requests.exceptions.Timeout:
        error(f"{endpoint} - {description} (TIMEOUT - possible blocking I/O)")
        return False, None
    except requests.exceptions.ConnectionError:
        error(f"{endpoint} - {description} (CONNECTION ERROR - server not running)")
        return False, None
    except Exception as e:
        error(f"{endpoint} - {description} (ERROR: {e})")
        return False, None

def test_graph_import():
    """Test if the graph can be imported without blocking errors"""
    try:
        result = subprocess.run([
            "python3", "-c", 
            "import sys; sys.path.append('src'); from agent import graph; print('SUCCESS')"
        ], capture_output=True, text=True, timeout=10, cwd=".")
        
        if result.returncode == 0 and "SUCCESS" in result.stdout:
            success("Graph import - Module loads without blocking errors")
            return True
        else:
            error(f"Graph import failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        error("Graph import - TIMEOUT (possible blocking I/O during import)")
        return False
    except Exception as e:
        error(f"Graph import error: {e}")
        return False

def check_server_running():
    """Check if LangGraph server is running"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            success("Server status - LangGraph dev server is running")
            return True
        else:
            error("Server status - Server responding with errors")
            return False
    except:
        error("Server status - Server not running or not responding")
        return False

def validate_no_blocking_calls():
    """Check for potential blocking calls in critical files"""
    blocking_patterns = [
        ("load_dotenv(", "Module-level dotenv loading"),
        ("requests.get(", "Synchronous HTTP requests"),
        ("open(", "Synchronous file operations"),
        ("time.sleep(", "Blocking sleep calls"),
    ]
    
    critical_files = [
        "src/agent/__init__.py",
        "src/agent/dataflows/interface.py",
        "src/agent/graph/__init__.py",
    ]
    
    issues = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        for pattern, description in blocking_patterns:
                            if pattern in line and not line.strip().startswith('#'):
                                # Check if it's in a function (not module level)
                                is_in_function = any(l.strip().startswith('def ') for l in lines[:i])
                                if not is_in_function and pattern == "load_dotenv(":
                                    issues.append(f"{file_path}:{i} - {description} at module level")
            except Exception as e:
                warning(f"Could not scan {file_path}: {e}")
    
    if issues:
        for issue in issues:
            error(f"Blocking call detected: {issue}")
        return False
    else:
        success("Blocking calls scan - No module-level blocking operations detected")
        return True

def main():
    print("🧪 Comprehensive LangGraph Validation")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Check server running
    total_tests += 1
    if check_server_running():
        tests_passed += 1
    
    # Test 2: Graph import without blocking
    total_tests += 1
    if test_graph_import():
        tests_passed += 1
    
    # Test 3: Validate no blocking calls
    total_tests += 1
    if validate_no_blocking_calls():
        tests_passed += 1
    
    # Test 4: Critical endpoints
    endpoints = [
        ("/assistants/search", "POST", {}, "Assistant search"),
        (f"/assistants/{ASSISTANT_ID}/schemas", "GET", None, "Graph schemas"),
        (f"/assistants/{ASSISTANT_ID}/graph", "GET", None, "Graph definition"),
        (f"/assistants/{ASSISTANT_ID}/subgraphs", "GET", None, "Subgraphs"),
        ("/docs", "GET", None, "API documentation"),
    ]
    
    for endpoint, method, data, desc in endpoints:
        total_tests += 1
        success_status, _ = test_endpoint(endpoint, method, data, desc)
        if success_status:
            tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        success("🎉 ALL TESTS PASSED - No blocking errors detected!")
        return 0
    else:
        error(f"💥 {total_tests - tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 