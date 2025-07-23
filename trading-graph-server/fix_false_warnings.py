#!/usr/bin/env python3
"""
Script to systematically downgrade false warning patterns in logging
"""
import re
import os

def fix_logging_file(filepath):
    """Fix logging levels in a file to eliminate false warnings"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Patterns to fix - downgrade to DEBUG level
    patterns = [
        # Response length logging
        (r'logger\.info\(f"📤 Response Length: \{[^}]+\} chars"\)', 
         r'logger.debug(f"📤 Response Length: {response_length} chars")  # Downgraded to DEBUG'),
        
        # Results counting
        (r'logger\.info\(f"📊 Results: \{[^}]+\} items"\)', 
         r'logger.debug(f"📊 Results: {count} items")  # Downgraded to DEBUG'),
         
        # RAW RESPONSE LENGTH
        (r'logger\.info\(f"🌐 RAW RESPONSE LENGTH: \{[^}]+\} items"\)', 
         r'logger.debug(f"🌐 RAW RESPONSE LENGTH: {len(news_results)} items")  # Downgraded to DEBUG'),
         
        # TOOL OUTPUT PREVIEW  
        (r'logger\.info\(f"📝 TOOL OUTPUT PREVIEW \(first 500 chars\):\\n\{[^}]+\}\.\.\."\)', 
         r'logger.debug(f"📝 TOOL OUTPUT PREVIEW (first 500 chars):\\n{result[:500]}...")  # Downgraded to DEBUG'),
         
        # EXTRACTED TEXT PREVIEW
        (r'logger\.info\(f"📝 EXTRACTED TEXT PREVIEW \(first 500 chars\):\\n\{[^}]+\}\.\.\."\)', 
         r'logger.debug(f"�� EXTRACTED TEXT PREVIEW (first 500 chars):\\n{result[:500]}...")  # Downgraded to DEBUG'),
    ]
    
    changes_made = 0
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            changes_made += len(re.findall(pattern, content))
            content = new_content
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {changes_made} logging patterns in {filepath}")
    else:
        print(f"ℹ️  No changes needed in {filepath}")

# Fix all relevant files
files_to_fix = [
    'src/agent/utils/debug_logging.py',
    'src/agent/dataflows/interface.py'
]

for file_path in files_to_fix:
    fix_logging_file(file_path)

print("🎯 False warning patterns fixed!")
