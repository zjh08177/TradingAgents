# Trading-Graph-Server Restart Guide

## Overview

This guide provides scripts and instructions for terminating all existing server processes and restarting the real trading-graph-server with proper configuration.

## Scripts Available

### 1. 🚀 `start_real_server.sh` (Comprehensive)

**Features:**
- Comprehensive process termination
- Environment variable validation
- Dependency checking
- Detailed logging and feedback
- Multiple fallback methods
- Port verification

**Usage:**
```bash
# From project root
./backend/start_real_server.sh

# From backend directory
./start_real_server.sh
```

**What it does:**
1. ✅ Checks environment and required files
2. 🔑 Validates API keys (OPENAI_API_KEY required)
3. 💀 Kills ALL existing server processes by multiple methods
4. 🔍 Clears ports 8000, 8001, 8080, 3000, 5000
5. ⏳ Verifies cleanup completion
6. 🚀 Starts real trading-graph-server
7. 📊 Shows server information and endpoints

### 2. ⚡ `quick_restart.sh` (Fast & Simple)

**Features:**
- Fast process termination
- Minimal output
- Quick startup

**Usage:**
```bash
# From project root
./backend/quick_restart.sh

# From backend directory
./quick_restart.sh
```

**What it does:**
1. 💀 Quickly kills existing processes
2. 🔍 Clears port 8000
3. 🚀 Starts server immediately

## Environment Setup

### Required Environment Variables

Create a `.env` file in your project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional but recommended
FINNHUB_API_KEY=your-finnhub-key-here
SERPAPI_API_KEY=your-serpapi-key-here
```

### Alternative: Export Variables

```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
export FINNHUB_API_KEY="your-finnhub-key-here"
export SERPAPI_API_KEY="your-serpapi-key-here"
```

## Server Information

Once started, your server will be available at:

- **Main URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Analysis Endpoint:** POST http://localhost:8000/analyze
- **Streaming Endpoint:** GET http://localhost:8000/analyze/stream

## Testing the Server

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Test Analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}'
```

### Test Streaming
```bash
curl -N http://localhost:8000/analyze/stream?ticker=AAPL
```

## Process Management

### Manual Process Killing

If scripts don't work, use these manual commands:

```bash
# Kill by process name
pkill -f uvicorn
pkill -f run_api.py
pkill -f api.py

# Kill by port
lsof -ti :8000 | xargs kill -9

# Force kill all Python processes (DANGEROUS!)
pkill -f python3
```

### Find Running Processes
```bash
# See all server processes
ps aux | grep -E "(uvicorn|api\.py|run_api)" | grep -v grep

# See what's using port 8000
lsof -i :8000

# See all Python processes
ps aux | grep python
```

## Troubleshooting

### Common Issues

**1. Port 8000 already in use**
```
Error: [Errno 48] Address already in use
```
**Solution:** Use `start_real_server.sh` to force kill existing processes

**2. API keys not found**
```
Error: OPENAI_API_KEY environment variable is not set
```
**Solution:** Set up your `.env` file or export the variable

**3. Permission denied**
```
Permission denied: ./start_real_server.sh
```
**Solution:** Make sure scripts are executable:
```bash
chmod +x backend/start_real_server.sh
chmod +x backend/quick_restart.sh
```

**4. Python dependencies missing**
```
ModuleNotFoundError: No module named 'uvicorn'
```
**Solution:** Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Script Comparison

| Feature | start_real_server.sh | quick_restart.sh |
|---------|---------------------|------------------|
| Process killing | Comprehensive (multiple methods) | Basic (pkill only) |
| Environment check | Full validation | None |
| Dependency check | Yes | No |
| Port verification | Multiple ports | Port 8000 only |
| Logging | Detailed with colors | Minimal |
| Startup time | Slower (thorough) | Faster |
| Error handling | Extensive | Basic |
| Best for | Production/Development | Quick testing |

## Integration with Flutter App

After starting the server, your Flutter app (if configured for LangGraph integration) should automatically:

1. Connect to http://localhost:8000
2. Perform health check
3. Run automated E2E test with TSLA ticker
4. Display results

## Production Deployment

For production deployment:

1. Use `start_real_server.sh` for thorough setup
2. Configure proper environment variables
3. Consider using process managers like:
   - systemd (Linux)
   - PM2 (Node.js ecosystem)
   - Docker containers
   - Cloud platforms (Railway, Heroku, AWS)

## Monitoring

### Server Logs
The server will display detailed logs including:
- Request/response information
- Trading analysis progress
- Agent execution status
- Error messages

### Health Monitoring
```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8000/health'

# Server status
ps aux | grep -E "(uvicorn|api\.py)" | grep -v grep
```

## Quick Reference Commands

```bash
# Start comprehensive server (recommended)
./backend/start_real_server.sh

# Quick restart
./backend/quick_restart.sh

# Check if server is running
curl -s http://localhost:8000/health

# Stop server manually
pkill -f uvicorn

# View server logs (if running in background)
tail -f backend/server.log

# Test full analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' | jq
```

---

## Notes

- The scripts automatically handle virtual environment activation
- Server runs with `--reload` flag for development (auto-restart on code changes)
- Default configuration uses OpenAI models (o3 for deep thinking, gpt-4o for quick thinking)
- All analysis results are saved to `backend/results/` directory
- For production, remove `--reload` flag and use proper process management 