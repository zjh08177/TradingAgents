#!/usr/bin/env python3
"""
Force Module Reload Script
Forces Python to reload all market analyst modules to ensure fixes are applied
"""

import sys
import importlib
import os

def force_reload_market_analyst_modules():
    """Force reload all market analyst related modules"""
    
    print("🔄 Forcing reload of market analyst modules...")
    
    # List of modules to reload
    modules_to_reload = [
        'src.agent.analysts.market_analyst_ultra_fast_async',
        'src.agent.dataflows.empty_response_handler',
        'src.agent.dataflows.yfin_utils', 
        'src.agent.dataflows.stockstats_utils',
        'src.agent.dataflows.interface',
        'src.agent.graph.enhanced_optimized_setup',
        'src.agent.graph.nodes.enhanced_parallel_analysts'
    ]
    
    reloaded_count = 0
    
    for module_name in modules_to_reload:
        try:
            if module_name in sys.modules:
                print(f"   🔄 Reloading: {module_name}")
                importlib.reload(sys.modules[module_name])
                reloaded_count += 1
            else:
                print(f"   ⚠️ Not loaded: {module_name}")
        except Exception as e:
            print(f"   ❌ Failed to reload {module_name}: {e}")
    
    print(f"✅ Reloaded {reloaded_count} modules")
    
    # Also clear any import caches
    if hasattr(importlib, 'invalidate_caches'):
        importlib.invalidate_caches()
        print("✅ Invalidated import caches")
    
    return reloaded_count

if __name__ == "__main__":
    force_reload_market_analyst_modules()