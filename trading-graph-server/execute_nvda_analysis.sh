#!/bin/bash
# Auto-generated execution script for NVDA analysis
# Created by restart_server_enhanced.sh

echo "🎯 Executing Trading Graph Analysis for NVDA"
echo "=========================================="

SCRIPT_FLAGS=""
if [[ "false" == "true" ]]; then
    SCRIPT_FLAGS="--skip-tests"
fi

# Execute the analysis
echo "🚀 Running: ./debug_local.sh NVDA $SCRIPT_FLAGS"
./debug_local.sh NVDA $SCRIPT_FLAGS

echo ""
echo "✅ Analysis complete for NVDA"
echo "📂 Check debug_logs/ for detailed results"
