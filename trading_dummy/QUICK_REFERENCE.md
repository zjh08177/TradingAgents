# LangGraph Integration Quick Reference

## 🚀 Quick Start Commands

### Start Backend Server
```bash
# With real API keys
cd backend
export OPENAI_API_KEY="your-key"
python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# With test keys
cd backend
./test_server.sh
```

### Run Flutter App
```bash
cd trading_dummy
flutter run
```

### Test API Directly
```bash
# Health check
curl http://localhost:8000/health

# Analyze TSLA
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA"}'
```

### Run Integration Test
```bash
cd trading_dummy
dart run test_langgraph_integration.dart
```

## 📍 Key Files

- **API Test Docs:** `LANGGRAPH_API_TEST_DOCUMENTATION.md`
- **Verification Checklist:** `LANGGRAPH_VERIFICATION_CHECKLIST.md` 
- **Implementation Summary:** `LANGGRAPH_INTEGRATION_SUMMARY.md`
- **Main README:** `LANGGRAPH_README.md`

## ✅ Verification Points

1. Server running → Check health endpoint
2. App connects → Green status card
3. Auto-test runs → TSLA analyzed after 2s
4. Logs complete → All 7 steps logged
5. Results shown → Trading recommendation displayed

## 🔍 Debug Commands

```bash
# Check if server is running
ps aux | grep uvicorn

# Watch Flutter logs
flutter logs

# Test server connection
nc -zv localhost 8000
```

## 🎯 E2E Test Flow

1. Launch app
2. Wait 2 seconds
3. TSLA analysis starts automatically
4. Results display
5. Check logs for verification

**No manual input required!**