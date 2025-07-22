# 🚀 **Current Deployment Guide: Unified Trading Graph Server**

## 📁 **Single Source of Truth**

**All deployment now uses**: `trading-graph-server/` directory

- **✅ Unified Structure**: Everything in one place
- **✅ No Backend**: Old `backend/` directory is obsolete
- **✅ Single Config**: One `langgraph.json` in `trading-graph-server/`
- **✅ All Nodes Visible**: Complete multi-agent workflow exposed

## 🎯 **Current Architecture**

```
TradingAgents/
└── trading-graph-server/          # 🎯 SINGLE SOURCE OF TRUTH
    ├── langgraph.json            # LangGraph Cloud config
    ├── .env                      # Environment variables
    ├── venv/                     # Python virtual environment
    ├── src/agent/                # Unified agent directory
    │   ├── __init__.py          # Graph entry point
    │   ├── analysts/            # All analyst implementations
    │   ├── managers/            # Research & risk managers
    │   ├── researchers/         # Bull & bear researchers
    │   ├── risk_mgmt/          # Risk analysis team
    │   ├── trader/             # Trading logic
    │   ├── utils/              # Agent utilities
    │   ├── dataflows/          # Data interfaces
    │   ├── graph/              # Graph orchestration
    │   └── default_config.py   # Configuration
    └── requirements.txt         # Dependencies
```

## 🛠️ **Deployment Options**

### **1. LangGraph Studio (Development)**
```bash
cd trading-graph-server
langgraph dev --allow-blocking
```
- **Access**: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
- **All 21 nodes visible**: Complete workflow transparency
- **Perfect for**: Development, testing, debugging

### **2. LangGraph Cloud (Production)**
```bash
cd trading-graph-server
langgraph deploy
```
- **Requirements**: LangGraph CLI, authenticated account
- **Scalable**: Auto-scaling production deployment
- **Perfect for**: Production workloads

### **3. Self-Hosted (Custom)**
```bash
cd trading-graph-server
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
- **Full control**: Your infrastructure
- **Custom scaling**: Manual configuration
- **Perfect for**: Enterprise/custom requirements

## 🔧 **Setup Instructions**

### **Prerequisites**
```bash
# 1. Install LangGraph CLI
pip install langraph-cli

# 2. Authenticate
langraph auth login

# 3. Set up environment
cd trading-graph-server
cp .env.example .env
# Edit .env with your API keys
```

### **Local Development**
```bash
cd trading-graph-server
source venv/bin/activate
langgraph dev --allow-blocking
```

### **Cloud Deployment**
```bash
cd trading-graph-server
langgraph deploy
```

## 📊 **What You Get**

### **Complete Multi-Agent Workflow**
- **4 Parallel Analysts**: Market, Social, News, Fundamentals
- **Investment Debate**: Bull vs Bear researchers
- **Risk Analysis**: 3-perspective risk assessment
- **Final Decision**: Comprehensive trading recommendation

### **Full Visibility**
- **21 Detailed Nodes**: No black boxes
- **Real-time Monitoring**: See every step
- **Debug Capabilities**: Interrupt and inspect
- **State Management**: Complete conversation history

## 🚫 **Deprecated/Removed**

- **❌ `backend/` directory**: No longer used
- **❌ `tradingagents/` directory**: Removed (was duplicate)
- **❌ Old deployment scripts**: Updated to use `trading-graph-server/`
- **❌ Multiple configs**: Single `langgraph.json` now

## 🎯 **Current Status**

- **✅ Unified Structure**: Single source of truth
- **✅ LangGraph Studio**: All nodes visible
- **✅ Production Ready**: Scalable deployment
- **✅ Clean Architecture**: No duplication
- **✅ Easy Deployment**: One command deploy

**Use `trading-graph-server/` for all deployment activities!** 🚀 