#!/bin/bash

# 🚀 Phase 0 Deployment Validation Script
# Validates that Phase 1 optimizations are properly deployed and functioning

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
VALIDATION_LOG="$SCRIPT_DIR/phase0_validation_$TIMESTAMP.log"

echo -e "${BLUE}🚀 Phase 0 Deployment Validation Script${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "📂 Project Root: $PROJECT_ROOT"
echo -e "📝 Validation Log: $VALIDATION_LOG"
echo ""

# Redirect all output to log file as well
exec > >(tee -a "$VALIDATION_LOG")
exec 2>&1

# Track validation results
VALIDATION_PASSED=true
FAILURES=()

# Function to check a validation item
check_validation() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    echo -e "${CYAN}Checking: $description${NC}"
    
    if eval "$command"; then
        echo -e "${GREEN}   ✅ PASS: $description${NC}"
    else
        echo -e "${RED}   ❌ FAIL: $description${NC}"
        VALIDATION_PASSED=false
        FAILURES+=("$description")
    fi
    echo ""
}

# Function to check if optimized graph is being used
check_graph_initialization() {
    echo -e "${PURPLE}=== Phase 1: Graph Initialization Check ===${NC}"
    
    # Check if OptimizedGraphBuilder is imported
    if grep -q "OptimizedGraphBuilder" "$PROJECT_ROOT/src/agent/graph/__init__.py"; then
        echo -e "${GREEN}   ✅ OptimizedGraphBuilder is imported in __init__.py${NC}"
    else
        echo -e "${RED}   ❌ OptimizedGraphBuilder NOT imported in __init__.py${NC}"
        echo -e "${YELLOW}   📋 Required change: Add 'from .optimized_setup import OptimizedGraphBuilder' to __init__.py${NC}"
        VALIDATION_PASSED=false
        FAILURES+=("OptimizedGraphBuilder not imported")
    fi
    
    # Check if GraphSetup uses OptimizedGraphBuilder
    if grep -q "OptimizedGraphBuilder as GraphSetup" "$PROJECT_ROOT/src/agent/graph/__init__.py"; then
        echo -e "${GREEN}   ✅ GraphSetup aliased to OptimizedGraphBuilder${NC}"
    else
        echo -e "${YELLOW}   ⚠️  GraphSetup may not be using OptimizedGraphBuilder${NC}"
    fi
    echo ""
}

# Function to check Phase 1 components
check_phase1_components() {
    echo -e "${PURPLE}=== Phase 2: Phase 1 Components Check ===${NC}"
    
    # Check AsyncTokenOptimizer
    check_validation "AsyncTokenOptimizer exists" \
        "test -f '$PROJECT_ROOT/src/agent/utils/async_token_optimizer.py'" \
        "File exists"
    
    # Check UltraPromptTemplates
    check_validation "UltraPromptTemplates exists" \
        "test -f '$PROJECT_ROOT/src/agent/utils/ultra_prompt_templates.py'" \
        "File exists"
    
    # Check ParallelExecutionManager
    check_validation "ParallelExecutionManager exists" \
        "test -f '$PROJECT_ROOT/src/agent/utils/parallel_execution_manager.py'" \
        "File exists"
    
    # Check Phase1Integration
    check_validation "Phase1Integration exists" \
        "test -f '$PROJECT_ROOT/src/agent/utils/phase1_integration.py'" \
        "File exists"
}

