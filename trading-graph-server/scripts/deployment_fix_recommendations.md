# Deployment Environment Fixes

## Issue 1: Market Agent - Pandas Not Available

### Problem
The market agent is falling back to pure-python implementation, calculating only 5 indicators instead of 130+.

### Root Cause
Missing dependencies in deployment:
- `pandas` 
- `pandas-ta`
- `pkg_resources` (part of setuptools)

### Solution
Update your deployment requirements or Dockerfile:

```bash
# In requirements.txt or pyproject.toml
pandas>=2.0.0
pandas-ta>=0.3.14b0
setuptools>=65.0.0
```

Or in Dockerfile:
```dockerfile
RUN pip install pandas pandas-ta setuptools
```

## Issue 2: Social Agent - Tool Call Failures

### Problem
All 3 social media tools (Reddit, Twitter, StockTwits) are failing in deployment.

### Root Cause
1. Missing `aiohttp` dependency for async HTTP requests
2. Type error in Twitter data fetching logic

### Solution

#### 1. Add missing dependency:
```bash
# In requirements.txt
aiohttp>=3.8.0
```

#### 2. Fix Twitter type comparison error:
The error `'>' not supported between instances of 'NoneType' and 'float'` suggests a comparison with None value.

Check and update the Twitter fetching code:
```python
# Before comparison, check for None
if value is not None and value > threshold:
    # process
```

## Issue 3: Environment Differences

### Local vs Deployment Environment

| Component | Local | Deployment | Action Needed |
|-----------|-------|------------|---------------|
| pandas | ✅ Installed | ❌ Missing | Install pandas |
| pandas-ta | ✅ Installed | ❌ Missing | Install pandas-ta |
| aiohttp | ✅ Installed | ❌ Missing | Install aiohttp |
| setuptools | ✅ Installed | ❌ Missing/Old | Update setuptools |

## Recommended Deployment Configuration

### Complete requirements.txt:
```txt
# Core dependencies
pandas>=2.0.0
pandas-ta>=0.3.14b0
aiohttp>=3.8.0
setuptools>=65.0.0

# Ensure these are also present
numpy>=1.24.0
httpx>=0.24.0
finnhub-python>=2.4.0
yfinance>=0.2.0
```

### Environment Variables Check:
Ensure all API keys are properly set in deployment:
- `FINNHUB_API_KEY`
- `SERPER_API_KEY`
- `OPENAI_API_KEY`
- `LANGSMITH_API_KEY`

### Docker Deployment Fix:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with no cache
RUN pip install --no-cache-dir -r requirements.txt

# Verify installations
RUN python -c "import pandas; import pandas_ta; import aiohttp; print('All dependencies installed')"
```

## Verification Steps

After deployment:
1. Check pandas availability:
   ```python
   python -c "import pandas; import pandas_ta; print('Pandas OK')"
   ```

2. Check aiohttp:
   ```python
   python -c "import aiohttp; print('Aiohttp OK')"
   ```

3. Run a test trade to verify all agents work properly

## Performance Impact

Once fixed, you should see:
- **Market Agent**: 130+ technical indicators instead of 5
- **Social Agent**: Real social media sentiment data
- **Overall**: More accurate trading decisions with complete data