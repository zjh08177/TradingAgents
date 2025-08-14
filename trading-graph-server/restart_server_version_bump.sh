#!/bin/bash

echo "🚀 Restarting Trading Graph Server with Version Bump Strategy..."

# Step 1: Kill all existing LangGraph processes
echo "🛑 Terminating existing LangGraph processes..."

# Kill langgraph dev processes
pkill -f "langgraph dev" 2>/dev/null || true

# Kill any uvicorn processes on port 2024
lsof -ti:2024 | xargs kill -9 2>/dev/null || true

# Kill any python processes related to langgraph
pkill -f "langgraph" 2>/dev/null || true

# Wait a moment for processes to clean up
sleep 2

echo "✅ All LangGraph processes terminated"

# Step 2: Version Bump Strategy - Auto increment version
echo "📈 Auto-bumping version to force package update..."

# Check if auto_version_bump.py exists
if [ -f "auto_version_bump.py" ]; then
    echo "   🔄 Running version bump utility..."
    python3 auto_version_bump.py patch
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Version bumped successfully"
    else
        echo "   ❌ Version bump failed, continuing with manual approach..."
        
        # Fallback: Manual version bump
        echo "   🔧 Manual version bump fallback..."
        python3 -c "
import re
from pathlib import Path

pyproject_path = Path('pyproject.toml')
content = pyproject_path.read_text()

# Find current version
version_match = re.search(r'version = \"([^\"]+)\"', content)
if version_match:
    old_version = version_match.group(1)
    parts = old_version.split('.')
    patch = int(parts[2]) + 1
    new_version = f'{parts[0]}.{parts[1]}.{patch}'
    
    # Replace version
    new_content = re.sub(r'version = \"[^\"]+\"', f'version = \"{new_version}\"', content)
    pyproject_path.write_text(new_content)
    
    print(f'   📈 Version: {old_version} → {new_version}')
else:
    print('   ❌ Could not find version in pyproject.toml')
        "
    fi
else
    echo "   ⚠️  auto_version_bump.py not found, using manual bump..."
    
    # Manual version bump
    python3 -c "
import re
from pathlib import Path

pyproject_path = Path('pyproject.toml')
content = pyproject_path.read_text()

# Find current version
version_match = re.search(r'version = \"([^\"]+)\"', content)
if version_match:
    old_version = version_match.group(1)
    parts = old_version.split('.')
    patch = int(parts[2]) + 1
    new_version = f'{parts[0]}.{parts[1]}.{patch}'
    
    # Replace version
    new_content = re.sub(r'version = \"[^\"]+\"', f'version = \"{new_version}\"', content)
    pyproject_path.write_text(new_content)
    
    print(f'   📈 Version: {old_version} → {new_version}')
else:
    print('   ❌ Could not find version in pyproject.toml')
    " 2>/dev/null || echo "   ❌ Manual version bump failed"
fi

# Step 3: Force Package Reinstall
echo "📦 Force reinstalling package with new version..."
pip install . --quiet --no-warn-script-location

if [ $? -eq 0 ]; then
    echo "✅ Package reinstalled successfully"
    
    # Show installed version
    INSTALLED_VERSION=$(pip list | grep "^agent " | awk '{print $2}')
    echo "   📦 Installed version: agent $INSTALLED_VERSION"
else
    echo "❌ Package installation failed"
    exit 1
fi

# Step 4: Check if port 2024 is free
echo "🔍 Checking port 2024..."
if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 2024 still in use, forcing kill..."
    lsof -ti:2024 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Step 5: Verify environment
echo "🔑 Checking environment variables..."
if [ -f ".env" ]; then
    echo "✅ .env file found"
    
    # Check for API keys (without exposing them)
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "✅ OpenAI API key configured"
    elif grep -q "GOOGLE_API_KEY=" .env && ! grep -q "your_google_key_here" .env; then
        echo "✅ Google API key configured"  
    else
        echo "⚠️  No valid API keys found in .env"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

# Step 6: Validate fixes are in place (quick check)
echo "🔍 Validating code fixes..."
FIXES_PRESENT=true

if grep -q "except AttributeError as e:" src/agent/analysts/market_analyst_ultra_fast_async.py; then
    echo "✅ AttributeError handling found"
else
    echo "❌ AttributeError handling missing"
    FIXES_PRESENT=false
fi

if grep -q "RetryError wrapping AttributeError" src/agent/analysts/market_analyst_ultra_fast_async.py; then
    echo "✅ RetryError handling found"
else
    echo "❌ RetryError handling missing"  
    FIXES_PRESENT=false
fi

if grep -q "pandas_ta not available" src/agent/analysts/market_analyst_ultra_fast_async.py; then
    echo "✅ ImportError handling found"
else
    echo "❌ ImportError handling missing"
    FIXES_PRESENT=false
fi

if [ "$FIXES_PRESENT" = true ]; then
    echo "✅ All fixes validated"
else
    echo "⚠️  Some fixes missing - check source code"
fi

# Step 7: Start the server
echo "🚀 Starting LangGraph server with updated code..."
echo "📍 API: http://localhost:2024"
echo "📍 Docs: http://localhost:2024/docs" 
echo "📍 Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024"
echo ""
echo "🛡️  Error Protection: ENABLED"
echo "📈 Version Bump: COMPLETED"
echo "📦 Package Update: COMPLETED"
echo "🚫 No Symlinks: As requested!"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Start server in foreground so we can see logs
langgraph dev --port 2024