#!/bin/bash

# Claude Code command handler for /trace:analyze
# This script bridges Claude commands to the actual trace analyzer

# Get the base directory
BASE_DIR="/Users/bytedance/Documents/TradingAgents"
SCRIPTS_DIR="$BASE_DIR/trading-graph-server/scripts"
ANALYZER_SCRIPT="$SCRIPTS_DIR/analyze_trace_production.sh"

# Change to scripts directory
cd "$SCRIPTS_DIR" || exit 1

# Parse arguments
TRACE_ID=""
PROJECT=""
FORMAT="summary"
VERBOSE=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT="--project $2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            if [ -z "$TRACE_ID" ]; then
                TRACE_ID="$1"
            fi
            shift
            ;;
    esac
done

# If no trace ID provided, list recent traces
if [ -z "$TRACE_ID" ]; then
    echo "📋 No trace ID provided. Listing recent traces..."
    exec "$ANALYZER_SCRIPT" --list-recent
fi

# Build command
CMD="$ANALYZER_SCRIPT $TRACE_ID"
[ -n "$PROJECT" ] && CMD="$CMD $PROJECT"
CMD="$CMD --format $FORMAT"
[ -n "$VERBOSE" ] && CMD="$CMD $VERBOSE"

# Execute the analyzer
exec $CMD