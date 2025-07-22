#!/usr/bin/env python3
"""
Deployment Validation Script for Trading Agents LangGraph Cloud

This script validates that your project is ready for LangGraph Cloud deployment.
Run this before deploying to catch any issues early.
"""

import os
import sys
import json
from pathlib import Path


def validate_file_structure():
    """Validate required files exist."""
    print("📋 Validating file structure...")
    
    required_files = [
        "langgraph.json",
        "graph_entry.py", 
        "requirements.txt",
        "env.production.example",
        "tradingagents/__init__.py",
        "tradingagents/graph/trading_graph.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True


def validate_langgraph_config():
    """Validate langgraph.json configuration."""
    print("📋 Validating LangGraph configuration...")
    
    try:
        with open("langgraph.json", "r") as f:
            config = json.load(f)
        
        required_keys = ["dependencies", "graphs", "env"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing key '{key}' in langgraph.json")
                return False
        
        # Check graph entry point
        if "trading-agent" not in config["graphs"]:
            print("❌ Missing 'trading-agent' graph in configuration")
            return False
            
        entry_point = config["graphs"]["trading-agent"]
        if not entry_point.endswith(":compiled_graph"):
            print(f"❌ Invalid entry point: {entry_point}")
            return False
        
        print("✅ LangGraph configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading langgraph.json: {e}")
        return False


def validate_graph_compilation():
    """Test that the graph compiles without errors."""
    print("📋 Validating graph compilation...")
    
    try:
        import graph_entry
        graph = graph_entry.compiled_graph
        
        # Check graph has nodes
        nodes = list(graph.get_graph().nodes.keys())
        if len(nodes) < 10:
            print(f"❌ Graph has too few nodes: {len(nodes)}")
            return False
            
        print(f"✅ Graph compiled successfully ({len(nodes)} nodes)")
        return True
        
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        return False


def validate_dependencies():
    """Check that key dependencies are listed."""
    print("📋 Validating dependencies...")
    
    try:
        with open("requirements.txt", "r") as f:
            deps = f.read().lower()
        
        required_deps = [
            "langgraph",
            "langchain-openai", 
            "serpapi",
            "finnhub-python"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if dep not in deps:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing dependencies: {missing_deps}")
            return False
            
        print("✅ Key dependencies present")
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False


def validate_environment_template():
    """Check environment template has required keys."""
    print("📋 Validating environment template...")
    
    try:
        with open("env.production.example", "r") as f:
            env_content = f.read()
        
        required_vars = [
            "OPENAI_API_KEY",
            "SERPER_API_KEY", 
            "FINNHUB_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False
            
        print("✅ Environment template complete")
        return True
        
    except Exception as e:
        print(f"❌ Error reading env.production.example: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Trading Agents - LangGraph Cloud Deployment Validation")
    print("=" * 60)
    
    checks = [
        validate_file_structure,
        validate_langgraph_config, 
        validate_dependencies,
        validate_environment_template,
        validate_graph_compilation,  # This one last as it's most intensive
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
            print()  # Add spacing
        except Exception as e:
            print(f"❌ Validation error: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Your project is ready for LangGraph Cloud deployment!")
        print("\nNext steps:")
        print("1. Copy env.production.example to .env")
        print("2. Fill in your API keys")
        print("3. Run: langgraph deploy --config langgraph.json")
    else:
        print("❌ Please fix the above issues before deploying")
        sys.exit(1)


if __name__ == "__main__":
    main() 