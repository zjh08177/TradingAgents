#!/usr/bin/env python3
"""Configuration validation script for trading graph server"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from agent.monitoring.configuration_validator import validate_startup_configuration
    
    print("🔍 Starting comprehensive configuration validation...")
    results = validate_startup_configuration()
    
    print(f"📊 Validation Summary:")
    print(f"  Total checks: {results['total_checks']}")
    print(f"  Passed: {results['passed_checks']}")
    print(f"  Failed: {results['failed_checks']}")
    print(f"  Success rate: {results['success_rate']}%")
    print(f"  Overall status: {results['overall_status']}")
    print(f"  Can proceed: {results['can_proceed']}")
    
    # Print issues if any
    if results['critical_issues'] > 0:
        print(f"\n🚨 CRITICAL ISSUES ({results['critical_issues']}):")
        for issue in results['issues_by_severity']['critical']:
            print(f"  ❌ {issue['component']}: {issue['message']}")
    
    if results['error_issues'] > 0:
        print(f"\n🚨 ERROR ISSUES ({results['error_issues']}):")
        for issue in results['issues_by_severity']['error']:
            print(f"  ⚠️ {issue['component']}: {issue['message']}")
    
    if results['warning_issues'] > 0:
        print(f"\n⚠️ WARNING ISSUES ({results['warning_issues']}):")
        for issue in results['issues_by_severity']['warning']:
            print(f"  ⚠️ {issue['component']}: {issue['message']}")
    
    if not results['can_proceed']:
        print("\n🚨 CRITICAL CONFIGURATION ISSUES DETECTED - CANNOT PROCEED")
        print("Please resolve the critical issues above before running the trading graph.")
        sys.exit(1)
    else:
        print("\n✅ CONFIGURATION VALIDATION PASSED - Safe to proceed")
        
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    print("Proceeding with execution but configuration issues may cause failures...")

