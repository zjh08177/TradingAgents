#!/usr/bin/env python3
"""
Enable Token Limiting in All Agents
Uncomments the token limiting calls that were disabled for debugging
"""

import os
import re
from pathlib import Path

def enable_token_limiting_in_file(filepath: str):
    """Enable token limiting in a specific file"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to find commented out token limiting calls
    patterns = [
        (r'# messages = get_token_limiter\(\)\.check_and_enforce_limit\((.*?)\)',
         r'messages = get_token_limiter().check_and_enforce_limit(\1)'),
        (r'# (\s*)messages = get_token_limiter\(\)\.check_and_enforce_limit\((.*?)\)',
         r'\1messages = get_token_limiter().check_and_enforce_limit(\2)'),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Enabled token limiting in: {filepath}")
        return True
    else:
        # Check if already enabled
        if 'messages = get_token_limiter().check_and_enforce_limit' in content:
            print(f"✓  Token limiting already enabled in: {filepath}")
        else:
            print(f"⚠️  No token limiting found in: {filepath}")
        return False

def main():
    """Enable token limiting in all agent files"""
    
    # Base directory
    base_dir = Path(__file__).parent.parent / "src" / "agent"
    
    # Agent directories and files
    agent_locations = [
        ("analysts", ["market_analyst.py", "news_analyst.py", "social_media_analyst.py", "fundamentals_analyst.py"]),
        ("managers", ["risk_manager.py", "research_manager.py"]),
        ("trader", ["trader.py"]),
        ("researchers", ["bull_researcher.py", "bear_researcher.py"]),
        ("risk_mgmt", ["aggresive_debator.py", "conservative_debator.py", "neutral_debator.py"])
    ]
    
    total_files = 0
    enabled_files = 0
    
    print("Enabling Token Limiting in All Agents")
    print("=" * 50)
    
    for directory, files in agent_locations:
        dir_path = base_dir / directory
        print(f"\nProcessing {directory}/")
        
        for file in files:
            filepath = dir_path / file
            if filepath.exists():
                total_files += 1
                if enable_token_limiting_in_file(str(filepath)):
                    enabled_files += 1
            else:
                print(f"❌ File not found: {filepath}")
    
    print("\n" + "=" * 50)
    print(f"Summary: Enabled token limiting in {enabled_files}/{total_files} files")
    
    # Also update any other references
    print("\nChecking for other token limiting references...")
    
    # Search for any other commented token limiting
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "# messages = get_token_limiter", str(base_dir)],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("\nOther files with commented token limiting:")
        print(result.stdout)

if __name__ == "__main__":
    main()