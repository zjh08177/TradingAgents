#!/bin/bash
# Claude command wrapper for /trace:analyze

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Change to project root
cd "$PROJECT_ROOT"

# Run the Python command
python3 "$SCRIPT_DIR/trace_analyze.py" "$@"