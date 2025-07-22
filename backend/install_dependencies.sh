#!/bin/bash

# TradingAgents Dependency Installation Script
# Ensures all required dependencies are installed in the virtual environment

set -e  # Exit on any error

echo "🔧 TradingAgents Dependency Installation"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to find and activate virtual environment
activate_venv() {
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
    print_info "Please create a virtual environment first:"
    print_info "  python3 -m venv .venv"
    print_info "  source .venv/bin/activate"
    exit 1
}

# Function to check if module can be imported
check_module() {
    local module=$1
    if python -c "import $module" 2>/dev/null; then
        print_success "$module is installed"
        return 0
    else
        print_warning "$module is NOT installed"
        return 1
    fi
}

# Main execution
main() {
    # Change to backend directory if needed
    if [ ! -f "requirements.txt" ]; then
        if [ -f "backend/requirements.txt" ]; then
            cd backend
            print_info "Changed to backend directory"
        else
            print_error "Cannot find requirements.txt"
            exit 1
        fi
    fi
    
    # Activate virtual environment
    activate_venv
    
    # Upgrade pip
    print_info "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install requirements
    print_info "Installing requirements from requirements.txt..."
    pip install -r requirements.txt
    
    print_success "Requirements installation completed"
    
    # Validate critical modules
    echo
    print_info "Validating critical dependencies..."
    
    critical_modules=(
        "fastapi"
        "uvicorn"
        "langchain_openai"
        "langchain_anthropic" 
        "langchain_google_genai"
        "langgraph"
        "pandas"
        "yfinance"
        "requests"
    )
    
    failed_modules=()
    
    for module in "${critical_modules[@]}"; do
        # Convert dash to underscore for import
        import_name=${module//-/_}
        if ! check_module "$import_name"; then
            failed_modules+=("$module")
        fi
    done
    
    echo
    if [ ${#failed_modules[@]} -eq 0 ]; then
        print_success "All critical dependencies are installed!"
        echo
        print_info "You can now start the server with:"
        print_info "  ./start_real_server.sh"
        print_info "  or"
        print_info "  ./quick_restart.sh"
    else
        print_error "Some dependencies failed to install:"
        for module in "${failed_modules[@]}"; do
            echo "  - $module"
        done
        echo
        print_info "Try installing them individually:"
        for module in "${failed_modules[@]}"; do
            echo "  pip install $module"
        done
        exit 1
    fi
}

# Run main function
main "$@" 