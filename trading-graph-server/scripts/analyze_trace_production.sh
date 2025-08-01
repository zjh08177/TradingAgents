#!/bin/bash

# LangSmith Trace Analyzer - Production Shell Script
# Analyzes any LangSmith trace with comprehensive error handling and reporting

# Set strict error handling
set -euo pipefail

# Script configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="analyze_langsmith_trace_optimized.py"
DEFAULT_TRACE_ID="1f06d636-ab7b-6768-8fcd-6ce23dce7772"
DEFAULT_PROJECT="trading-agent-graph"
OUTPUT_DIR="trace_analysis_reports"
DEFAULT_MAX_SIZE_KB=2048  # Default max size in KB

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
cd "$SCRIPT_DIR"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to display usage
usage() {
    cat << EOF
$(print_color "$BLUE" "🔍 LangSmith Trace Analyzer - Optimized Production Version")
$(print_color "$BLUE" "==========================================================")

Usage: $0 [TRACE_ID] [OPTIONS]

Arguments:
    TRACE_ID          The LangSmith trace ID to analyze
                      Default: $DEFAULT_TRACE_ID

Options:
    -p, --project     LangSmith project name (default: $DEFAULT_PROJECT)
    -o, --output      Custom output file path
    -f, --format      Output format: summary, json, both (default: both)
    -v, --verbose     Enable verbose logging
    -s, --max-size    Maximum file size in KB (default: $DEFAULT_MAX_SIZE_KB)
    -h, --help        Display this help message
    --list-recent     List recent traces from the project
    --env-check       Check environment setup

Examples:
    # Analyze default trace with summary
    $0

    # Analyze specific trace
    $0 1f06d636-ab7b-6768-8fcd-6ce23dce7772

    # Analyze trace from specific project
    $0 abc123 -p my-project

    # Save to custom location with JSON output only
    $0 abc123 -o /tmp/analysis.json -f json

    # Analyze with 1MB file size limit
    $0 abc123 --max-size 1024

    # List recent traces
    $0 --list-recent

    # Check environment
    $0 --env-check

Performance Features:
    - Size-optimized reports (under 2MB by default)
    - Enhanced analysis with 7 categories
    - Performance regression detection
    - Priority-based recommendations

EOF
}

# Function to check environment
check_environment() {
    print_color "$BLUE" "🔧 Checking Environment..."
    echo ""
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_color "$GREEN" "✅ Python 3 found: $(python3 --version)"
    else
        print_color "$RED" "❌ Python 3 is required but not installed"
        exit 1
    fi
    
    # Check for .env file and load it
    if [ -f "../.env" ]; then
        set -a
        source ../.env
        set +a
        print_color "$GREEN" "✅ Loaded environment from ../.env"
    elif [ -f ".env" ]; then
        set -a
        source .env
        set +a
        print_color "$GREEN" "✅ Loaded environment from .env"
    fi
    
    # Check API key
    if [ -z "${LANGSMITH_API_KEY:-}" ]; then
        print_color "$RED" "❌ LANGSMITH_API_KEY not found in environment"
        echo ""
        echo "Please set your API key:"
        echo "  export LANGSMITH_API_KEY=your_api_key_here"
        echo "Or add it to your .env file"
        exit 1
    else
        print_color "$GREEN" "✅ LANGSMITH_API_KEY found: ${LANGSMITH_API_KEY:0:20}..."
    fi
    
    # Check Python script
    if [ -f "$PYTHON_SCRIPT" ]; then
        print_color "$GREEN" "✅ Analyzer script found: $PYTHON_SCRIPT"
    else
        print_color "$RED" "❌ Analyzer script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    # Check langsmith package
    if python3 -c "import langsmith" 2>/dev/null; then
        print_color "$GREEN" "✅ LangSmith Python package installed"
    else
        print_color "$YELLOW" "⚠️  LangSmith package not found. Installing..."
        pip3 install langsmith
    fi
    
    echo ""
}

# Function to list recent traces
list_recent_traces() {
    print_color "$BLUE" "📋 Listing Recent Traces..."
    
    python3 << EOF
import os
from langsmith import Client
from datetime import datetime

api_key = os.getenv('LANGSMITH_API_KEY')
if not api_key:
    print("❌ LANGSMITH_API_KEY not set")
    exit(1)

try:
    client = Client(api_key=api_key)
    
    # List projects first
    print("\n📁 Available Projects:")
    projects = list(client.list_projects())
    for i, proj in enumerate(projects[:5]):
        print(f"  {i+1}. {proj.name} (ID: {proj.id})")
    
    # Try to list recent runs
    print("\n📊 Recent Traces (last 10):")
    
    # Get runs from the default project
    project_name = "${DEFAULT_PROJECT}"
    print(f"From project: {project_name}")
    
    try:
        runs = list(client.list_runs(
            project_name=project_name,
            execution_order=1,  # Only top-level runs
            limit=10
        ))
        
        if runs:
            for run in runs:
                status_icon = "✅" if run.status == "success" else "❌"
                time_str = run.start_time.strftime("%Y-%m-%d %H:%M") if run.start_time else "Unknown"
                print(f"  {status_icon} {run.id}")
                print(f"     Name: {run.name}")
                print(f"     Time: {time_str}")
                print(f"     Status: {run.status}")
                print()
        else:
            print("  No recent traces found")
            
    except Exception as e:
        print(f"  Error listing runs: {e}")
        
except Exception as e:
    print(f"❌ Error: {e}")
EOF
}