# Function to test component functionality
test_components() {
    echo -e "${PURPLE}=== Phase 3: Component Functionality Tests ===${NC}"
    
    # Create a test script
    cat > "$SCRIPT_DIR/test_phase0_components.py" << 'EOF'
#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_components():
    results = {"passed": 0, "failed": 0, "errors": []}
    
    # Test 1: AsyncTokenOptimizer
    try:
        from src.agent.utils.async_token_optimizer import AsyncTokenOptimizer
        optimizer = AsyncTokenOptimizer()
        tokens = await optimizer.count_tokens_async("Test prompt for validation")
        if tokens > 0:
            print("✅ AsyncTokenOptimizer: Working (counted {} tokens)".format(tokens))
            results["passed"] += 1
        else:
            print("❌ AsyncTokenOptimizer: Failed to count tokens")
            results["failed"] += 1
    except Exception as e:
        print("❌ AsyncTokenOptimizer: Error - {}".format(str(e)))
        results["failed"] += 1
        results["errors"].append(str(e))
    
    # Test 2: UltraPromptTemplates
    try:
        from src.agent.utils.ultra_prompt_templates import UltraPromptTemplates
        template = UltraPromptTemplates.get_template("market")
        if template and template.reduction_percentage >= 70:
            print("✅ UltraPromptTemplates: Working ({:.1f}% reduction)".format(template.reduction_percentage))
            results["passed"] += 1
        else:
            print("❌ UltraPromptTemplates: Insufficient reduction")
            results["failed"] += 1
    except Exception as e:
        print("❌ UltraPromptTemplates: Error - {}".format(str(e)))
        results["failed"] += 1
        results["errors"].append(str(e))
    
    # Test 3: ParallelExecutionManager
    try:
        from src.agent.utils.parallel_execution_manager import ParallelExecutionManager
        manager = ParallelExecutionManager(max_workers=4)
        
        async def test_agent(state):
            await asyncio.sleep(0.1)
            return {"result": "success"}
        
        agents = {"test1": test_agent, "test2": test_agent}
        result, stats = await manager.execute_agents_parallel(agents, {})
        
        if stats.speedup_factor > 1.5:
            print("✅ ParallelExecutionManager: Working ({:.1f}x speedup)".format(stats.speedup_factor))
            results["passed"] += 1
        else:
            print("❌ ParallelExecutionManager: Insufficient speedup")
            results["failed"] += 1
    except Exception as e:
        print("❌ ParallelExecutionManager: Error - {}".format(str(e)))
        results["failed"] += 1
        results["errors"].append(str(e))
    
    # Test 4: Phase1Integration
    try:
        from src.agent.utils.phase1_integration import Phase1Optimizer
        optimizer = Phase1Optimizer()
        print("✅ Phase1Optimizer: Initialized successfully")
        results["passed"] += 1
    except Exception as e:
        print("❌ Phase1Optimizer: Error - {}".format(str(e)))
        results["failed"] += 1
        results["errors"].append(str(e))
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_components())
    print("\n📊 Component Test Summary:")
    print("   Passed: {}".format(results["passed"]))
    print("   Failed: {}".format(results["failed"]))
    
    if results["failed"] > 0:
        print("\n❌ Errors encountered:")
        for error in results["errors"]:
            print("   - {}".format(error))
        sys.exit(1)
    else:
        print("\n✅ All component tests passed!")
        sys.exit(0)
EOF

    # Run the test
    echo -e "${CYAN}Running component functionality tests...${NC}"
    if python3 "$SCRIPT_DIR/test_phase0_components.py"; then
        echo -e "${GREEN}   ✅ Component tests passed${NC}"
    else
        echo -e "${RED}   ❌ Component tests failed${NC}"
        VALIDATION_PASSED=false
        FAILURES+=("Component functionality tests")
    fi
    echo ""
}

# Function to check configuration
check_configuration() {
    echo -e "${PURPLE}=== Phase 4: Configuration Check ===${NC}"
    
    # Create a config checker script
    cat > "$SCRIPT_DIR/check_phase0_config.py" << 'EOF'
#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.agent.dataflows.config import get_config
    config = get_config()
    
    # Check optimization flags
    optimizations = {
        'enable_phase1_optimizations': config.get('enable_phase1_optimizations', False),
        'enable_async_tokens': config.get('enable_async_tokens', False),
        'enable_ultra_prompts': config.get('enable_ultra_prompts', False),
        'enable_parallel_execution': config.get('enable_parallel_execution', False),
        'max_parallel_agents': config.get('max_parallel_agents', 1)
    }
    
    print("📋 Current Configuration:")
    for key, value in optimizations.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    # Check if all optimizations are enabled
    all_enabled = all([
        optimizations['enable_phase1_optimizations'],
        optimizations['enable_async_tokens'],
        optimizations['enable_ultra_prompts'],
        optimizations['enable_parallel_execution'],
        optimizations['max_parallel_agents'] >= 4
    ])
    
    if all_enabled:
        print("\n✅ All Phase 1 optimizations are enabled in config!")
        sys.exit(0)
    else:
        print("\n❌ Some optimizations are not enabled in config!")
        print("\n📝 Required configuration:")
        print(json.dumps({
            'enable_phase1_optimizations': True,
            'enable_async_tokens': True,
            'enable_ultra_prompts': True,
            'enable_parallel_execution': True,
            'max_parallel_agents': 4
        }, indent=2))
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error checking configuration: {e}")
    sys.exit(1)
EOF

    # Run the config check
    echo -e "${CYAN}Checking configuration settings...${NC}"
    if python3 "$SCRIPT_DIR/check_phase0_config.py"; then
        echo -e "${GREEN}   ✅ Configuration properly set${NC}"
    else
        echo -e "${RED}   ❌ Configuration needs updating${NC}"
        VALIDATION_PASSED=false
        FAILURES+=("Configuration settings")
    fi
    echo ""
}

