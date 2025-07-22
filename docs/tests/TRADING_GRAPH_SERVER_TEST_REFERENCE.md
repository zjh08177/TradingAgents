# Trading Graph Server Test Reference

## Overview
This document consolidates test-related information for the trading-graph-server LangGraph implementation. While test scripts have been removed for project cleanup, this document preserves essential testing context and graph validation approaches.

## Test Implementation History

### LangGraph Testing Suite (Removed)
Previously implemented comprehensive testing for the LangGraph trading workflow:

#### 1. Integration Testing
- **Test Scope**: End-to-end graph execution validation
- **Features Tested**:
  - Complete trading analysis workflow
  - Agent coordination and message passing
  - Graph state management
  - Node execution order validation
- **Components**: All trading agents, research managers, risk management

#### 2. Unit Testing
- **Test Scope**: Individual component validation
- **Coverage**:
  - Configuration management
  - Graph setup and initialization
  - Node-level functionality
  - Error handling and recovery

#### 3. Graph Workflow Testing
- **Test Scope**: LangGraph-specific functionality
- **Features Tested**:
  - State transitions between nodes
  - Conditional routing logic
  - Agent communication patterns
  - Parallel execution capabilities

## Preserved Testing Assets

### Test Data
- **Location**: `src/tradingagents/dataflows/data_cache/`
- **File**: `TEST-YFin-data-2010-06-30-2025-06-30.csv`
- **Purpose**: Reference dataset for Yahoo Finance data validation
- **Usage**: Enables testing without external API dependencies

### Configuration
- **Test Environment**: Development graph configuration
- **Mock Data Support**: Cached market data for consistent testing
- **Graph Validation**: Workflow execution validation

## Testing Approach Documentation

### 1. Graph Execution Testing
```python
# Example test pattern used:
async def test_trading_graph_execution():
    from agent.graph import create_trading_graph
    
    graph = create_trading_graph()
    
    # Test with sample ticker
    initial_state = {"ticker": "TSLA"}
    result = await graph.ainvoke(initial_state)
    
    # Validate graph execution
    assert "final_trade_decision" in result
    assert result["analysis_complete"] is True
```

### 2. Node Integration Testing
```python
# Example node test pattern:
async def test_analysis_nodes():
    # Test market analyst node
    # Test news analyst node  
    # Test fundamentals analyst node
    # Test research manager coordination
    # Test risk management evaluation
    # Test final trading decision
```

### 3. Configuration Testing
```python
# Example configuration test:
def test_graph_configuration():
    # Validate all required environment variables
    # Test API key configuration
    # Verify graph node connections
    # Check state schema validation
```

## Key Test Scenarios

### Critical Test Cases
1. **Complete Analysis Workflow**: Full TSLA analysis from start to finish
2. **Agent Coordination**: Multi-agent information sharing and synthesis
3. **Risk Management Integration**: Risk assessment and trade recommendation
4. **Error Recovery**: Handling API failures and invalid inputs
5. **State Management**: Graph state persistence and transitions

### Graph-Specific Testing
- **Node Execution Order**: Verify correct workflow sequence
- **State Transitions**: Validate state changes between nodes
- **Conditional Logic**: Test decision routing based on analysis results
- **Parallel Processing**: Multiple analysis streams coordination

## LangGraph Workflow Validation

### Graph Structure Testing
```python
# Example graph validation:
def test_graph_structure():
    graph = create_trading_graph()
    
    # Verify all nodes are present
    expected_nodes = [
        "market_analyst",
        "news_analyst", 
        "fundamentals_analyst",
        "research_manager",
        "risk_manager",
        "trader"
    ]
    
    # Validate graph connections
    # Check for proper entry and exit points
```

### State Schema Validation
```python
# Example state validation:
def test_state_schema():
    # Validate initial state structure
    # Test intermediate state updates
    # Verify final state completeness
    # Check state type consistency
```

## Validation Commands

### Graph Health Check
```bash
# Server health validation
curl http://localhost:8000/health
```

### Analysis Execution Test
```bash
# Test full analysis workflow
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}'
```

### Graph Development Testing
```bash
# Local graph testing (if test scripts were recreated)
cd trading-graph-server
python -m pytest tests/ -v
```

## Graph Architecture Notes

### Agent Workflow
1. **Market Analyst**: Technical analysis and price patterns
2. **News Analyst**: Sentiment analysis from news sources
3. **Fundamentals Analyst**: Financial metrics and ratios
4. **Research Manager**: Synthesis of analyst findings
5. **Risk Manager**: Risk assessment and position sizing
6. **Trader**: Final trading decision and execution plan

### Graph Features
- **Conditional Routing**: Dynamic workflow based on analysis results
- **State Persistence**: Maintains analysis context across nodes
- **Error Handling**: Graceful degradation on node failures
- **Parallel Execution**: Concurrent analyst operations where possible

## Notes for Future Testing

### Re-implementation Guidelines
If test scripts need to be recreated:
1. Focus on end-to-end graph workflow validation
2. Test individual node functionality and integration
3. Validate state management and transitions
4. Include error scenarios and recovery testing
5. Test with both live and cached data

### Critical Dependencies
- All environment variables must be configured
- External API connectivity (OpenAI, Finnhub, SERPER)
- Proper graph configuration and node setup
- State schema validation

### Development Environment
- Use cached test data for consistent results
- Mock external APIs for isolated testing
- Validate graph structure before execution testing
- Test both synchronous and asynchronous execution paths

## Related Documentation
- LangGraph official documentation for graph testing patterns
- Agent implementation details in `src/tradingagents/agents/`
- Graph configuration in `src/agent/graph.py`
- State management documentation 