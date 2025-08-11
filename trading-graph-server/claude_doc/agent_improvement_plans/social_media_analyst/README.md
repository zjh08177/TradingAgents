# Social Media Analyst Documentation

## Current Documentation Structure

### Active Documents (Use These)

1. **`current_status_analysis.md`** - Complete analysis of current implementation
   - Current failures and root causes
   - Clear role definition (social media only, no news)
   - Performance metrics and gaps

2. **`improvement_plan_atomic.md`** - Actionable improvement plan
   - Atomic, self-testable subtasks
   - Week-by-week implementation schedule
   - Follows KISS, YAGNI, DRY principles

### Archived Documents (Reference Only)

These documents contain research and ideas but are superseded by the active documents above:

- `improvement_plan.md` - Original comprehensive plan (overly complex)
- `technical_implementation.md` - Technical details (violates YAGNI with speculative features)
- `social-sentiment-strategy.md` - Strategy document (includes news which is out of scope)
- `social-sentiment-implementation.py` - Implementation code (premature, needs basic fixes first)
- `social-sentiment-integration-guide.md` - Integration guide (cart before horse)

## Key Decisions

### Role Clarity
**Social Media Analyst**: Analyzes Reddit, StockTwits, Twitter/X discussions
**NOT Responsible For**: News articles, press releases, financial reports (News Analyst's job)

### Implementation Principles
1. **KISS**: Fix basic tools first, add complexity only when needed
2. **YAGNI**: No account rotation, scraping armies, or complex architectures yet
3. **DRY**: Don't duplicate news analyst functionality

### Priority Order
1. Fix Reddit division by zero error (CRITICAL)
2. Implement basic StockTwits API (HIGH)
3. Remove news tools from social analyst (HIGH)
4. Add simple caching and rate limiting (MEDIUM)
5. Improve prompt engineering (HIGH)

## Quick Start

```bash
# 1. Fix Reddit tool
vim src/agent/dataflows/interface.py
# Add: if len(posts) == 0: return "No Reddit discussions found"

# 2. Implement StockTwits
vim src/agent/dataflows/interface_new_tools.py
# Replace mock with real API call

# 3. Update toolkit
vim src/agent/factories/toolkit_factory.py
# Remove get_stock_news_openai from social toolkit

# 4. Test
python -c "from interface import get_reddit_company_news; print(get_reddit_company_news('AAPL', '2024-01-01', 7, 5))"
```

## Testing

Each task in `improvement_plan_atomic.md` includes specific test commands:

```bash
# Test Reddit fix
pytest tests/test_social_tools.py::test_reddit_error_handling

# Test StockTwits
pytest tests/test_social_tools.py::test_stocktwits_real_data

# Test full workflow
pytest tests/test_social_analyst.py::test_full_workflow
```

## Success Criteria

- [ ] Reddit tool doesn't crash on empty results
- [ ] StockTwits returns real sentiment data
- [ ] Social analyst uses no news tools
- [ ] Execution completes in <20 seconds
- [ ] Error rate <5%

## Archive Note

The archived documents contain valuable research but propose overly complex solutions:
- Twitter scraping with account rotation (YAGNI)
- Multiple fallback systems (premature optimization)
- News sentiment integration (wrong analyst)

These ideas may be revisited after basic functionality is working.