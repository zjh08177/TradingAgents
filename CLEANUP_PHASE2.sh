#!/bin/bash
# Phase 2 Cleanup Script - Virtual Environment Optimization

echo "=== Phase 2: Virtual Environment Optimization ==="

# Backup current requirements
echo "1. Backing up current requirements..."
cd /Users/bytedance/Documents/TradingAgents/backend
pip freeze --path .venv/lib/python3.12/site-packages > requirements_current_backup.txt

cd /Users/bytedance/Documents/TradingAgents/trading-graph-server  
pip freeze --path .venv/lib/python3.12/site-packages > requirements_current_backup.txt

# Create new clean virtual environments
echo "2. Creating clean virtual environments..."
cd /Users/bytedance/Documents/TradingAgents/backend
mv .venv .venv_backup
python3 -m venv .venv_clean
source .venv_clean/bin/activate
pip install -r requirements_minimal.txt

# Test basic functionality
echo "3. Testing backend with minimal dependencies..."
python -c "import langchain_core; import pandas; print('Basic imports OK')"

echo "Phase 2 complete. Test your application before removing backup venvs."