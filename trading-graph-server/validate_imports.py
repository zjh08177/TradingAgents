#!/usr/bin/env python3
"""
Import Validation Script
Future-proofing tool to detect import issues and classify real vs false errors
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

def scan_for_import_issues(directory: str) -> Dict[str, List[str]]:
    """Scan Python files for potential import issues"""
    issues = {
        'direct_pandas': [],
        'direct_yfinance': [],
        'direct_stockstats': [],
        'missing_lazy_loading': []
    }
    
    python_files = Path(directory).rglob("*.py")
    
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for direct pandas usage without lazy loading
                    if re.search(r'\bpd\.', line) and '_get_pandas()' not in content:
                        issues['direct_pandas'].append(f"{file_path}:{i} - {line.strip()}")
                    
                    # Check for direct yfinance usage
                    if re.search(r'\byf\.', line) and '_get_yfinance()' not in content:
                        issues['direct_yfinance'].append(f"{file_path}:{i} - {line.strip()}")
                    
                    # Check for direct stockstats usage
                    if re.search(r'\bwrap\(', line) and '_get_stockstats_wrap()' not in content:
                        issues['direct_stockstats'].append(f"{file_path}:{i} - {line.strip()}")
                        
        except Exception as e:
            print(f"Warning: Could not scan {file_path}: {e}")
    
    return issues

def classify_log_errors(log_content: str) -> Dict[str, List[str]]:
    """Classify log entries into real errors vs debug artifacts"""
    real_errors = []
    false_positives = []
    
    lines = log_content.split('\n')
    
    # Patterns that indicate real errors
    real_error_patterns = [
        r'Error.*Exception',
        r'Traceback.*Exception',
        r'.*not defined',
        r'.*ImportError',
        r'.*ModuleNotFoundError',
        r'.*AttributeError.*not.*attribute',
        r'.*KeyError.*not found'
    ]
    
    # Patterns that are false positives
    false_positive_patterns = [
        r'default.*model.*gpt',
        r'incomplete_details.*None',
        r'Response Length.*0 chars',
        r'DEBUG.*0 items',
        r'chars.*Apple Inc',
        r'Request options.*default'
    ]
    
    for line in lines:
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in real_error_patterns):
            # Double-check it's not a false positive
            if not any(re.search(fp_pattern, line, re.IGNORECASE) for fp_pattern in false_positive_patterns):
                real_errors.append(line.strip())
        elif any(re.search(pattern, line, re.IGNORECASE) for pattern in false_positive_patterns):
            false_positives.append(line.strip())
    
    return {
        'real_errors': real_errors,
        'false_positives': false_positives
    }

def validate_stockstats_module():
    """Test the stockstats module functionality"""
    try:
        sys.path.insert(0, 'src')
        from agent.dataflows.stockstats_utils import StockstatsUtils
        
        # Test basic functionality
        test_indicators = ['close_50_sma', 'vwma', 'macd']
        results = {}
        
        for indicator in test_indicators:
            try:
                result = StockstatsUtils.get_stock_stats('AAPL', indicator, '2025-07-22', './test_data', online=True)
                if isinstance(result, (int, float)):
                    results[indicator] = f"✅ SUCCESS: {result}"
                elif 'N/A' in str(result):
                    results[indicator] = f"✅ OK: {result}"
                else:
                    results[indicator] = f"❌ ERROR: {result}"
            except Exception as e:
                results[indicator] = f"❌ EXCEPTION: {e}"
        
        return results
    except Exception as e:
        return {"import_error": f"❌ Cannot import module: {e}"}

def main():
    print("🔍 Import Validation and Error Classification")
    print("=" * 50)
    
    # 1. Scan for import issues
    print("\n📊 Scanning for Import Issues...")
    issues = scan_for_import_issues('src')
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    
    if total_issues == 0:
        print("✅ No import issues detected!")
    else:
        print(f"❌ Found {total_issues} potential import issues:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"\n  {issue_type}:")
                for issue in issue_list[:5]:  # Show first 5
                    print(f"    {issue}")
                if len(issue_list) > 5:
                    print(f"    ... and {len(issue_list) - 5} more")
    
    # 2. Test stockstats functionality
    print("\n🧪 Testing Stockstats Functionality...")
    stockstats_results = validate_stockstats_module()
    
    for indicator, result in stockstats_results.items():
        print(f"  {indicator}: {result}")
    
    # 3. Analyze recent log if available
    print("\n📋 Log Analysis...")
    debug_logs = list(Path('debug_logs').glob('debug_session_*.log'))
    
    if debug_logs:
        latest_log = max(debug_logs, key=os.path.getctime)
        print(f"Analyzing: {latest_log}")
        
        try:
            with open(latest_log, 'r') as f:
                log_content = f.read()
            
            classification = classify_log_errors(log_content)
            
            print(f"  Real Errors: {len(classification['real_errors'])}")
            print(f"  False Positives: {len(classification['false_positives'])}")
            
            if classification['real_errors']:
                print("\n  Real Errors Found:")
                for error in classification['real_errors'][:3]:
                    print(f"    {error[:100]}...")
        except Exception as e:
            print(f"  Could not analyze log: {e}")
    else:
        print("  No debug logs found")
    
    # 4. Summary
    print("\n" + "=" * 50)
    stockstats_working = all('SUCCESS' in str(result) or 'OK' in str(result) 
                           for result in stockstats_results.values())
    
    if total_issues == 0 and stockstats_working:
        print("🎉 VALIDATION PASSED: System is healthy!")
        return 0
    else:
        print("⚠️  VALIDATION ISSUES: Please review findings above")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 