# Parse command line arguments
TRACE_ID=""
PROJECT="$DEFAULT_PROJECT"
OUTPUT=""
FORMAT="both"
VERBOSE=""
MAX_SIZE_KB="$DEFAULT_MAX_SIZE_KB"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --env-check)
            check_environment
            print_color "$GREEN" "✅ Environment check complete!"
            exit 0
            ;;
        --list-recent)
            check_environment
            list_recent_traces
            exit 0
            ;;
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -s|--max-size)
            MAX_SIZE_KB="$2"
            shift 2
            ;;
        -*)
            print_color "$RED" "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$TRACE_ID" ]; then
                TRACE_ID="$1"
            else
                print_color "$RED" "Unexpected argument: $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Use default trace ID if none provided
if [ -z "$TRACE_ID" ]; then
    TRACE_ID="$DEFAULT_TRACE_ID"
fi

# Check environment
check_environment

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Display analysis information
print_color "$BLUE" "🚀 Starting LangSmith Trace Analysis (Optimized)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Trace ID: $TRACE_ID"
echo "📁 Project: $PROJECT"
echo "📊 Format: $FORMAT"
echo "📏 Max Size: ${MAX_SIZE_KB}KB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build command
CMD="python3 $PYTHON_SCRIPT $TRACE_ID"
CMD="$CMD --project '$PROJECT'"
CMD="$CMD --format $FORMAT"
CMD="$CMD --max-size $MAX_SIZE_KB"

if [ ! -z "$OUTPUT" ]; then
    CMD="$CMD --output '$OUTPUT'"
fi

if [ ! -z "$VERBOSE" ]; then
    CMD="$CMD $VERBOSE"
fi

# Run the analyzer
eval $CMD
EXIT_CODE=$?

# Handle results
if [ $EXIT_CODE -eq 0 ]; then
    print_color "$GREEN" "\n✅ Analysis completed successfully!"
    
    # If no custom output specified, show where the report was saved
    if [ -z "$OUTPUT" ] && [ "$FORMAT" != "summary" ]; then
        LATEST_REPORT=$(ls -t trace_analysis_optimized_${TRACE_ID}_*.json 2>/dev/null | head -1)
        if [ ! -z "$LATEST_REPORT" ]; then
            # Move to output directory
            mv "$LATEST_REPORT" "$OUTPUT_DIR/"
            print_color "$BLUE" "📄 Report saved to: $OUTPUT_DIR/$LATEST_REPORT"
            
            # Show file size
            FILE_SIZE=$(ls -lh "$OUTPUT_DIR/$LATEST_REPORT" | awk '{print $5}')
            echo "   Size: $FILE_SIZE"
            
            # Check if size is under limit
            FILE_SIZE_KB=$(du -k "$OUTPUT_DIR/$LATEST_REPORT" | cut -f1)
            if [ "$FILE_SIZE_KB" -le "$MAX_SIZE_KB" ]; then
                print_color "$GREEN" "   ✅ Size within limit (${FILE_SIZE_KB}KB <= ${MAX_SIZE_KB}KB)"
            else
                print_color "$YELLOW" "   ⚠️  Size exceeds limit (${FILE_SIZE_KB}KB > ${MAX_SIZE_KB}KB)"
            fi
        fi
    fi
else
    print_color "$RED" "\n❌ Analysis failed with exit code $EXIT_CODE"
    echo "Check the error messages above for details."
    exit $EXIT_CODE
fi

# Provide next steps
echo ""
print_color "$YELLOW" "🔍 Next Steps:"
echo "  - Review the analysis report for insights and recommendations"
echo "  - Check performance metrics against targets (120s runtime, 40K tokens)"
echo "  - Monitor for performance regressions between traces"
echo "  - Use --max-size to control report file size (default: 2MB)"
echo "  - Run with --verbose for detailed logging"
echo "  - Use --list-recent to find other traces to analyze"
echo ""

print_color "$BLUE" "📊 Analysis Features:"
echo "  - Enhanced analysis with 7 comprehensive categories"
echo "  - Size-optimized reports (under ${MAX_SIZE_KB}KB)"
echo "  - Performance regression detection"
echo "  - Priority-based recommendations"
echo "  - Quality grading system (A+ to D)"
echo ""