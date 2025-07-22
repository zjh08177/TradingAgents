#!/bin/bash

# LangGraph Cloud Deployment Script
# Run from project root: ./deploy.sh

echo "🚀 Deploying Trading Agents to LangGraph Cloud..."
echo "================================================="

# Check if langgraph.json exists
if [ ! -f "langgraph.json" ]; then
    echo "❌ Error: langgraph.json not found in current directory"
    echo "💡 Make sure you're running this from the TradingAgents project root"
    exit 1
fi

# Check if required files exist
echo "📋 Checking required files..."
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo "💡 Please create backend/.env with your API keys"
    exit 1
fi

if [ ! -f "backend/graph_entry.py" ]; then
    echo "❌ Error: backend/graph_entry.py not found"
    exit 1
fi

if [ ! -d "backend/tradingagents" ]; then
    echo "❌ Error: backend/tradingagents directory not found"
    exit 1
fi

echo "✅ All required files found"

# Run validation with virtual environment
echo ""
echo "🔍 Running deployment validation..."
if source backend/.venv/bin/activate && python3 backend/validate_deployment.py; then
    echo ""
    echo "🚀 Starting deployment..."
    echo "Run the following command:"
    echo ""
    echo "langgraph deploy --config langgraph.json"
    echo ""
    echo "📝 Note: Make sure you have:"
    echo "   1. Installed langraph CLI: pip install langraph-cli"
    echo "   2. Logged in: langraph auth login"
    echo "   3. Set up your API keys in backend/.env"
else
    echo ""
    echo "❌ Validation failed. Please fix the issues above before deploying."
    exit 1
fi 