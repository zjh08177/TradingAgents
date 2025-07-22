#!/bin/bash

# LangGraph Cloud Deployment Script
# Deploy from trading-graph-server directory

echo "🚀 Deploying Trading Agents to LangGraph Cloud..."
echo "================================================="

# Navigate to trading-graph-server directory
cd trading-graph-server || {
    echo "❌ Error: trading-graph-server directory not found"
    echo "💡 Make sure you're running this from the TradingAgents project root"
    exit 1
}

# Check if langgraph.json exists
if [ ! -f "langgraph.json" ]; then
    echo "❌ Error: langgraph.json not found in trading-graph-server directory"
    exit 1
fi

# Check if required files exist
echo "📋 Checking required files..."
if [ ! -f ".env" ]; then
    echo "❌ Error: .env not found in trading-graph-server"
    echo "💡 Please create .env with your API keys"
    exit 1
fi

if [ ! -f "src/agent/__init__.py" ]; then
    echo "❌ Error: src/agent/__init__.py not found"
    exit 1
fi

if [ ! -d "src/agent" ]; then
    echo "❌ Error: src/agent directory not found"
    exit 1
fi

echo "✅ All required files found in trading-graph-server"

# Activate virtual environment and validate
echo ""
echo "🔍 Running deployment validation..."
if source venv/bin/activate && python -c "from src.agent import graph; print('✅ Graph validation successful')"; then
    echo ""
    echo "🚀 Starting deployment..."
    echo "Run the following command from trading-graph-server directory:"
    echo ""
    echo "cd trading-graph-server && langgraph deploy"
    echo ""
    echo "📝 Note: Make sure you have:"
    echo "   1. Installed langraph CLI: pip install langraph-cli"
    echo "   2. Logged in: langraph auth login"  
    echo "   3. Set up your API keys in trading-graph-server/.env"
    echo "   4. All dependencies installed in trading-graph-server/venv"
else
    echo ""
    echo "❌ Validation failed. Please fix the issues above before deploying."
    exit 1
fi 