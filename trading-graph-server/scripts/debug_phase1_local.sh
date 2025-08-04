#!/bin/bash

# Phase 1 Local Debug Script
# Validates Phase 1 optimizations against real traces and local execution
# Targets: 40% runtime reduction, 25% token reduction, A+ quality preservation

# Set strict error handling
set -euo pipefail

# Script configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PHASE1_TEST_SCRIPT="test_phase1_integration.py"
TRACE_ANALYZER="analyze_trace_production.sh"

# Test traces from analysis
TEST_TRACES=(
    "1f06f71b-e63b-6b63-9c01-4f264e9febb0"  # 126s runtime, 43K tokens
    "1f06f71c-8c4b-6277-b4bb-ae81915fbca2"  # 603s runtime, 54K tokens
    "1f06f72e-e6d0-6c4a-a6c8-8b898d6fdb16"  # 354s runtime, 52K tokens
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Change to script directory
cd "$SCRIPT_DIR"

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to display banner
display_banner() {
    echo ""
    print_color "$BLUE" "╔════════════════════════════════════════════════════════════════╗"
    print_color "$BLUE" "║           🚀 PHASE 1 OPTIMIZATION DEBUG SUITE 🚀               ║"
    print_color "$BLUE" "║                                                                ║"
    print_color "$BLUE" "║  Targets: 40% Runtime ↓ | 25% Tokens ↓ | A+ Quality ✓        ║"
    print_color "$BLUE" "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# Function to check environment
check_environment() {
    print_color "$CYAN" "🔧 Checking Environment..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_color "$GREEN" "  ✅ Python 3: $(python3 --version)"
    else
        print_color "$RED" "  ❌ Python 3 not found"
        exit 1
    fi
    
    # Check for .env file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
        print_color "$GREEN" "  ✅ Environment loaded from .env"
    else
        print_color "$YELLOW" "  ⚠️  No .env file found"
    fi
    
    # Check LANGSMITH_API_KEY
    if [ -z "${LANGSMITH_API_KEY:-}" ]; then
        print_color "$YELLOW" "  ⚠️  LANGSMITH_API_KEY not set (trace analysis will be skipped)"
        SKIP_TRACE_ANALYSIS=true
    else
        print_color "$GREEN" "  ✅ LANGSMITH_API_KEY found"
        SKIP_TRACE_ANALYSIS=false
    fi
    
    # Check required Python packages
    print_color "$CYAN" "\n🐍 Checking Python packages..."
    
    packages=("langsmith" "langchain" "asyncio" "tiktoken")
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            print_color "$GREEN" "  ✅ $pkg installed"
        else
            print_color "$YELLOW" "  ⚠️  Installing $pkg..."
            pip3 install "$pkg"
        fi
    done
    
    echo ""
}

# Function to run Phase 1 unit tests
run_unit_tests() {
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "$MAGENTA" "🧪 STEP 1: Running Phase 1 Component Unit Tests"
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Test async token optimizer
    print_color "$CYAN" "📝 Testing Async Token Optimizer..."
    if python3 "$PROJECT_ROOT/src/agent/utils/async_token_optimizer.py"; then
        print_color "$GREEN" "  ✅ Async token optimizer tests passed"
    else
        print_color "$RED" "  ❌ Async token optimizer tests failed"
        return 1
    fi
    
    # Test ultra-compressed prompts
    print_color "$CYAN" "\n📝 Testing Ultra-Compressed Prompts..."
    if python3 "$PROJECT_ROOT/src/agent/utils/ultra_prompt_templates.py"; then
        print_color "$GREEN" "  ✅ Ultra prompt templates tests passed"
    else
        print_color "$RED" "  ❌ Ultra prompt templates tests failed"
        return 1
    fi
    
    # Test parallel execution manager
    print_color "$CYAN" "\n📝 Testing Parallel Execution Manager..."
    if python3 "$PROJECT_ROOT/src/agent/utils/parallel_execution_manager.py"; then
        print_color "$GREEN" "  ✅ Parallel execution manager tests passed"
    else
        print_color "$RED" "  ❌ Parallel execution manager tests failed"
        return 1
    fi
    
    # Test Phase 1 integration
    print_color "$CYAN" "\n📝 Testing Phase 1 Integration Module..."
    if python3 "$PROJECT_ROOT/src/agent/utils/phase1_integration.py"; then
        print_color "$GREEN" "  ✅ Phase 1 integration tests passed"
    else
        print_color "$RED" "  ❌ Phase 1 integration tests failed"
        return 1
    fi
    
    echo ""
    print_color "$GREEN" "✅ All unit tests passed!"
    echo ""
}

# Function to run integration tests
run_integration_tests() {
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "$MAGENTA" "🔗 STEP 2: Running Phase 1 Integration Tests"
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ -f "$PHASE1_TEST_SCRIPT" ]; then
        python3 "$PHASE1_TEST_SCRIPT"
        return $?
    else
        print_color "$RED" "❌ Integration test script not found: $PHASE1_TEST_SCRIPT"
        return 1
    fi
}

# Function to analyze traces
analyze_traces() {
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "$MAGENTA" "📊 STEP 3: Analyzing Real LangSmith Traces"
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ "$SKIP_TRACE_ANALYSIS" = true ]; then
        print_color "$YELLOW" "⚠️  Skipping trace analysis (no API key)"
        return 0
    fi
    
    # Analyze each test trace
    for trace_id in "${TEST_TRACES[@]}"; do
        print_color "$CYAN" "🔍 Analyzing trace: $trace_id"
        
        if [ -f "$TRACE_ANALYZER" ]; then
            # Run trace analysis with summary format
            if bash "$TRACE_ANALYZER" "$trace_id" -f summary; then
                print_color "$GREEN" "  ✅ Trace analyzed successfully"
            else
                print_color "$RED" "  ❌ Trace analysis failed"
            fi
        else
            print_color "$YELLOW" "  ⚠️  Trace analyzer not found, using Python directly"
            python3 analyze_langsmith_trace_optimized.py "$trace_id" --format summary
        fi
        
        echo ""
    done
}

