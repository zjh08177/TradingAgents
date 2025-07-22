# Backend Test Reference

## Overview
This document consolidates test-related information for the TradingAgents backend system. While test scripts have been removed for project cleanup, this document preserves essential testing context and approaches.

## Test Implementation History

### Comprehensive Test Suite (Removed)
Previously implemented comprehensive testing covering:

#### 1. Main System Testing
- **Test Scope**: Full `main.py` system testing
- **Features Tested**: 
  - Multiple configuration scenarios
  - Agent execution timing
  - Parallel execution detection
  - Detailed execution logging
- **Output**: Results saved to `test_results/` directory
- **Custom Components**: TestLogger class, TrackedTradingAgentsGraph

#### 2. FastAPI Endpoint Testing  
- **Test Scope**: Complete API testing (`run_api.py`)
- **Endpoints Covered**:
  - Health endpoint (`/health`)
  - Root endpoint (`/`)
  - Analysis endpoint (`/analyze`)
  - Streaming endpoint (`/analyze/stream`)
- **Test Types**: Single requests, parallel requests, error scenarios

#### 3. Specialized Component Tests
- **Risk Management**: Isolated risk manager testing
- **SERPER Integration**: API integration testing with mocks
- **Parallel Execution**: Multi-threaded analysis testing
- **Tool Call Fixes**: LLM tool calling validation

## Preserved Testing Assets

### Data Assets
- **Location**: `backend/tradingagents/dataflows/data_cache/`
- **File**: `TEST-YFin-data-2010-06-30-2025-06-30.csv`
- **Purpose**: Test dataset for Yahoo Finance data validation
- **Retention Reason**: Reference data for integration validation

### Configuration & Validation
- **Server Restart Utilities**: Preserved in `SERVER_RESTART_GUIDE.md`
- **API Validation Scripts**: Available via `verify_api.sh`
- **Setup Validation**: Available via `check_setup.py`

## Testing Approach Documentation

### 1. System Integration Testing
```python
# Example test pattern used:
async def test_full_analysis_flow():
    # Initialize trading graph
    # Execute analysis with real ticker
    # Validate agent execution order
    # Check parallel execution
    # Verify output format
```

### 2. API Testing Patterns
```python
# Example API test pattern:
async def test_analyze_endpoint():
    # POST to /analyze with ticker
    # Validate response structure
    # Check execution timing
    # Verify streaming capability
```

### 3. Mock Testing Strategy
- **SERPER API**: Mock responses for news/search data
- **LLM Calls**: Mock OpenAI responses for predictable testing
- **Market Data**: Use cached/test datasets

## Key Test Scenarios

### Critical Test Cases
1. **TSLA Analysis**: Standard test case for Tesla stock
2. **Error Handling**: Invalid tickers, API failures
3. **Parallel Processing**: Multiple simultaneous requests
4. **Agent Coordination**: Risk management vs trading decisions
5. **Streaming Responses**: Real-time analysis updates

### Performance Benchmarks
- **Single Analysis**: ~30-60 seconds
- **Parallel Analyses**: Support for 3-5 concurrent requests
- **Memory Usage**: Monitor for memory leaks in long-running tests

## Validation Commands

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Analysis Test
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}'
```

### Server Verification
```bash
./verify_api.sh
```

## Notes for Future Testing

### Re-implementation Guidelines
If test scripts need to be recreated:
1. Focus on end-to-end analysis workflows
2. Test agent coordination and parallel execution
3. Validate all API endpoints
4. Include error scenario testing
5. Test with both real and mock data

### Critical Dependencies
- Ensure all environment variables are set
- Validate API key functionality
- Test network connectivity for external APIs
- Verify LangGraph execution flow

## Related Documentation
- `SERVER_RESTART_GUIDE.md`: Server management procedures
- `DEPLOYMENT_GUIDE.md`: Production deployment testing
- `API Documentation`: Endpoint specifications and usage 