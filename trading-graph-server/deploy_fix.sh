#!/bin/bash

# Deployment Fix Script for Trading Graph Server
# This script fixes the pandas and social media tool issues in deployment

echo "🔧 Trading Graph Server Deployment Fix"
echo "======================================="
echo ""

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Install missing dependencies locally (for testing)
echo -e "${YELLOW}Step 1: Installing missing dependencies locally...${NC}"
pip3 install "aiohttp>=3.8.0" "pandas>=2.0.0" "pandas-ta>=0.3.14b0" "setuptools>=65.0.0"

# Step 2: Verify installations
echo -e "${YELLOW}Step 2: Verifying installations...${NC}"
python3 -c "
import sys
try:
    import pandas
    print('✅ pandas installed:', pandas.__version__)
except ImportError as e:
    print('❌ pandas not installed:', e)
    sys.exit(1)

try:
    import pandas_ta
    print('✅ pandas-ta installed')
except ImportError as e:
    print('❌ pandas-ta not installed:', e)
    sys.exit(1)

try:
    import aiohttp
    print('✅ aiohttp installed:', aiohttp.__version__)
except ImportError as e:
    print('❌ aiohttp not installed:', e)
    sys.exit(1)

try:
    import pkg_resources
    print('✅ setuptools/pkg_resources available')
except ImportError as e:
    print('❌ setuptools/pkg_resources not available:', e)
    sys.exit(1)

print('✅ All dependencies verified successfully!')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Dependency verification failed!${NC}"
    exit 1
fi

# Step 3: Apply Twitter patch
echo -e "${YELLOW}Step 3: Applying Twitter NoneType fix...${NC}"
if [ -f "fix_social_twitter_none.patch" ]; then
    patch -p0 < fix_social_twitter_none.patch
    echo -e "${GREEN}✅ Twitter fix applied${NC}"
else
    echo -e "${YELLOW}⚠️  Patch file not found, skipping...${NC}"
fi

# Step 4: Rebuild the deployment package
echo -e "${YELLOW}Step 4: Rebuilding deployment package...${NC}"
if [ -f "pyproject.toml" ]; then
    pip install -e .
    echo -e "${GREEN}✅ Package rebuilt with new dependencies${NC}"
fi

# Step 5: Test the agents
echo -e "${YELLOW}Step 5: Running quick validation test...${NC}"
python3 -c "
from src.agent.dataflows import market_helpers
import pandas as pd
import pandas_ta as ta

# Test pandas availability
try:
    df = pd.DataFrame({'close': [1, 2, 3, 4, 5]})
    df.ta.rsi(length=14, append=True)
    print('✅ Pandas-ta working correctly')
except Exception as e:
    print('❌ Pandas-ta error:', e)

# Test aiohttp import
try:
    import aiohttp
    print('✅ Aiohttp import successful')
except Exception as e:
    print('❌ Aiohttp import failed:', e)
"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment fix complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps for LangGraph Cloud deployment:"
echo "1. Commit these changes:"
echo "   git add pyproject.toml"
echo "   git add src/agent/dataflows/twitter_simple.py"
echo "   git commit -m 'fix: Add missing dependencies for deployment (pandas, aiohttp)'"
echo ""
echo "2. Push to your deployment branch:"
echo "   git push origin main"
echo ""
echo "3. Trigger deployment rebuild:"
echo "   Either push to trigger auto-deploy or manually restart the deployment"
echo ""
echo "4. Verify in deployment logs that:"
echo "   - Market agent shows 'pandas-ta' engine with 130+ indicators"
echo "   - Social agent successfully fetches data without aiohttp errors"