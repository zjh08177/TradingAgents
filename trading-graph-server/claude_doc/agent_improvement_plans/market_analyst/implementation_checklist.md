# Market Analyst Simplified Refactor - Implementation Checklist

## Quick Start Guide

This checklist provides a day-by-day implementation plan for the simplified market analyst refactor. Check off items as you complete them.

---

## Pre-Implementation (Day 0)

### Setup
- [ ] Create feature branch: `git checkout -b feature/simplified-market-analyst`
- [ ] Create new directory structure:
  ```bash
  mkdir -p src/agent/data
  mkdir -p src/agent/calculations  
  mkdir -p src/agent/nodes
  mkdir -p tests/agent/data
  mkdir -p tests/agent/calculations
  mkdir -p tests/agent/nodes
  ```
- [ ] Set up test framework: `pip install pytest pytest-asyncio pytest-mock`
- [ ] Create feature flag in `.env`: `USE_SIMPLE_ANALYST=false`

---

## Week 1: Core Implementation

### Day 1-2: Minimal Data Fetcher

#### Day 1: Create MarketDataFetcher
- [ ] Create `src/agent/data/market_data_fetcher.py`
- [ ] Implement `MarketDataFetcher` class (200 lines max)
- [ ] Add input validation for ticker symbols
- [ ] Implement Yahoo Finance HTTP client
- [ ] Add simple error handling
- [ ] Remove all environment detection code

#### Day 2: Test MarketDataFetcher
- [ ] Create `tests/agent/data/test_market_data_fetcher.py`
- [ ] Write test for valid ticker fetch
- [ ] Write test for invalid ticker handling
- [ ] Write test for network error handling
- [ ] Mock httpx responses
- [ ] Achieve >90% test coverage

**Validation Checkpoint**:
- [ ] Can fetch AAPL data successfully?
- [ ] Does invalid ticker return error?
- [ ] Is code <200 lines?
- [ ] Zero pandas/numpy imports?

### Day 3-4: Minimal Calculator

#### Day 3: Create IndicatorCalculator
- [ ] Create `src/agent/calculations/indicator_calculator.py`
- [ ] Implement `IndicatorCalculator` class (300 lines max)
- [ ] Add SMA calculations (5, 20, 50 periods)
- [ ] Add RSI calculation (simplified)
- [ ] Add trend determination logic
- [ ] Add signal generation logic
- [ ] Use pure Python only (no pandas/numpy)

#### Day 4: Test IndicatorCalculator
- [ ] Create `tests/agent/calculations/test_indicator_calculator.py`
- [ ] Test SMA calculations with known values
- [ ] Test RSI calculation edge cases
- [ ] Test trend determination logic
- [ ] Test signal generation
- [ ] Achieve >90% test coverage

**Validation Checkpoint**:
- [ ] Do calculations match expected values?
- [ ] Is code <300 lines?
- [ ] Zero external dependencies?
- [ ] All functions <20 lines?

### Day 5: Minimal Node Interface

#### Morning: Create Node
- [ ] Create `src/agent/nodes/market_analyst_node.py`
- [ ] Implement `create_market_analyst_node` function
- [ ] Integrate MarketDataFetcher
- [ ] Integrate IndicatorCalculator
- [ ] Add report generation
- [ ] Keep under 150 lines

#### Afternoon: Test Node
- [ ] Create `tests/agent/nodes/test_market_analyst_node.py`
- [ ] Test complete flow with mocked components
- [ ] Test error handling
- [ ] Test report generation
- [ ] Integration test with real components

**Validation Checkpoint**:
- [ ] Does node work in LangGraph?
- [ ] Is code <150 lines?
- [ ] Clean separation of concerns?
- [ ] <2 second execution time?

---

## Week 2: Integration & Rollout

### Day 6-7: Integration Testing

#### Day 6: End-to-End Testing
- [ ] Create `tests/integration/test_market_analyst_flow.py`
- [ ] Test complete flow: ticker → data → calculations → report
- [ ] Test with multiple tickers (AAPL, MSFT, GOOGL)
- [ ] Test error cases (invalid ticker, network failure)
- [ ] Benchmark performance (<2 seconds requirement)

#### Day 7: LangGraph Integration
- [ ] Update `src/agent/graph/setup.py` to use feature flag
- [ ] Add conditional import based on `USE_SIMPLE_ANALYST`
- [ ] Test in local LangGraph environment
- [ ] Test in Docker container
- [ ] Verify no pandas import errors