# Function to run performance validation
run_performance_validation() {
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "$MAGENTA" "📈 STEP 4: Performance Validation"
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Run a simple performance benchmark
    python3 << EOF
import json
import os
from pathlib import Path

# Load test results if available
test_report = None
reports = sorted(Path('.').glob('phase1_test_report_*.json'), reverse=True)
if reports:
    with open(reports[0], 'r') as f:
        test_report = json.load(f)

print("📊 Phase 1 Performance Summary")
print("=" * 50)

if test_report:
    metrics = test_report.get('aggregate_metrics', {})
    print(f"Token Reduction:   {metrics.get('avg_token_reduction', 0):.1%}")
    print(f"Runtime Reduction: {metrics.get('avg_runtime_reduction', 0):.1%}")
    print(f"Quality Score:     {metrics.get('avg_quality_score', 0):.2f}")
    print("-" * 50)
    
    # Check against targets
    targets_met = {
        "Token": metrics.get('avg_token_reduction', 0) >= 0.25,
        "Runtime": metrics.get('avg_runtime_reduction', 0) >= 0.40,
        "Quality": metrics.get('avg_quality_score', 0) >= 0.95
    }
    
    print("Target Achievement:")
    for metric, met in targets_met.items():
        status = "✅ PASS" if met else "❌ FAIL"
        print(f"  {metric}: {status}")
    
    overall = all(targets_met.values())
    print("-" * 50)
    print(f"Overall: {'✅ ALL TARGETS MET' if overall else '❌ TARGETS NOT MET'}")
else:
    print("No test report found. Run integration tests first.")

print("=" * 50)
EOF
}

# Function to generate final report
generate_final_report() {
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_color "$MAGENTA" "📄 FINAL REPORT"
    print_color "$MAGENTA" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Create summary report
    REPORT_FILE="phase1_debug_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "PHASE 1 OPTIMIZATION DEBUG REPORT"
        echo "================================="
        echo "Generated: $(date)"
        echo ""
        echo "Components Tested:"
        echo "  - Async Token Optimizer"
        echo "  - Ultra-Compressed Prompts"
        echo "  - Parallel Execution Manager"
        echo "  - Phase 1 Integration"
        echo ""
        echo "Test Results:"
        
        # Check for test report
        if ls phase1_test_report_*.json 1> /dev/null 2>&1; then
            latest_report=$(ls -t phase1_test_report_*.json | head -1)
            python3 -c "
import json
with open('$latest_report', 'r') as f:
    data = json.load(f)
    print(f'  Tests Passed: {data[\"tests_passed\"]}/{data[\"tests_total\"]}')
    print(f'  Success Rate: {data[\"success_rate\"]:.1%}')
    metrics = data.get('aggregate_metrics', {})
    print(f'  Token Reduction: {metrics.get(\"avg_token_reduction\", 0):.1%}')
    print(f'  Runtime Reduction: {metrics.get(\"avg_runtime_reduction\", 0):.1%}')
    print(f'  Quality Score: {metrics.get(\"avg_quality_score\", 0):.2f}')
"
        else
            echo "  No test results found"
        fi
        
        echo ""
        echo "Trace Analysis Results:"
        if [ "$SKIP_TRACE_ANALYSIS" = true ]; then
            echo "  Skipped (no API key)"
        else
            echo "  Analyzed ${#TEST_TRACES[@]} traces"
            echo "  See trace_analysis_reports/ for details"
        fi
        
    } > "$REPORT_FILE"
    
    print_color "$GREEN" "✅ Debug report saved to: $REPORT_FILE"
    echo ""
    
    # Display report
    cat "$REPORT_FILE"
}

# Main execution
main() {
    display_banner
    check_environment
    
    # Track overall success
    ALL_PASSED=true
    
    # Run tests
    if ! run_unit_tests; then
        ALL_PASSED=false
    fi
    
    if ! run_integration_tests; then
        ALL_PASSED=false
    fi
    
    # Analyze traces (optional)
    analyze_traces
    
    # Validate performance
    run_performance_validation
    
    # Generate final report
    generate_final_report
    
    # Final status
    echo ""
    if [ "$ALL_PASSED" = true ]; then
        print_color "$GREEN" "✅ PHASE 1 VALIDATION COMPLETE - ALL TESTS PASSED!"
    else
        print_color "$RED" "❌ PHASE 1 VALIDATION FAILED - SEE ERRORS ABOVE"
        exit 1
    fi
}

# Run main function
main