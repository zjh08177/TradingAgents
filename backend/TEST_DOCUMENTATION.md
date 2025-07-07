# TradingAgents Test Suite Documentation

## Overview

This document describes the comprehensive test suite created for the TradingAgents system, covering both `main.py` and the FastAPI implementation (`run_api.py`).

## Test Files Created

### 1. `test_main_comprehensive.py`
**Purpose**: Comprehensive test for main.py with continuous logging and parallel execution verification.

**Features**:
- Tests multiple configurations
- Tracks agent execution times
- Detects and logs parallel execution
- Provides detailed execution logs
- Saves results to `test_results/` directory

**Key Capabilities**:
- Custom `TestLogger` class for enhanced logging
- `TrackedTradingAgentsGraph` for message tracking
- Parallel execution detection
- Comprehensive validation of all required reports

### 2. `test_api_comprehensive.py`
**Purpose**: Tests all FastAPI endpoints including streaming and concurrent requests.

**Features**:
- Tests health check endpoint
- Tests root endpoint
- Tests synchronous `/analyze` endpoint
- Tests streaming `/analyze/stream` endpoint
- Tests parallel request handling
- Tests error handling

**Key Capabilities**:
- Automatic API server startup
- SSE (Server-Sent Events) stream parsing
- Parallel agent detection in streaming
- Comprehensive event tracking

### 3. `test_parallel_execution.py`
**Purpose**: Specifically verifies that agents execute in parallel when expected.

**Features**:
- `ParallelExecutionTracker` class
- Real-time parallel execution detection
- Timeline visualization
- Detailed execution summary

**Key Capabilities**:
- Tracks active agents in real-time
- Identifies parallel execution groups
- Creates execution timeline
- Saves parallel execution analysis

### 4. `test_main_simple.py`
**Purpose**: Simple test to verify basic main.py functionality.

**Features**:
- Basic import verification
- Simple propagation test
- Continuous progress logging
- Report validation

### 5. `run_all_tests.py`
**Purpose**: Test runner that executes all tests and provides a comprehensive summary.

**Features**:
- Automatic test discovery
- Individual test execution with timeout
- Comprehensive logging
- JSON summary generation

## Running the Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   # Create virtual environment (if needed)
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

2. **Set Environment Variables** (if using OpenAI):
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

### Running Individual Tests

1. **Test main.py comprehensively**:
   ```bash
   python3 test_main_comprehensive.py
   ```

2. **Test API comprehensively**:
   ```bash
   # Start the API server first (in a separate terminal)
   python3 run_api.py
   
   # Then run the test
   python3 test_api_comprehensive.py
   ```

3. **Test parallel execution**:
   ```bash
   python3 test_parallel_execution.py
   ```

4. **Simple main.py test**:
   ```bash
   python3 test_main_simple.py
   ```

### Running All Tests

```bash
python3 run_all_tests.py
```

This will:
- Check for available test files
- Run each test with a 5-minute timeout
- Generate a comprehensive summary
- Save logs to `test_results/`

## Test Output

### Log Files

All tests generate detailed logs in the `test_results/` directory:

- `main_test_YYYYMMDD_HHMMSS.log` - Main.py test logs
- `api_test_YYYYMMDD_HHMMSS.log` - API test logs
- `all_tests_YYYYMMDD_HHMMSS.log` - Combined test runner logs
- `test_summary.json` - JSON summary of all test results

### Parallel Execution Detection

The tests specifically track parallel execution. You should see output like:

```
🔄 PARALLEL EXECUTION DETECTED: ['market_analyst', 'social_analyst']
🔄 PARALLEL AGENTS: ['news_analyst', 'fundamentals_analyst']
```

### Continuous State Logging

Tests provide continuous updates:

```
📦 Chunk 1: Keys = ['messages']
🤖 Agent Active: MarketAnalyst
🔧 Tool Called: get_YFin_data_online
📄 MARKET_REPORT COMPLETED
✅ market_analyst completed in 5.23s
```

## Expected Results

### Successful Test Run

When all agents are working correctly, you should see:

1. **All reports generated**:
   - market_report
   - sentiment_report
   - news_report
   - fundamentals_report
   - investment_plan
   - trader_investment_plan
   - final_trade_decision

2. **Parallel execution detected**:
   - Multiple analysts running simultaneously
   - Bull and Bear researchers running in parallel

3. **Reasonable execution times**:
   - Total execution: 30-60 seconds
   - Individual agents: 5-20 seconds

### Common Issues and Solutions

1. **Missing Dependencies**:
   ```
   ModuleNotFoundError: No module named 'langchain_openai'
   ```
   **Solution**: Install all requirements using pip

2. **API Key Issues**:
   ```
   Error: Invalid API key
   ```
   **Solution**: Set correct API keys in environment variables

3. **Timeout Issues**:
   ```
   TIMEOUT - Test exceeded 5 minutes
   ```
   **Solution**: Check network connection and API availability

4. **No Parallel Execution Detected**:
   - Check if the graph configuration supports parallel execution
   - Verify LangGraph version supports streaming

## Interpreting Results

### Parallel Execution Summary

The parallel execution test provides detailed analysis:

```
PARALLEL EXECUTION SUMMARY
================================================================================
Total parallel groups detected: 3
Maximum agents running in parallel: 4

Parallel execution instances:
  1. [10:15:23.456] 2 agents: market_analyst, social_analyst
  2. [10:15:24.789] 4 agents: market_analyst, social_analyst, news_analyst, fundamentals_analyst
  3. [10:15:45.123] 2 agents: bull_researcher, bear_researcher
```

### API Streaming Events

The API test tracks streaming events:

```
📡 Streaming Events Summary:
  AAPL: 45 events
    - status: 2
    - agent_status: 18
    - report: 7
    - progress: 8
    - reasoning: 9
    - complete: 1
```

## Continuous Improvement

To improve the system based on test results:

1. **Monitor Execution Times**: Long-running agents may need optimization
2. **Check Parallel Efficiency**: Ensure parallel agents don't wait unnecessarily
3. **Validate Report Quality**: Ensure all reports contain meaningful content
4. **Review Error Logs**: Fix any recurring errors or warnings

## Conclusion

This comprehensive test suite ensures:
- All agents execute correctly
- Parallel execution works as designed
- API endpoints function properly
- System handles concurrent requests
- Continuous logging provides visibility

Run these tests regularly to maintain system health and catch regressions early.