#!/bin/bash

# TradingAgents Railway Deployment Script
# This script helps deploy the TradingAgents API to Railway for App Store submission

set -e  # Exit on any error

echo "🚀 TradingAgents Railway Deployment Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "api.py" ]; then
    print_error "This script must be run from the backend directory"
    exit 1
fi

print_status "Step 1: Pre-deployment Checklist"
echo

# Check for required files
print_status "Checking required deployment files..."

if [ -f "railway.json" ]; then
    print_success "railway.json found"
else
    print_error "railway.json not found"
    exit 1
fi

if [ -f "Procfile" ]; then
    print_success "Procfile found"
else
    print_error "Procfile not found"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    print_success "requirements.txt found"
else
    print_error "requirements.txt not found"
    exit 1
fi

if [ -f "production.env.example" ]; then
    print_success "production.env.example found"
else
    print_warning "production.env.example not found (optional)"
fi

echo

print_status "Step 2: Environment Variables Check"
echo

print_warning "Make sure you have these API keys ready for Railway:"
echo "  📋 OPENAI_API_KEY=your_openai_key"
echo "  📋 FINNHUB_API_KEY=your_finnhub_key"
echo "  📋 SERPAPI_API_KEY=your_serpapi_key (optional but recommended)"
echo

print_status "Step 3: Git Repository Status"
echo

# Check git status
if git status --porcelain | grep -q .; then
    print_warning "You have uncommitted changes:"
    git status --short
    echo
    read -p "Do you want to commit these changes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo
        read -p "Enter commit message: " commit_message
        git add .
        git commit -m "$commit_message"
        print_success "Changes committed"
    else
        print_warning "Proceeding with uncommitted changes..."
    fi
else
    print_success "Working directory is clean"
fi

# Check if we're on a branch
current_branch=$(git branch --show-current)
print_status "Current branch: $current_branch"

# Push to remote
print_status "Pushing to remote repository..."
git push origin $current_branch
print_success "Code pushed to remote"

echo

print_status "Step 4: Railway Deployment Instructions"
echo

print_success "🎯 Ready for Railway deployment!"
echo
echo "Next steps:"
echo "1. 🌐 Go to https://railway.app"
echo "2. 🔑 Sign up/Login with your GitHub account"
echo "3. ➕ Click 'New Project' → 'Deploy from GitHub repo'"
echo "4. 📁 Select your TradingAgents repository"
echo "5. ⚙️  Railway will auto-detect Python and start building"
echo
echo "After deployment starts:"
echo "6. 🔧 Go to project → Variables tab"
echo "7. ➕ Add your environment variables:"
echo "   OPENAI_API_KEY=your_actual_key"
echo "   FINNHUB_API_KEY=your_actual_key"
echo "   SERPAPI_API_KEY=your_actual_key"
echo "8. 🌍 Go to Settings → Domains to get your public URL"
echo "9. 🧪 Test your API at https://your-app.railway.app/health"
echo

print_status "Step 5: Post-Deployment Tasks"
echo

echo "After successful Railway deployment:"
echo "1. 📝 Copy your Railway URL (e.g., https://tradingagents-prod.up.railway.app)"
echo "2. 📱 Update iOS app AppConfig.swift with the new URL"
echo "3. 🧪 Test iOS app with production API"
echo "4. 🍎 Submit to App Store"
echo

print_status "Helpful Railway Commands (install CLI first)"
echo

echo "Install Railway CLI:"
echo "  npm install -g @railway/cli"
echo
echo "Useful commands:"
echo "  railway login              # Login to Railway"
echo "  railway status             # Check deployment status"
echo "  railway logs               # View application logs"
echo "  railway shell              # Access deployment shell"
echo "  railway redeploy           # Redeploy current version"
echo

print_success "🎉 Deployment script completed!"
print_warning "📋 Don't forget to update the iOS app with your Railway URL!"

echo
echo "For detailed instructions, see: DEPLOYMENT_GUIDE.md"
echo "Good luck with your App Store submission! 🍎" 