**Validation Checkpoint**:
- [ ] Works in LangGraph without errors?
- [ ] Performance <2 seconds?
- [ ] Memory usage <50MB?

### Day 8-9: Documentation & Migration

#### Day 8: Documentation
- [ ] Create API documentation in `docs/api/market_analyst.md`
- [ ] Add usage examples
- [ ] Document configuration options
- [ ] Create migration guide from old to new
- [ ] Update README with new architecture

#### Day 9: Migration Plan
- [ ] Create rollback plan
- [ ] Set up monitoring for new implementation
- [ ] Create performance comparison dashboard
- [ ] Document feature differences
- [ ] Plan gradual rollout strategy

**Validation Checkpoint**:
- [ ] Is documentation complete?
- [ ] Can another developer understand the code?
- [ ] Is rollback plan tested?

### Day 10: Deployment Preparation

#### Morning: Final Testing
- [ ] Run full test suite
- [ ] Performance benchmarks
- [ ] Memory profiling
- [ ] Load testing with concurrent requests

#### Afternoon: Deployment
- [ ] Deploy to dev environment with flag enabled
- [ ] Monitor for 2 hours
- [ ] Check error rates
- [ ] Verify performance metrics
- [ ] Create PR for review

**Final Validation**:
- [ ] All tests passing?
- [ ] Performance targets met?
- [ ] Code review approved?
- [ ] Ready for staging deployment?

---

## Post-Implementation

### Week 3: Gradual Rollout

#### Staging Environment
- [ ] Enable for 10% of requests
- [ ] Monitor for 24 hours
- [ ] Increase to 50%
- [ ] Monitor for 24 hours
- [ ] Full staging rollout

#### Production Environment
- [ ] Enable for 1% of requests
- [ ] Monitor for 48 hours
- [ ] Gradual increase: 5% → 10% → 25% → 50% → 100%
- [ ] Monitor error rates at each stage
- [ ] Ready to rollback if needed

### Week 4: Cleanup

- [ ] Remove old implementation files
- [ ] Remove mock pandas classes
- [ ] Remove unnecessary dependencies
- [ ] Update all documentation
- [ ] Close refactoring tickets

---

## Success Criteria Checklist

### Code Quality ✅
- [ ] Total lines < 700 (was 1,352)
- [ ] Each component < assigned line limit
- [ ] Zero pandas/numpy dependencies
- [ ] No environment-specific code
- [ ] All functions < 20 lines
- [ ] Cyclomatic complexity < 4

### Performance ✅
- [ ] Response time < 2 seconds
- [ ] Memory usage < 50MB
- [ ] CPU usage < 30%
- [ ] Zero memory leaks
- [ ] Handles 100 concurrent requests

### Testing ✅
- [ ] Unit test coverage > 90%
- [ ] Integration tests passing
- [ ] Performance tests passing
- [ ] LangGraph compatibility verified
- [ ] Error handling tested

### Documentation ✅
- [ ] API documentation complete
- [ ] Migration guide written
- [ ] Usage examples provided
- [ ] Architecture diagram updated
- [ ] Rollback plan documented

---

## Common Issues & Solutions

### Issue: Yahoo Finance API Changes
**Solution**: Update response parsing in `_parse_response` method

### Issue: Timeout Errors
**Solution**: Increase timeout from 10 to 15 seconds

### Issue: Missing Indicators
**Solution**: Only essential indicators included by design

### Issue: Performance Regression
**Solution**: Check for blocking operations in async code

### Issue: Test Failures
**Solution**: Update mocked responses to match new structure

---

## Emergency Rollback

If critical issues arise:

1. **Immediate Rollback**:
   ```bash
   export USE_SIMPLE_ANALYST=false
   kubectl rollout restart deployment/trading-agent
   ```

2. **Revert Code**:
   ```bash
   git revert HEAD
   git push origin main
   ```

3. **Notify Team**:
   - Post in #engineering channel
   - Create incident report
   - Schedule postmortem

---

## Contact for Help

- **Architecture Questions**: Review `simplified_refactor_architecture.md`
- **Implementation Details**: Check `refactoring_implementation_guide.md`
- **Original Analysis**: See `comprehensive_implementation_analysis.md`

**Remember**: Simplicity is the goal. If something seems complex, it probably is. Simplify it!