# Function to run a quick performance test
run_performance_test() {
    echo -e "${PURPLE}=== Phase 5: Performance Validation ===${NC}"
    
    # Create a performance test script
    cat > "$SCRIPT_DIR/test_phase0_performance.py" << 'EOF'
#!/usr/bin/env python3
import sys
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

async def test_performance():
    try:
        from src.agent.utils.phase1_integration import Phase1Optimizer
        from src.agent.utils.ultra_prompt_templates import UltraPromptTemplates
        
        optimizer = Phase1Optimizer()
        
        # Create mock agents
        async def mock_agent(name):
            async def agent(state):
                await asyncio.sleep(0.5)
                return {f"{name}_report": f"Test report for {name}"}
            return agent
        
        # Test with 4 agents
        agents = {}
        for agent_type in ["market", "news", "social", "fundamentals"]:
            agents[f"{agent_type}_analyst"] = {
                "function": await mock_agent(agent_type),
                "original_prompt": UltraPromptTemplates.get_template(agent_type).original_prompt if hasattr(UltraPromptTemplates, 'get_template') else "Test prompt"
            }
        
        test_state = {"company_of_interest": "TEST"}
        
        # Run with optimizations
        start_time = time.time()
        result, metrics = await optimizer.optimize_and_execute_agents(agents, test_state)
        end_time = time.time()
        
        runtime = end_time - start_time
        
        print("📊 Performance Test Results:")
        print(f"   Runtime: {runtime:.2f}s")
        print(f"   Token Reduction: {metrics.token_reduction:.1%}")
        print(f"   Runtime Reduction: {metrics.runtime_reduction:.1%}")
        print(f"   Quality Score: {metrics.quality_score:.2f}")
        print(f"   Success Rate: {metrics.success_rate:.1%}")
        
        # Check if targets are met
        targets_met = (
            metrics.token_reduction >= 0.25 and
            metrics.runtime_reduction >= 0.40 and
            metrics.quality_score >= 0.95
        )
        
        if targets_met:
            print("\n✅ Phase 1 performance targets MET!")
            return True
        else:
            print("\n❌ Phase 1 performance targets NOT met!")
            return False
            
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_performance())
    sys.exit(0 if success else 1)
EOF

    # Run the performance test
    echo -e "${CYAN}Running performance validation test...${NC}"
    if python3 "$SCRIPT_DIR/test_phase0_performance.py"; then
        echo -e "${GREEN}   ✅ Performance targets met${NC}"
    else
        echo -e "${RED}   ❌ Performance targets not met${NC}"
        VALIDATION_PASSED=false
        FAILURES+=("Performance validation")
    fi
    echo ""
}

# Main validation flow
echo -e "${CYAN}Starting Phase 0 deployment validation...${NC}"
echo ""

# Run all validation checks
check_graph_initialization
check_phase1_components
test_components
check_configuration
run_performance_test

# Summary
echo -e "${PURPLE}=== Validation Summary ===${NC}"
echo ""

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED!${NC}"
    echo -e "${GREEN}Phase 1 optimizations are ready for production deployment.${NC}"
    echo ""
    echo -e "${CYAN}Next Steps:${NC}"
    echo "1. Deploy to staging environment"
    echo "2. Run load tests with production-like data"
    echo "3. Monitor metrics closely"
    echo "4. Deploy to production with gradual rollout"
else
    echo -e "${RED}❌ VALIDATION FAILED!${NC}"
    echo ""
    echo -e "${RED}Failed checks:${NC}"
    for failure in "${FAILURES[@]}"; do
        echo -e "   - $failure"
    done
    echo ""
    echo -e "${YELLOW}Required Actions:${NC}"
    echo "1. Update src/agent/graph/__init__.py to import OptimizedGraphBuilder"
    echo "2. Ensure all Phase 1 optimization flags are enabled in config"
    echo "3. Fix any component errors identified above"
    echo "4. Re-run this validation script"
fi

echo ""
echo -e "${BLUE}Validation log saved to: $VALIDATION_LOG${NC}"
echo ""

# Cleanup temporary test scripts
rm -f "$SCRIPT_DIR/test_phase0_components.py"
rm -f "$SCRIPT_DIR/check_phase0_config.py"
rm -f "$SCRIPT_DIR/test_phase0_performance.py"

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = true ]; then
    exit 0
else
    exit 1
fi