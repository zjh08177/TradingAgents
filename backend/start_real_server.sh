#!/bin/bash

# Real Trading-Graph-Server Restart Script
# This script terminates ALL existing server processes and starts the real trading-graph-server

set -e  # Exit on any error

echo "🔄 Real Trading-Graph-Server Restart Script"
echo "============================================"
echo "📅 Started at: $(date)"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
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

# Function to kill processes by pattern with enhanced search
kill_processes_enhanced() {
    local pattern=$1
    local description=$2
    
    echo "🔍 Searching for $description..."
    
    # Method 1: ps aux with grep
    pids1=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}' 2>/dev/null || true)
    
    # Method 2: pgrep if available
    pids2=""
    if command -v pgrep >/dev/null 2>&1; then
        pids2=$(pgrep -f "$pattern" 2>/dev/null || true)
    fi
    
    # Method 3: pkill dry run to see what would be killed
    if command -v pkill >/dev/null 2>&1; then
        pkill_matches=$(pkill -f "$pattern" -l 2>/dev/null | awk '{print $1}' || true)
    fi
    
    # Combine all PIDs and remove duplicates
    all_pids=$(echo "$pids1 $pids2 $pkill_matches" | tr ' ' '\n' | sort -u | grep -E '^[0-9]+$' || true)
    
    if [ -n "$all_pids" ]; then
        echo "💀 Found $description processes: $all_pids"
        for pid in $all_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Killing PID $pid..."
                kill -TERM "$pid" 2>/dev/null || true
                sleep 0.5
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            fi
        done
        sleep 1
        print_success "Killed $description"
    else
        print_success "No $description found"
    fi
}

