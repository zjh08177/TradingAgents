#!/usr/bin/env python3
"""
Enable Ultra-Fast Fundamentals Collector in Trading Graph
This script patches the graph setup to use the high-performance fundamentals collector.
"""

import os
import sys
import shutil
from pathlib import Path

def patch_graph_files():
    """Patch graph setup files to use ultra-fast fundamentals analyst."""
    
    print("🚀 Enabling Ultra-Fast Fundamentals Collector...")
    
    # Files to patch
    files_to_patch = [
        "src/agent/graph/setup.py",
        "src/agent/graph/optimized_setup.py",
        "src/agent/graph/enhanced_optimized_setup.py"
    ]
    
    patches_applied = 0
    
    for file_path in files_to_patch:
        if not os.path.exists(file_path):
            print(f"⚠️  Skipping {file_path} - file not found")
            continue
        
        # Create backup
        backup_path = f"{file_path}.backup_original"
        if not os.path.exists(backup_path):
            shutil.copy(file_path, backup_path)
            print(f"📦 Created backup: {backup_path}")
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if "fundamentals_analyst_ultra_fast" in content:
            print(f"✅ {file_path} already patched")
            patches_applied += 1
            continue
        
        # Apply patch - replace import
        original_import = "from ..analysts.fundamentals_analyst import create_fundamentals_analyst"
        new_import = """# Ultra-fast implementation enabled
from ..analysts.fundamentals_analyst_ultra_fast import create_fundamentals_analyst_ultra_fast as create_fundamentals_analyst
# Original (disabled): from ..analysts.fundamentals_analyst import create_fundamentals_analyst"""
        
        if original_import in content:
            content = content.replace(original_import, new_import)
            
            # Write patched file
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Patched {file_path}")
            patches_applied += 1
        else:
            print(f"⚠️  Could not patch {file_path} - import not found")
    
    # Also patch the enhanced parallel analysts file
    enhanced_file = "src/agent/graph/nodes/enhanced_parallel_analysts.py"
    if os.path.exists(enhanced_file):
        with open(enhanced_file, 'r') as f:
            content = f.read()
        
        if "fundamentals_analyst_ultra_fast" not in content:
            # Add import at the top
            import_section = """from ...interfaces import IAnalystToolkit, ILLMProvider"""
            new_import = """from ...interfaces import IAnalystToolkit, ILLMProvider
from ...analysts.fundamentals_analyst_ultra_fast import create_fundamentals_analyst_ultra_fast"""
            
            content = content.replace(import_section, new_import)
            
            # Replace the create function
            old_func = '''async def create_fundamentals_analyst_node(llm: ILLMProvider, toolkit: IAnalystToolkit) -> Callable:
    """Create enhanced fundamentals analyst node with MANDATORY tool usage"""'''
            
            new_func = '''async def create_fundamentals_analyst_node(llm: ILLMProvider, toolkit: IAnalystToolkit) -> Callable:
    """Create ultra-fast fundamentals analyst node (bypasses LLM for direct API)"""
    # Use ultra-fast implementation
    return create_fundamentals_analyst_ultra_fast(llm, toolkit)
    
async def create_fundamentals_analyst_node_original(llm: ILLMProvider, toolkit: IAnalystToolkit) -> Callable:
    """Original enhanced fundamentals analyst node with MANDATORY tool usage (disabled)"""'''
            
            if old_func in content:
                content = content.replace(old_func, new_func)
                
                # Create backup
                backup_path = f"{enhanced_file}.backup_original"
                if not os.path.exists(backup_path):
                    shutil.copy(enhanced_file, backup_path)
                
                with open(enhanced_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Patched {enhanced_file}")
                patches_applied += 1
    
    print(f"\n📊 Summary: {patches_applied} files patched")
    
    # Create a flag file to indicate ultra-fast mode is enabled
    flag_file = ".ultra_fast_fundamentals_enabled"
    with open(flag_file, 'w') as f:
        f.write("Ultra-Fast Fundamentals Collector is enabled\n")
    
    print(f"✅ Created flag file: {flag_file}")
    
    return patches_applied > 0


def verify_installation():
    """Verify that the ultra-fast collector is properly installed."""
    
    print("\n🔍 Verifying installation...")
    
    # Check if the ultra-fast module exists
    ultra_fast_file = "src/agent/dataflows/ultra_fast_fundamentals_collector.py"
    if not os.path.exists(ultra_fast_file):
        print(f"❌ Ultra-fast collector not found: {ultra_fast_file}")
        return False
    
    # Check if the integration module exists
    integration_file = "src/agent/analysts/fundamentals_analyst_ultra_fast.py"
    if not os.path.exists(integration_file):
        print(f"❌ Integration module not found: {integration_file}")
        return False
    
    # Try to import the modules
    try:
        sys.path.insert(0, 'src')
        from agent.dataflows.ultra_fast_fundamentals_collector import UltraFastFundamentalsCollector
        from agent.analysts.fundamentals_analyst_ultra_fast import create_fundamentals_analyst_ultra_fast
        print("✅ Modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 You may need to install dependencies: pip install httpx aioredis")
        return False


def print_usage():
    """Print usage instructions."""
    
    print("\n📚 Usage Instructions:")
    print("=" * 60)
    print("1. Test with COST ticker:")
    print("   ./debug_local.sh COST")
    print("")
    print("2. Test with NVDA ticker:")
    print("   ./debug_local.sh NVDA")
    print("")
    print("3. Skip preliminary tests for faster execution:")
    print("   ./debug_local.sh COST --skip-tests")
    print("")
    print("4. Monitor performance:")
    print("   - Check logs in debug_logs/ directory")
    print("   - Look for '⚡ fundamentals_analyst_ultra_fast' entries")
    print("   - Compare execution times (should be <2s vs 30-60s)")
    print("")
    print("5. To disable ultra-fast mode:")
    print("   - Restore backup files: *.backup_original")
    print("   - Delete .ultra_fast_fundamentals_enabled flag")
    print("=" * 60)


def main():
    """Main entry point."""
    
    # Check if we're in the right directory
    if not os.path.exists("src/agent/__init__.py"):
        print("❌ Error: Not in trading-graph-server directory")
        print("💡 Please run this script from the trading-graph-server directory")
        sys.exit(1)
    
    # Apply patches
    success = patch_graph_files()
    
    if not success:
        print("\n❌ Failed to apply patches")
        sys.exit(1)
    
    # Verify installation
    if verify_installation():
        print("\n🎉 Ultra-Fast Fundamentals Collector successfully enabled!")
        print_usage()
        
        print("\n🚀 Performance Improvements Expected:")
        print("  - 15-30x faster fundamentals collection")
        print("  - <2s response time (vs 30-60s with LLM)")
        print("  - 90% reduction in API overhead")
        print("  - Redis caching for <10ms cached responses")
        print("  - Circuit breaker for fault tolerance")
        
        sys.exit(0)
    else:
        print("\n⚠️  Installation verification failed")
        print("Please check the error messages above")
        sys.exit(1)


if __name__ == "__main__":
    main()