#!/usr/bin/env python3
"""
Create required data directories for trading graph server.
This script ensures all necessary data directories exist to prevent FileNotFoundError issues.
"""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_data_directories():
    """Create all required data directories for the trading graph server."""
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define required directories
    required_directories = [
        "data/finnhub_data/news_data",
        "data/finnhub_data/earnings_data", 
        "data/finnhub_data/stock_data",
        "data/cache",
        "data/logs",
        "debug_logs",
        "scripts/trace_analysis_reports",
        "claude_doc/agent_improvement_plans",
        "claude_doc/agent_improvement_plans/fundamentals_analyst",
        "claude_doc/agent_improvement_plans/market_analyst", 
        "claude_doc/agent_improvement_plans/news_analyst",
        "claude_doc/agent_improvement_plans/social_analyst"
    ]
    
    created_count = 0
    exists_count = 0
    
    for directory in required_directories:
        dir_path = project_root / directory
        
        if dir_path.exists():
            logger.info(f"✅ Directory already exists: {directory}")
            exists_count += 1
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Created directory: {directory}")
                created_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to create directory {directory}: {e}")
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"   ✅ Existing directories: {exists_count}")
    logger.info(f"   📁 Created directories: {created_count}")
    logger.info(f"   📁 Total directories: {len(required_directories)}")
    
    if created_count > 0:
        logger.info(f"🚀 Successfully created {created_count} missing directories")
    else:
        logger.info("✅ All required directories already exist")

if __name__ == "__main__":
    create_data_directories()