# Function to kill processes on specific ports
kill_ports() {
    local ports=("$@")
    
    for port in "${ports[@]}"; do
        echo "🔍 Checking port $port..."
        
        # Method 1: lsof (most reliable)
        if command -v lsof >/dev/null 2>&1; then
            pids=$(lsof -ti :$port 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo "💀 Killing processes on port $port: $pids"
                echo "$pids" | xargs kill -TERM 2>/dev/null || true
                sleep 1
                # Force kill if still running
                echo "$pids" | xargs kill -KILL 2>/dev/null || true
                print_success "Port $port cleared"
            else
                print_success "Port $port is free"
            fi
        else
            # Method 2: netstat fallback
            if command -v netstat >/dev/null 2>&1; then
                pids=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$' || true)
                if [ -n "$pids" ]; then
                    echo "💀 Killing processes on port $port: $pids"
                    echo "$pids" | xargs kill -TERM 2>/dev/null || true
                    sleep 1
                    echo "$pids" | xargs kill -KILL 2>/dev/null || true
                    print_success "Port $port cleared"
                else
                    print_success "Port $port is free"
                fi
            else
                print_warning "Cannot check port $port (no lsof or netstat)"
            fi
        fi
    done
}

# Function to verify environment
check_environment() {
    print_step "ENV" "Checking environment"
    
    # Check if we're in the right directory
    if [ ! -f "api.py" ]; then
        if [ -f "backend/api.py" ]; then
            cd backend
            print_success "Changed to backend directory"
        else
            print_error "Cannot find api.py. Please run from project root or backend directory."
            exit 1
        fi
    fi
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        print_error "Python3 not found"
        exit 1
    fi
    print_success "Python3 found: $(python3 --version)"
    
    # Check required files
    local required_files=("api.py" "run_api.py" "requirements.txt")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file not found: $file"
            exit 1
        fi
    done
    print_success "All required files found"
}

# Function to setup environment variables
setup_environment() {
    print_step "1" "Setting up environment variables"
    
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
    fi
    
    # Check for required API keys
    local required_keys=("OPENAI_API_KEY")
    local optional_keys=("FINNHUB_API_KEY" "SERPAPI_API_KEY" "SERPER_API_KEY")
    
    echo "🔑 Checking API keys..."
    for key in "${required_keys[@]}"; do
        if [ -z "${!key}" ]; then
            print_error "Required environment variable $key is not set"
            echo "   Please set it in your .env file or export it:"
            echo "   export $key='your-key-here'"
            exit 1
        else
            print_success "$key is set"
        fi
    done
    
    for key in "${optional_keys[@]}"; do
        if [ -z "${!key}" ]; then
            print_warning "$key is not set (optional)"
        else
            print_success "$key is set"
        fi
    done
}

# Function to kill all server processes
kill_all_servers() {
    print_step "2" "Terminating all existing server processes"
    
    # Kill by process names/patterns
    kill_processes_enhanced "uvicorn" "uvicorn servers"
    kill_processes_enhanced "run_api.py" "run_api.py processes"
    kill_processes_enhanced "api.py" "api.py processes"
    kill_processes_enhanced "TradingAgents" "TradingAgents processes"
    kill_processes_enhanced "trading.*server" "trading server processes"
    kill_processes_enhanced "fastapi" "FastAPI processes"
    kill_processes_enhanced "gunicorn" "Gunicorn processes"
    
    # Kill by ports
    kill_ports 8000 8001 8080 3000 5000
    
    print_success "All server processes terminated"
}

# Function to wait and verify cleanup
verify_cleanup() {
    print_step "3" "Verifying cleanup"
    
    echo "⏳ Waiting for cleanup to complete..."
    sleep 3
    
    # Final verification
    local remaining_procs=$(ps aux | grep -E "(uvicorn|api\.py|run_api)" | grep -v grep | wc -l)
    if [ "$remaining_procs" -gt 0 ]; then
        print_warning "Some processes may still be running"
        ps aux | grep -E "(uvicorn|api\.py|run_api)" | grep -v grep || true
    else
        print_success "All processes cleaned up"
    fi
    
    # Check if ports are really free
    if command -v lsof >/dev/null 2>&1; then
        if lsof -ti :8000 >/dev/null 2>&1; then
            print_error "Port 8000 is still occupied!"
            lsof -i :8000
            exit 1
        fi
    fi
    
    print_success "Port 8000 is available"
}

# Function to start the real server
start_server() {
    print_step "4" "Starting Real Trading-Graph-Server"
    
    # Activate virtual environment if it exists
    local venv_activated=false
    
    # Try different virtual environment locations
    local venv_paths=(
        "../.venv/bin/activate"
        ".venv/bin/activate" 
        "venv/bin/activate"
        "../venv/bin/activate"
        "../../.venv/bin/activate"
    )
    
    for venv_path in "${venv_paths[@]}"; do
        if [ -f "$venv_path" ]; then
            print_info "Activating virtual environment at $venv_path..."
            source "$venv_path"
            venv_activated=true
            print_success "Virtual environment activated"
            break
        fi
    done
    
    if [ "$venv_activated" = false ]; then
        print_warning "No virtual environment found, using system Python"
        print_warning "This may cause import errors. Consider activating your venv first."
    fi
    
    # Check dependencies
    print_info "Checking dependencies..."
    if ! python3 -c "import uvicorn, fastapi" 2>/dev/null; then
        print_warning "Installing/updating dependencies..."
        pip install -r requirements.txt
    fi
    print_success "Dependencies verified"
    
    # Display server information
    echo
    echo -e "${CYAN}🚀 Real Trading-Graph-Server Information${NC}"
    echo -e "${CYAN}=======================================${NC}"
    echo -e "${GREEN}📍 Server URL: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}🔄 Health Check: http://localhost:8000/health${NC}"
    echo -e "${GREEN}📊 Analysis Endpoint: POST http://localhost:8000/analyze${NC}"
    echo -e "${GREEN}📡 Streaming Endpoint: GET http://localhost:8000/analyze/stream${NC}"
    echo
    echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
    echo -e "${YELLOW}💡 Server logs will appear below${NC}"
    echo
    echo -e "${CYAN}========================================${NC}"
    
    # Start the server with enhanced configuration
    export TRADINGAGENTS_API_HOST="0.0.0.0"
    export TRADINGAGENTS_API_PORT="8000"
    
    # Method 1: Try run_api.py (recommended)
    if [ -f "run_api.py" ]; then
        print_success "Starting server using run_api.py..."
        exec python3 run_api.py
    else
        # Method 2: Direct uvicorn fallback
        print_info "run_api.py not found, using direct uvicorn..."
        exec python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload --log-level info
    fi
}

# Main execution
main() {
    # Trap Ctrl+C
    trap 'echo -e "\n${YELLOW}👋 Server stopped by user${NC}"; exit 0' INT
    
    check_environment
    setup_environment
    kill_all_servers
    verify_cleanup
    start_server
}

# Run main function
main "$@" 