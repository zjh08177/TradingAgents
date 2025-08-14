#!/usr/bin/env python3
"""
Runtime Code Verification Script
=================================
This script verifies that the token reduction fixes are actually loaded and running.
It will help prove whether the system is using old cached code or the new fixed versions.

Usage: python verify_runtime_code.py
"""

import os
import sys
import importlib
import logging
from datetime import datetime

# Set up critical-level logging to see verification messages
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_imports():
    """Verify that the correct modules can be imported and contain expected code."""
    print("\n" + "="*80)
    print("🔍 RUNTIME CODE VERIFICATION SCRIPT")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    verification_results = []
    
    # Test 1: Verify news_analyst_ultra_fast.py has token limits
    print("\n📰 TEST 1: Checking news_analyst_ultra_fast.py...")
    try:
        from src.agent.analysts import news_analyst_ultra_fast
        
        # Check if the module has the expected token limit constant
        module_source = open('src/agent/analysts/news_analyst_ultra_fast.py', 'r').read()
        
        checks = {
            "MAX_ARTICLES = 15": "MAX_ARTICLES = 15" in module_source,
            "RUNTIME VERIFICATION logs": "RUNTIME VERIFICATION" in module_source,
            "ARTICLE LIMIT VERIFICATION": "ARTICLE LIMIT VERIFICATION" in module_source,
            "FINAL ARTICLE COUNT VERIFICATION": "FINAL ARTICLE COUNT VERIFICATION" in module_source
        }
        
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {'FOUND' if check_result else 'NOT FOUND'}")
            verification_results.append((f"news_analyst: {check_name}", check_result))
            
    except Exception as e:
        print(f"  ❌ ERROR: Could not verify news_analyst_ultra_fast.py: {e}")
        verification_results.append(("news_analyst", False))
    
    # Test 2: Verify social_media_analyst_hardcoded.py has token limits
    print("\n📱 TEST 2: Checking social_media_analyst_hardcoded.py...")
    try:
        from src.agent.analysts import social_media_analyst_hardcoded
        
        module_source = open('src/agent/analysts/social_media_analyst_hardcoded.py', 'r').read()
        
        checks = {
            "MAX_SOCIAL_TOKENS = 3000": "MAX_SOCIAL_TOKENS = 3000" in module_source,
            "RUNTIME VERIFICATION logs": "RUNTIME VERIFICATION" in module_source,
            "SOCIAL MEDIA TOKEN LIMIT VERIFICATION": "SOCIAL MEDIA TOKEN LIMIT VERIFICATION" in module_source
        }
        
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {'FOUND' if check_result else 'NOT FOUND'}")
            verification_results.append((f"social_media: {check_name}", check_result))
            
    except Exception as e:
        print(f"  ❌ ERROR: Could not verify social_media_analyst_hardcoded.py: {e}")
        verification_results.append(("social_media", False))
    
    # Test 3: Verify risk management agents have token limits
    print("\n⚠️ TEST 3: Checking risk management agents...")
    risk_agents = [
        ('conservative_debator', 'src/agent/risk_mgmt/conservative_debator.py'),
        ('aggresive_debator', 'src/agent/risk_mgmt/aggresive_debator.py'),
        ('neutral_debator', 'src/agent/risk_mgmt/neutral_debator.py')
    ]
    
    for agent_name, agent_path in risk_agents:
        print(f"\n  Checking {agent_name}...")
        try:
            module_source = open(agent_path, 'r').read()
            
            checks = {
                "MAX_RISK_RESPONSE_TOKENS = 2000": "MAX_RISK_RESPONSE_TOKENS = 2000" in module_source,
                "RUNTIME VERIFICATION logs": "RUNTIME VERIFICATION" in module_source,
                "TOKEN LIMIT VERIFICATION": "TOKEN LIMIT VERIFICATION" in module_source
            }
            
            for check_name, check_result in checks.items():
                status = "✅" if check_result else "❌"
                print(f"    {status} {check_name}: {'FOUND' if check_result else 'NOT FOUND'}")
                verification_results.append((f"{agent_name}: {check_name}", check_result))
                
        except Exception as e:
            print(f"    ❌ ERROR: Could not verify {agent_name}: {e}")
            verification_results.append((agent_name, False))
    
    # Test 4: Verify graph configuration uses correct analysts
    print("\n🔗 TEST 4: Checking graph node configuration...")
    try:
        module_source = open('src/agent/graph/nodes/enhanced_parallel_analysts.py', 'r').read()
        
        checks = {
            "imports news_analyst_ultra_fast": "from ...analysts.news_analyst_ultra_fast import" in module_source,
            "RUNTIME VERIFICATION in module": "RUNTIME VERIFICATION: enhanced_parallel_analysts.py" in module_source,
            "CREATING NEWS ANALYST NODE logs": "CREATING NEWS ANALYST NODE" in module_source
        }
        
        for check_name, check_result in checks.items():
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {'FOUND' if check_result else 'NOT FOUND'}")
            verification_results.append((f"graph_config: {check_name}", check_result))
            
    except Exception as e:
        print(f"  ❌ ERROR: Could not verify graph configuration: {e}")
        verification_results.append(("graph_config", False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 VERIFICATION SUMMARY")
    print("="*80)
    
    total_checks = len(verification_results)
    passed_checks = sum(1 for _, result in verification_results if result)
    failed_checks = total_checks - passed_checks
    
    print(f"\n✅ Passed: {passed_checks}/{total_checks}")
    print(f"❌ Failed: {failed_checks}/{total_checks}")
    
    if failed_checks > 0:
        print("\n⚠️ WARNING: Some verification checks failed!")
        print("This indicates the token reduction fixes may NOT be properly deployed.")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Restart the Python process/server to clear any cached imports")
        print("2. Check for multiple Python environments or deployment locations")
        print("3. Verify no old .pyc files are being used")
        print("4. Force reload modules with: importlib.reload()")
    else:
        print("\n✅ SUCCESS: All verification checks passed!")
        print("The token reduction fixes appear to be properly deployed.")
        print("\n🔍 NEXT STEPS:")
        print("1. Run the graph with a test ticker to see the runtime logs")
        print("2. Check that CRITICAL logs appear showing article limits")
        print("3. Monitor token usage in the next trace")
    
    return passed_checks == total_checks

def test_dynamic_import():
    """Test that imports are using the current code, not cached versions."""
    print("\n" + "="*80)
    print("🔄 DYNAMIC IMPORT TEST")
    print("="*80)
    
    # Force reload of key modules to ensure latest code
    modules_to_reload = [
        'src.agent.analysts.news_analyst_ultra_fast',
        'src.agent.analysts.social_media_analyst_hardcoded',
        'src.agent.risk_mgmt.conservative_debator',
        'src.agent.risk_mgmt.aggresive_debator',
        'src.agent.risk_mgmt.neutral_debator',
        'src.agent.graph.nodes.enhanced_parallel_analysts'
    ]
    
    for module_name in modules_to_reload:
        try:
            if module_name in sys.modules:
                print(f"  🔄 Reloading {module_name}...")
                importlib.reload(sys.modules[module_name])
                print(f"    ✅ Successfully reloaded")
            else:
                print(f"  📦 Module {module_name} not loaded yet")
        except Exception as e:
            print(f"  ⚠️ Could not reload {module_name}: {e}")

if __name__ == "__main__":
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    print("\n🚀 Starting Runtime Code Verification...\n")
    
    # Run verification
    all_passed = verify_imports()
    
    # Test dynamic imports
    test_dynamic_import()
    
    # Final recommendation
    print("\n" + "="*80)
    print("🎯 FINAL RECOMMENDATION")
    print("="*80)
    
    if all_passed:
        print("\n✅ Code verification PASSED - Token reduction fixes are in place")
        print("\n📝 To confirm fixes are ACTIVE in production:")
        print("1. Run: python debug_local.sh AAPL")
        print("2. Look for these CRITICAL logs:")
        print("   - '🔥🔥🔥 RUNTIME VERIFICATION: news_analyst_ultra_fast.py VERSION ACTIVE'")
        print("   - '🔥 ARTICLE LIMIT VERIFICATION' showing ≤15 articles")
        print("   - '🔥 SOCIAL MEDIA TOKEN LIMIT VERIFICATION'")
        print("3. If logs don't appear, the server is using cached/old code")
    else:
        print("\n❌ Code verification FAILED - Token reduction fixes may not be deployed")
        print("\n🔧 CRITICAL ACTIONS REQUIRED:")
        print("1. Stop all Python processes: pkill -f python")
        print("2. Clear Python cache: find . -name '*.pyc' -delete")
        print("3. Restart the server: python restart_server.sh")
        print("4. Run this script again to verify")
    
    print("\n" + "="*80)
    print("Verification complete.")
    print("="*80)