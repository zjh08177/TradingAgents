#!/usr/bin/env python3
"""
Studio Environment Test - Reproduce exact Studio loading conditions
"""

import os
import sys
import traceback
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_studio_environment():
    """Test environment conditions that match Studio exactly"""
    
    print("🔍 STUDIO ENVIRONMENT DIAGNOSTIC")
    print("=" * 50)
    
    # Environment info
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Test pandas import isolation
    print("\n📦 PANDAS IMPORT TEST")
    print("-" * 30)
    try:
        import pandas as pd
        print(f"✅ Pandas Version: {pd.__version__}")
        print(f"✅ Pandas Location: {pd.__file__}")
    except Exception as e:
        print(f"❌ Pandas Import Error: {e}")
        traceback.print_exc()
    
    # Test the exact import chain that fails in Studio
    print("\n🔗 STUDIO IMPORT CHAIN TEST")
    print("-" * 30)
    
    # Add src to path exactly like Studio
    src_path = str(Path(__file__).parent / "src")
    sys.path.insert(0, src_path)
    print(f"Added to path: {src_path}")
    
    try:
        # Step 1: Test agent module structure
        print("1. Testing agent module access...")
        import agent
        print("   ✅ Agent module imported")
        
        # Step 2: Test exact Studio importlib call
        print("2. Testing Studio importlib pattern...")
        import importlib
        trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
        print("   ✅ Trading graph module imported via importlib")
        
        # Step 3: Test graph factory function
        print("3. Testing graph factory function...")
        from langchain_core.runnables import RunnableConfig
        
        config = RunnableConfig(
            tags=[],
            metadata={},
            callbacks=None,
            recursion_limit=25,
            configurable={
                '__pregel_store': None,
                '__pregel_checkpointer': None
            }
        )
        
        # This is exactly what Studio calls - note it's a function call
        result = agent.graph(config)
        print("   ✅ Graph factory function executed successfully")
        print(f"   📊 Graph type: {type(result)}")
        
    except Exception as e:
        print(f"❌ STUDIO IMPORT CHAIN FAILED: {e}")
        print("📋 Full Traceback:")
        traceback.print_exc()
        return False
    
    print("\n🎉 ALL TESTS PASSED - STUDIO ENVIRONMENT WORKING")
    return True

def test_pandas_circular_import_conditions():
    """Test specific conditions that trigger pandas circular import"""
    
    print("\n🔄 PANDAS CIRCULAR IMPORT TESTS")
    print("-" * 40)
    
    # Test multiple pandas imports in the exact order Studio does
    try:
        print("Testing pandas import in Studio context...")
        
        # Clear any pandas modules to simulate fresh import
        pandas_modules = [mod for mod in sys.modules.keys() if 'pandas' in mod]
        print(f"Existing pandas modules: {pandas_modules}")
        
        # Import in the order Studio would do it
        # First via agent_utils.py
        print("1. Testing agent_utils pandas import...")
        from agent.utils.agent_utils import create_msg_delete  # This triggers pandas import
        print("   ✅ Agent utils import with pandas")
        
        # Then direct pandas access
        print("2. Testing direct pandas import...")
        import pandas as pd
        print(f"   ✅ Pandas version: {pd.__version__}")
        print(f"   ✅ Pandas location: {pd.__file__}")
        
    except Exception as e:
        print(f"❌ Pandas circular import detected: {e}")
        traceback.print_exc()
        return False
    
    return True

def simulate_studio_python_env():
    """Try to simulate the exact Python 3.11 environment that Studio uses"""
    
    print("\n🐍 PYTHON VERSION ANALYSIS")
    print("-" * 40)
    
    # Check if we can find Python 3.11 on the system
    import subprocess
    try:
        result = subprocess.run(['python3.11', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Found Python 3.11: {result.stdout.strip()}")
            
            # Test import with Python 3.11
            test_script = '''
import sys
sys.path.insert(0, "/Users/bytedance/Documents/TradingAgents/trading-graph-server/src")
try:
    import importlib
    trading_graph_module = importlib.import_module('.graph.trading_graph', package='agent')
    print("SUCCESS: Python 3.11 import chain works")
except Exception as e:
    print(f"FAILED: Python 3.11 import error: {e}")
    import traceback
    traceback.print_exc()
'''
            
            result = subprocess.run(['python3.11', '-c', test_script], 
                                 capture_output=True, text=True)
            print("Python 3.11 Test Result:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
                
        else:
            print("❌ Python 3.11 not found on system")
            
    except FileNotFoundError:
        print("❌ Python 3.11 not available")
    
    return True

if __name__ == "__main__":
    success1 = test_studio_environment()
    success2 = test_pandas_circular_import_conditions()
    success3 = simulate_studio_python_env()
    
    if success1 and success2 and success3:
        print("\n🎯 ENVIRONMENT TEST PASSED")
        sys.exit(0)
    else:
        print("\n💥 ENVIRONMENT TEST FAILED")
        sys.exit(1) 