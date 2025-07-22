#!/bin/bash

# Fix Dependencies and Start Server Script
# Comprehensive solution to resolve import errors and start the trading-graph-server

set -e  # Exit on any error

echo "🔧 TradingAgents Fix & Start Script"
echo "=================================="
echo "📅 Started at: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 Step $1: $2${NC}"
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

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to kill existing processes
kill_existing_servers() {
    print_step "1" "Killing existing server processes"
    
    pkill -f "uvicorn" 2>/dev/null || true
    pkill -f "run_api.py" 2>/dev/null || true
    pkill -f "api.py" 2>/dev/null || true
    
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    fi
    
    sleep 1
    print_success "Existing servers terminated"
}

# Function to find and activate virtual environment
activate_venv() {
    print_step "2" "Activating virtual environment"
    
    local venv_paths=(
        "../.venv/bin/activate"
        ".venv/bin/activate" 
        "venv/bin/activate"
        "../venv/bin/activate"
        "../../.venv/bin/activate"
    )
    
    for venv_path in "${venv_paths[@]}"; do
        if [ -f "$venv_path" ]; then
            print_info "Found virtual environment at $venv_path"
            source "$venv_path"
            print_success "Virtual environment activated"
            return 0
        fi
    done
    
    print_error "No virtual environment found!"
    print_info "Creating a new virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    print_success "New virtual environment created and activated"
}

# Function to install/update dependencies
install_dependencies() {
    print_step "3" "Installing/updating dependencies"
    
    # Upgrade pip first
    print_info "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install requirements
    print_info "Installing requirements..."
    pip install -r requirements.txt
    
    # Install additional langchain packages explicitly if they failed
    local critical_packages=(
        "langchain-anthropic"
        "langchain-google-genai" 
        "langchain-openai"
        "langgraph"
        "fastapi"
        "uvicorn[standard]"
    )
    
    for package in "${critical_packages[@]}"; do
        print_info "Ensuring $package is installed..."
        pip install "$package" --upgrade
    done
    
    print_success "Dependencies installation completed"
}

# Function to validate imports
validate_imports() {
    print_step "4" "Validating critical imports"
    
    local critical_modules=(
        "fastapi"
        "uvicorn" 
        "langchain_openai"
        "langchain_anthropic"
        "langchain_google_genai"
        "langgraph"
        "pandas"
        "yfinance"
    )
    
    local failed_modules=()
    
    for module in "${critical_modules[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            print_success "$module ✓"
        else
            print_warning "$module ✗"
            failed_modules+=("$module")
        fi
    done
    
    if [ ${#failed_modules[@]} -eq 0 ]; then
        print_success "All critical modules validated"
    else
        print_error "Some modules failed validation"
        for module in "${failed_modules[@]}"; do
            print_info "Attempting to fix $module..."
            pip install "${module//_/-}" --force-reinstall
        done
    fi
}

# Function to test API import
test_api_import() {
    print_step "5" "Testing API module import"
    
    if python -c "from api import app; print('API import successful')" 2>/dev/null; then
        print_success "API module imports successfully"
    else
        print_error "API module import failed"
        print_info "Checking specific import that failed..."
        
        # Try to identify the specific import issue
        python -c "
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    print('✅ TradingAgentsGraph import successful')
except ImportError as e:
    print(f'❌ TradingAgentsGraph import failed: {e}')
    
    # Try importing individual components
    try:
        from langchain_anthropic import ChatAnthropic
        print('✅ ChatAnthropic import successful')
    except ImportError as e:
        print(f'❌ ChatAnthropic import failed: {e}')
        
    try:
        from langchain_openai import ChatOpenAI
        print('✅ ChatOpenAI import successful')  
    except ImportError as e:
        print(f'❌ ChatOpenAI import failed: {e}')
" || true
        
        print_warning "Continuing despite import issues..."
    fi
}

# Function to setup environment variables
setup_environment() {
    print_step "6" "Setting up environment variables"
    
    # Load .env file if it exists
    if [ -f ".env" ]; then
        print_info "Loading environment from .env file"
        export $(grep -v '^#' .env | xargs)
        print_success "Environment loaded from .env"
    elif [ -f "../.env" ]; then
        print_info "Loading environment from ../.env file"
        export $(grep -v '^#' ../.env | xargs)
        print_success "Environment loaded from ../.env"
    else
        print_warning "No .env file found"
        print_info "Setting dummy API keys for testing..."
        export OPENAI_API_KEY="sk-test-dummy-key-for-testing"
        export FINNHUB_API_KEY="test-finnhub-key"
        export SERPAPI_API_KEY="test-serpapi-key"
        print_warning "Using dummy API keys - real analysis may not work"
    fi
    
    # Validate required keys
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY not set"
    else
        print_success "OPENAI_API_KEY is set"
    fi
}

# Function to start the server
start_server() {
    print_step "7" "Starting the trading-graph-server"
    
    # Display server information
    echo
    echo -e "${CYAN}🚀 Trading-Graph-Server Starting${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo -e "${GREEN}📍 Server URL: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}🔄 Health Check: http://localhost:8000/health${NC}"
    echo -e "${GREEN}📊 Analysis Endpoint: POST http://localhost:8000/analyze${NC}"
    echo
    echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
    echo -e "${YELLOW}💡 Server logs will appear below${NC}"
    echo
    echo -e "${CYAN}=================================${NC}"
    
    # Start the server
    if [ -f "run_api.py" ]; then
        print_success "Starting server using run_api.py..."
        exec python run_api.py
    else
        print_info "run_api.py not found, using direct uvicorn..."
        exec python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
    fi
}

# Main execution
main() {
    # Trap Ctrl+C
    trap 'echo -e "\n${YELLOW}👋 Server stopped by user${NC}"; exit 0' INT
    
    # Change to backend directory if needed
    if [ ! -f "api.py" ]; then
        if [ -f "backend/api.py" ]; then
            cd backend
            print_info "Changed to backend directory"
        else
            print_error "Cannot find api.py"
            exit 1
        fi
    fi
    
    kill_existing_servers
    activate_venv  
    install_dependencies
    validate_imports
    test_api_import
    setup_environment
    start_server
}

# Run main function
main "$@" 