#!/bin/bash
# Auto-generated execution script for ETH analysis
# Created by restart_server_enhanced.sh

echo "🎯 Executing Trading Graph Analysis for ETH"
echo "=========================================="

SCRIPT_FLAGS=""
if [[ "false" == "true" ]]; then
    SCRIPT_FLAGS="--skip-tests"
fi

# Execute the analysis
echo "🚀 Running: ./debug_local.sh ETH $SCRIPT_FLAGS"
./debug_local.sh ETH $SCRIPT_FLAGS

echo ""
echo "✅ Analysis complete for ETH"
echo "📂 Check debug_logs/ for detailed results"
