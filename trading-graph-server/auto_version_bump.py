#!/usr/bin/env python3
"""
Auto Version Bump Utility
Automatically increments version in pyproject.toml for LangGraph dev updates
"""

import re
import sys
from pathlib import Path

def bump_version(version_str: str, bump_type: str = "patch") -> str:
    """Bump semantic version string."""
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version_str}")
    
    major, minor, patch = map(int, parts)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

def update_pyproject_version(pyproject_path: Path, bump_type: str = "patch") -> tuple[str, str]:
    """Update version in pyproject.toml and return old, new versions."""
    
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")
    
    content = pyproject_path.read_text()
    
    # Find version line
    version_pattern = r'^version = "([^"]+)"'
    match = re.search(version_pattern, content, re.MULTILINE)
    
    if not match:
        raise ValueError("Version line not found in pyproject.toml")
    
    old_version = match.group(1)
    new_version = bump_version(old_version, bump_type)
    
    # Replace version
    new_content = re.sub(
        version_pattern,
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    pyproject_path.write_text(new_content)
    
    return old_version, new_version

def main():
    """Main execution function."""
    bump_type = sys.argv[1] if len(sys.argv) > 1 else "patch"
    
    if bump_type not in ["major", "minor", "patch"]:
        print(f"❌ Invalid bump type: {bump_type}")
        print("Usage: python auto_version_bump.py [major|minor|patch]")
        sys.exit(1)
    
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    
    try:
        old_version, new_version = update_pyproject_version(pyproject_path, bump_type)
        
        print(f"🚀 Version Bump Complete!")
        print(f"   Old: {old_version}")
        print(f"   New: {new_version}")
        print(f"   Type: {bump_type}")
        print()
        print("📋 Next Steps:")
        print("   1. Run: pip install .")
        print("   2. LangGraph dev will automatically use new code")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()