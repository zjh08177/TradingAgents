#!/usr/bin/env python3
"""
Debug LangGraph Module Loading Issue
=====================================
This script debugs why LangGraph isn't picking up new code changes.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
import json

def check_langgraph_process():
    """Check how LangGraph is running."""
    print("\n🔍 CHECKING LANGGRAPH PROCESS")
    print("="*60)
    
    # Check running processes
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    langgraph_processes = [line for line in result.stdout.split('\n') if 'langgraph' in line.lower() and 'grep' not in line]
    
    if langgraph_processes:
        print("✅ LangGraph process found:")
        for proc in langgraph_processes:
            print(f"  {proc[:150]}...")
            
        # Extract PID
        for proc in langgraph_processes:
            parts = proc.split()
            if len(parts) > 1:
                pid = parts[1]
                print(f"\n📊 Process ID: {pid}")
                
                # Check open files
                try:
                    lsof_result = subprocess.run(['lsof', '-p', pid], capture_output=True, text=True)
                    python_files = [line for line in lsof_result.stdout.split('\n') if '.py' in line]
                    print(f"📁 Python files loaded by process {pid}:")
                    for pf in python_files[:5]:  # Show first 5
                        print(f"    {pf.split()[-1] if pf.split() else pf}")
                except:
                    pass
    else:
        print("❌ No LangGraph process found")

def check_package_installation():
    """Check how the agent package is installed."""
    print("\n📦 CHECKING PACKAGE INSTALLATION")
    print("="*60)
    
    # Check pip list
    result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
    agent_line = [line for line in result.stdout.split('\n') if line.startswith('agent ')]
    
    if agent_line:
        print(f"✅ Agent package installed: {agent_line[0]}")
        
        # Check installation location
        result = subprocess.run(['pip', 'show', 'agent'], capture_output=True, text=True)
        print("\n📍 Installation details:")
        for line in result.stdout.split('\n'):
            if line.startswith('Location:') or line.startswith('Version:'):
                print(f"  {line}")
    else:
        print("❌ Agent package not found in pip list")
    
    # Check if installed in editable mode
    result = subprocess.run(['pip', 'list', '--editable'], capture_output=True, text=True)
    if 'agent' in result.stdout:
        print("✅ Package installed in EDITABLE mode (good for development)")
    else:
        print("⚠️  Package NOT in editable mode - changes may not be reflected!")
        print("   Fix with: pip install -e .")

def check_module_locations():
    """Check where Python is loading modules from."""
    print("\n📂 CHECKING MODULE LOCATIONS")
    print("="*60)
    
    # Try to import and check location
    try:
        import src.agent.analysts.news_analyst_ultra_fast as news_module
        print(f"✅ news_analyst_ultra_fast loaded from:")
        print(f"   {news_module.__file__}")
        
        # Check if it has the token limits
        with open(news_module.__file__, 'r') as f:
            content = f.read()
            if 'MAX_ARTICLES = 15' in content:
                print("   ✅ Token limits FOUND in loaded module")
            else:
                print("   ❌ Token limits MISSING in loaded module")
                
            if 'RUNTIME VERIFICATION' in content:
                print("   ✅ Runtime verification FOUND in loaded module")
            else:
                print("   ❌ Runtime verification MISSING in loaded module")
    except Exception as e:
        print(f"❌ Could not import news_analyst_ultra_fast: {e}")

def check_langgraph_config():
    """Check LangGraph configuration."""
    print("\n⚙️ CHECKING LANGGRAPH CONFIGURATION")
    print("="*60)
    
    # Check for langgraph.json
    if Path('langgraph.json').exists():
        print("✅ langgraph.json found")
        with open('langgraph.json', 'r') as f:
            config = json.load(f)
            print(f"   Graph path: {config.get('graphs', {}).get('agent', {}).get('path', 'N/A')}")
    else:
        print("❌ langgraph.json not found")
    
    # Check for .langgraph directory
    if Path('.langgraph').exists():
        print("✅ .langgraph directory found")
        # Check for cached files
        cache_files = list(Path('.langgraph').rglob('*.py'))
        if cache_files:
            print(f"   ⚠️  Found {len(cache_files)} Python files in .langgraph cache")
            print("   This could be causing stale code issues!")
    else:
        print("❌ .langgraph directory not found")

def check_python_path():
    """Check Python path and import order."""
    print("\n🐍 CHECKING PYTHON PATH")
    print("="*60)
    
    print("Python executable:", sys.executable)
    print("\nPython path (import search order):")
    for i, path in enumerate(sys.path[:10], 1):  # Show first 10
        print(f"  {i}. {path}")
    
    # Check if current directory is in path
    cwd = os.getcwd()
    if cwd in sys.path:
        print(f"\n✅ Current directory in Python path: {cwd}")
    else:
        print(f"\n⚠️  Current directory NOT in Python path: {cwd}")
        print("   This could cause import issues!")

def suggest_fixes():
    """Suggest fixes based on findings."""
    print("\n🔧 SUGGESTED FIXES")
    print("="*60)
    
    print("""
1. **Clear ALL caches**:
   ```bash
   # Stop server
   pkill -f langgraph
   
   # Clear Python cache
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   
   # Clear LangGraph cache
   rm -rf .langgraph
   
   # Clear pip cache
   pip cache purge
   ```

2. **Reinstall in editable mode**:
   ```bash
   # Uninstall first
   pip uninstall agent -y
   
   # Install in editable mode
   pip install -e .
   ```

3. **Force module reload in LangGraph**:
   ```bash
   # Add to restart script
   export PYTHONDONTWRITEBYTECODE=1
   export PYTHONUNBUFFERED=1
   ```

4. **Use explicit module invalidation**:
   ```python
   # Add to graph initialization
   import importlib
   import sys
   
   # Remove cached modules
   for module in list(sys.modules.keys()):
       if module.startswith('src.agent'):
           del sys.modules[module]
   ```

5. **Restart with full cleanup**:
   ```bash
   ./restart_server.sh
   ```
   
6. **Verify with runtime logs**:
   ```bash
   # After restart, test with
   python3 debug_local.sh AAPL 2>&1 | grep "RUNTIME VERIFICATION"
   ```
""")

if __name__ == "__main__":
    print("🔍 DEBUGGING LANGGRAPH MODULE LOADING ISSUE")
    print("="*60)
    
    check_langgraph_process()
    check_package_installation()
    check_module_locations()
    check_langgraph_config()
    check_python_path()
    suggest_fixes()
    
    print("\n" + "="*60)
    print("✅ Debug analysis complete")
    print("="*60)