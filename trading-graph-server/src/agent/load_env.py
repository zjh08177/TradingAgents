#!/usr/bin/env python3
"""
Environment Loader - Load .env file BEFORE importing any other modules

This module should be imported FIRST in your application entry point:

    # In your main application file (e.g., debug_local.sh, app.py, main.py):
    import sys
    sys.path.insert(0, 'src')
    
    # CRITICAL: Load environment FIRST before any other imports
    from agent.load_env import load_environment
    load_environment()
    
    # NOW you can import other modules that use the config
    from agent.graph.trading_graph import TradingAgentsGraph
    # ... rest of your imports
    
This ensures environment variables are set WITHOUT any blocking I/O
happening during module imports in the async context.
"""

import os
from pathlib import Path
from typing import Optional


def load_environment(env_file: Optional[str] = None, verbose: bool = False) -> bool:
    """
    Load environment variables from .env file.
    
    This should be called ONCE at application startup, BEFORE importing
    any modules that use configuration.
    
    Args:
        env_file: Path to .env file (default: looks for .env in current dir)
        verbose: Print loading status
        
    Returns:
        True if environment loaded successfully
    """
    # Only import dotenv when actually loading (not at module import time)
    try:
        from dotenv import load_dotenv
    except ImportError:
        if verbose:
            print("⚠️ python-dotenv not installed. Environment variables must be set manually.")
        return False
    
    # Determine .env file path
    if env_file:
        env_path = Path(env_file)
    else:
        # Look for .env in current directory and parent directories
        current = Path.cwd()
        env_path = current / ".env"
        
        # If not found, check parent directories
        if not env_path.exists():
            for parent in current.parents:
                potential_env = parent / ".env"
                if potential_env.exists():
                    env_path = potential_env
                    break
    
    # Load the environment file if it exists
    if env_path.exists():
        if verbose:
            print(f"📋 Loading environment from: {env_path}")
        
        # Load the .env file
        load_dotenv(env_path, override=False)
        
        if verbose:
            # Show what was loaded (without exposing secrets)
            loaded_vars = []
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key = line.split('=')[0].strip()
                        if os.getenv(key):
                            loaded_vars.append(key)
            
            if loaded_vars:
                print(f"✅ Loaded {len(loaded_vars)} environment variables")
                if verbose == "debug":
                    print(f"   Variables: {', '.join(loaded_vars)}")
            else:
                print("⚠️ .env file found but no variables loaded")
        
        return True
    else:
        if verbose:
            print(f"ℹ️ No .env file found at {env_path}")
            print("   Using system environment variables only")
        return False


def ensure_environment():
    """
    Ensure environment is loaded. 
    This is a convenience function that loads with default settings.
    """
    return load_environment(verbose=False)


# DO NOT load environment at module import time!
# The application must explicitly call load_environment()
if __name__ == "__main__":
    # Only load if running this module directly (for testing)
    import sys
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    debug = "--debug" in sys.argv
    
    if debug:
        success = load_environment(verbose="debug")
    else:
        success = load_environment(verbose=verbose)
    
    if success:
        print("✅ Environment loaded successfully")
        
        # Test that config can be loaded without blocking I/O
        print("\n🧪 Testing async-safe config loading...")
        from agent.config import get_trading_config
        config = get_trading_config()
        print(f"✅ Config loaded successfully")
        print(f"   LLM Provider: {config.llm_provider}")
        print(f"   Deep Think Model: {config.deep_think_model}")
        print(f"   Quick Think Model: {config.quick_think_model}")
    else:
        print("⚠️ Environment loading failed or no .env file found")
        sys.exit(1)