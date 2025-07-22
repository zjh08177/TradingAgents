# TradingAgents - Multi-Agent Trading Analysis System

A sophisticated multi-agent system for stock trading analysis using LangGraph and AI agents.

## 🏗️ **Project Structure**

This project contains **two different server implementations**:

### 📊 **`backend/` - FastAPI Trading Server** (Main Development)
- **FastAPI REST API** for web applications
- **CLI interface** for command-line usage  
- **Flutter app integration** ready
- **Local development** focused

```bash
cd backend
python api.py  # Start FastAPI server on :8000
python main.py TSLA  # CLI analysis
```

### 🌐 **`trading-graph-server/` - LangGraph Cloud Server**
- **LangGraph Studio** compatible
- **LangGraph Cloud** deployment ready
- **Visual debugging** with Studio UI
- **Professional deployment** focused

```bash
cd trading-graph-server
langgraph dev  # Start LangGraph server on :2024
```

## 🚀 **Quick Start**

### **For Development & Testing:**
```bash
# Use the backend FastAPI server
cd backend
./start_real_server.sh
# API: http://localhost:8000
```

### **For LangGraph Studio & Cloud:**
```bash
# Use the LangGraph server
cd trading-graph-server  
./restart_server.sh
# Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## 📱 **Flutter App**

The Flutter app in `trading_dummy/` connects to the **backend FastAPI server** by default.

## 🔄 **Recent Updates**

- ✅ Fixed LangGraph Cloud deployment configuration
- ✅ Updated validation scripts for new structure
- ✅ All 5/5 deployment checks passing
- ✅ Ready for both local and cloud deployment

## 🔧 **Configuration**

Both servers use the same core `tradingagents` package but with different entry points and configurations suitable for their respective deployment targets.

## 📚 **Documentation**

- **Backend API**: See `backend/README.md`
- **LangGraph Server**: See `trading-graph-server/README.md` 
- **Flutter App**: See `trading_dummy/README.md`
- **Deployment**: See `DEPLOYMENT_FIX_SUMMARY.md`

---

*Choose the right server for your use case: FastAPI for development/integration, LangGraph for Studio/Cloud.*
