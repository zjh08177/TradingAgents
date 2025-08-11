# Agent Data Collection Separation Guide

## Clear Agent Responsibilities

### Market Analyst - Technical & Trading Data Specialist
**Exclusive Responsibility**: All market trading and technical data

**Collects**:
- ✅ Price data (OHLCV) across all timeframes
- ✅ Volume data and volume profiles
- ✅ Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- ✅ Options flow and derivatives data
- ✅ Market microstructure (order book, bid-ask spreads)
- ✅ Cross-asset technical data (bonds, currencies, commodities)
- ✅ Market breadth and sentiment indicators (VIX, A/D ratios)

**Does NOT Collect**:
- ❌ Financial statements
- ❌ Earnings data
- ❌ Company fundamental metrics (P/E, ROE, etc.)
- ❌ Analyst estimates or price targets
- ❌ Company profile information

### Fundamentals Analyst - Company Financial Data Specialist
**Exclusive Responsibility**: All company-specific financial and business data

**Collects**:
- ✅ Financial statements (income, balance sheet, cash flow)
- ✅ Earnings data and history
- ✅ Company metrics and ratios (P/E, P/B, ROE, margins)
- ✅ Analyst estimates and consensus
- ✅ Price targets and recommendations
- ✅ Company profile and business description
- ✅ Insider transactions
- ✅ Peer company comparisons

**Does NOT Collect**:
- ❌ Price/volume data
- ❌ Technical indicators
- ❌ Options flow data
- ❌ Market microstructure
- ❌ Cross-asset correlations

### News Analyst - News Data Specialist
**Exclusive Responsibility**: All news articles and headlines

**Collects**:
- ✅ News articles from 4,500+ sources
- ✅ Headlines and summaries
- ✅ News sentiment scores
- ✅ Breaking news alerts

**Does NOT Collect**:
- ❌ Social media posts
- ❌ Price data
- ❌ Financial statements

### Social Media Analyst - Social Sentiment Specialist
**Exclusive Responsibility**: All social media and forum data

**Collects**:
- ✅ Reddit posts and comments
- ✅ Twitter/X posts
- ✅ Social sentiment analysis
- ✅ Retail trader sentiment

**Does NOT Collect**:
- ❌ News articles
- ❌ Price data
- ❌ Financial statements

## Data Pipeline Architecture

```
Layer 1: Data Collection (Specialized Agents)
┌─────────────────┬──────────────────┬──────────────┬────────────────┐
│ Market Analyst  │ Fundamentals     │ News Analyst │ Social Analyst │
│ - Prices        │ - Financials     │ - Articles   │ - Reddit       │
│ - Technical     │ - Earnings       │ - Headlines  │ - Twitter      │
│ - Options       │ - Metrics        │ - Sentiment  │ - Forums       │
│ - Microstructure│ - Estimates      │              │                │
└─────────────────┴──────────────────┴──────────────┴────────────────┘
                                ↓
Layer 2: Research & Analysis (Downstream Agents)
┌─────────────────────────────────────────────────────────────────────┐
│                     Research Agents                                 │
│ - Technical Analysis (uses Market data)                             │
│ - Fundamental Analysis (uses Fundamentals data)                     │
│ - Sentiment Analysis (uses News + Social data)                      │
│ - Integrated Analysis (combines all data types)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Principles

1. **No Overlap**: Each agent has exclusive responsibility for their data domain
2. **Clear Boundaries**: Well-defined scope prevents duplication
3. **Specialized Collection**: Each agent optimizes for their specific data type
4. **Standardized Output**: All agents output clean, structured JSON
5. **Research Layer Separation**: Analysis happens in downstream agents, not collection agents

## Data Request Examples

### Example 1: Technical Analysis Research
```yaml
request:
  from: Technical Analysis Research Agent
  to: Market Analyst
  data_needed:
    - 5 years of daily OHLCV
    - RSI, MACD, Bollinger Bands
    - Options flow last 30 days
    - VIX levels
```

### Example 2: Fundamental Analysis Research
```yaml
request:
  from: Fundamental Analysis Research Agent
  to: Fundamentals Analyst
  data_needed:
    - 5 years of financial statements
    - Current P/E, P/B ratios
    - Analyst estimates
    - Peer comparison metrics
```

### Example 3: Integrated Analysis Research
```yaml
request:
  from: Integrated Research Agent
  to: [Market Analyst, Fundamentals Analyst, News Analyst]
  data_needed:
    market_analyst:
      - Current price and volume
      - Technical indicators
    fundamentals_analyst:
      - Latest earnings
      - P/E ratio
    news_analyst:
      - Recent headlines
      - News sentiment
```

## Implementation Guidelines

1. **API Segregation**: Each agent uses different APIs
   - Market Analyst: Alpha Vantage, Yahoo Finance (price data)
   - Fundamentals Analyst: Finnhub (fundamentals endpoints only)
   - News Analyst: Serper/Google News
   - Social Analyst: Reddit API, Twitter API

2. **No Cross-Domain Calls**: Agents should never call APIs outside their domain

3. **Validation Rules**: Each agent validates they're not collecting out-of-scope data

4. **Error Messages**: Clear errors if wrong agent is asked for wrong data type

## Quality Assurance

### Boundary Testing
- Test that Market Analyst rejects requests for earnings data
- Test that Fundamentals Analyst rejects requests for price data
- Verify no overlap in collected data across agents

### Integration Testing
- Test research agents can request from correct collection agents
- Verify data format compatibility across agents
- Test error handling for incorrect data requests

This separation ensures efficient, specialized data collection with no duplication or confusion about responsibilities.