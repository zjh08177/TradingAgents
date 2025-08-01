#!/bin/bash

# Enhanced Debug Script with Studio Validation
# Prevents pandas circular import and blocking I/O regressions

set -e  # Exit on any error

echo "🔧 Enhanced Trading Agents Debug & Validation"
echo "============================================="

# Store original directory
ORIGINAL_DIR=$(pwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Enhanced validation functions

validate_pandas_imports() {
    echo "🔍 Validating pandas imports (preventing circular import regression)..."
    
    # Check for problematic module-level pandas imports
    problematic_imports=$(find src -name "*.py" -exec grep -l "^import pandas\|^from pandas" {} \; 2>/dev/null || true)
    if [ -n "$problematic_imports" ]; then
        error "Found module-level pandas imports that could cause circular import:"
        echo "$problematic_imports"
        return 1
    fi
    
    # Test graph import works without blocking
    if uv run python3 -c "import sys; sys.path.append('src'); from agent import graph; print('Graph imports successfully')" >/dev/null 2>&1; then
        success "Pandas imports validation passed"
        return 0
    else
        error "Graph import failed - possible circular import issue"
        return 1
    fi
}

validate_type_hints() {
    echo "🔤 Validating type hints (preventing NameError regression)..."
    
    # Check for DataFrame/Series type hints without proper imports
    type_hint_issues=$(find src -name "*.py" -exec grep -Hn "-> DataFrame\|: DataFrame\|-> Series\|: Series" {} \; 2>/dev/null | grep -v "\"DataFrame\"\|'DataFrame'\|\"Series\"\|'Series'" || true)
    if [ -n "$type_hint_issues" ]; then
        error "Found non-string DataFrame/Series type hints that could cause NameError:"
        echo "$type_hint_issues"
        return 1
    fi
    
    success "Type hints validation passed"
    return 0
}

validate_blocking_io() {
    echo "🚫 Validating blocking I/O operations (preventing LangGraph Studio errors)..."
    
    # Check for module-level blocking calls that cause LangGraph Studio issues
    blocking_calls=$(find src -name "*.py" -exec grep -Hn "^load_dotenv\|^requests\." {} \; 2>/dev/null || true)
    if [ -n "$blocking_calls" ]; then
        error "Found module-level blocking I/O calls that could hang LangGraph Studio:"
        echo "$blocking_calls"
        warning "These should be moved inside functions or made lazy"
        return 1
    fi
    
    success "Blocking I/O validation passed"
    return 0
}

validate_langgraph_compatibility() {
    echo "🧪 Validating LangGraph Studio compatibility..."
    
    # Test if graph can be imported without timeouts/blocking
    if uv run python3 -c "
import sys
import signal
sys.path.append('src')

def timeout_handler(signum, frame):
    raise TimeoutError('Graph import timed out - possible blocking operation')

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)  # 10 second timeout

try:
    from agent import graph
    print('SUCCESS: Graph loads without blocking')
    signal.alarm(0)
except TimeoutError as e:
    print(f'ERROR: {e}')
    exit(1)
except Exception as e:
    print(f'ERROR: Graph import failed: {e}')
    exit(1)
" 2>/dev/null; then
        success "LangGraph Studio compatibility validated"
        return 0
    else
        error "Graph import failed or timed out - blocking operation detected"
        return 1
    fi
}

# Enhanced main logic with all validations

# Parse command line arguments
MODE="$1"

if [ "$MODE" = "imports-only" ]; then
    # Run import validations only
    validate_pandas_imports
    validate_type_hints
    validate_blocking_io
    echo "🎉 Import validation complete!"
elif [ "$MODE" = "full" ]; then
    # Run all validations including LangGraph compatibility
    validate_pandas_imports
    validate_type_hints 
    validate_blocking_io
    validate_langgraph_compatibility
    echo "🎉 Full validation complete!"
else
    # Default: Run core validations
    validate_pandas_imports
    validate_type_hints
    validate_blocking_io
    echo "🎉 Enhanced debug validation complete!"
    echo "💡 Use './debug_local.sh full' for complete LangGraph Studio testing"
fi

# Return to original directory
cd "$ORIGINAL_DIR" 