# Trading Graph Server - Configuration Analysis

## 🏗️ Configuration Architecture Overview

The Trading Graph Server uses a **layered configuration system** with multiple customization points for models, behavior, and performance tuning.

### Configuration Flow
```
Environment Variables → default_config.py → dataflows/config.py → TradingAgentsGraph
```

## 📍 Key Configuration Points

### 1. **Model Configuration** (Primary Customization Point)

#### **Quick Thinking Model** (`quick_thinking_llm`)
- **Location**: `default_config.py:32` and `llm_factory.py:40-46`
- **Usage**: Fast analysis tasks, tool calls, routing decisions
- **Current**: `"gpt-4o-mini"`
- **Used by**: All analysts, dispatchers, tool nodes
- **Customization**:
  ```python
  config = {
      "quick_thinking_model": "gpt-4o",  # Upgrade to GPT-4o
      "llm_provider": "openai"
  }
  ```

#### **Deep Thinking Model** (`deep_thinking_llm`)
- **Location**: `default_config.py:31` and `llm_factory.py:48-55`
- **Usage**: Complex reasoning, debates, final decisions
- **Current**: `"gpt-4o-mini"`
- **Used by**: Bull/bear researchers, risk debators, research manager, trader
- **Customization**:
  ```python
  config = {
      "reasoning_model": "gpt-4o",  # Upgrade to GPT-4o
      "llm_provider": "openai"
  }
  ```

**Note**: There's a **naming inconsistency** in the config:
- Config uses: `"deep_think_llm"` and `"quick_think_llm"`
- Factory expects: `"reasoning_model"` and `"quick_thinking_model"`

### 2. **LLM Provider Configuration**

#### **Supported Providers** (`llm_factory.py:17-37`)
- **OpenAI**: `"openai"` (default)
- **Anthropic**: `"anthropic"`
- **Google**: `"google"`
- **Ollama**: `"ollama"` (via OpenAI API)
- **OpenRouter**: `"openrouter"` (via OpenAI API)

#### **Provider Customization**:
```python
# OpenAI (default)
config = {
    "llm_provider": "openai",
    "backend_url": "https://api.openai.com/v1",
    "quick_thinking_model": "gpt-4o-mini",
    "reasoning_model": "gpt-4o"
}

# Anthropic
config = {
    "llm_provider": "anthropic", 
    "backend_url": "https://api.anthropic.com/v1",
    "quick_thinking_model": "claude-3-haiku-20240307",
    "reasoning_model": "claude-3-sonnet-20240229"
}

# Ollama (local)
config = {
    "llm_provider": "ollama",
    "backend_url": "http://localhost:11434/v1",
    "quick_thinking_model": "llama3:8b",
    "reasoning_model": "llama3:70b"
}
```

### 3. **Performance & Behavior Configuration**

#### **Execution Settings** (`default_config.py:44-45`)
```python
config = {
    "max_tokens_per_analyst": 2000,  # Token limit per analyst
    "execution_timeout": 120,        # Hard timeout in seconds
}
```

#### **Debate Configuration** (`default_config.py:36-39`)
```python
config = {
    "max_debate_rounds": 1,           # Bull/bear debate rounds
    "max_risk_discuss_rounds": 1,     # Risk debate rounds  
    "max_research_debate_rounds": 1,  # Research debate rounds
}
```

#### **Feature Toggles** (`default_config.py:49-52`)
```python
config = {
    "enable_parallel_tools": True,      # Parallel tool execution
    "enable_smart_caching": True,       # Tool result caching
    "enable_smart_retry": True,         # Smart retry logic
    "enable_debate_optimization": True, # Multi-round optimization
}
```

### 4. **Graph Architecture Configuration**

#### **Analyst Selection** (`trading_graph.py:35`)
```python
# Select which analysts to include
selected_analysts = ["market", "social", "news", "fundamentals"]

# Custom selection
selected_analysts = ["market", "fundamentals"]  # Skip social/news
```

#### **Memory Configuration** (`setup.py:233-240`)
- Research memory for bull/bear researchers
- Risk memory for risk analysis
- Trader memory for final decisions

### 5. **Tool & API Configuration**

#### **External APIs** (`default_config.py:55-58`)
```python
config = {
    "online_tools": True,                    # Enable online data fetching
    "serper_key": os.getenv("SERPER_API_KEY", ""),  # Google Search API
}
```

#### **Data Sources** (`default_config.py:20-23`)
```python  
config = {
    "data_dir": "./data",
    "data_cache_dir": "./dataflows/data_cache",
    "results_dir": "./results",
}
```

## 🔧 Configuration Implementation Points

### 1. **Graph Setup Entry Point** (`setup.py:94-100`)
```python
class GraphBuilder(IGraphBuilder):
    def __init__(self, 
                 quick_thinking_llm: ILLMProvider,    # ← Injected model
                 deep_thinking_llm: ILLMProvider,     # ← Injected model  
                 config: Dict[str, Any]):             # ← Full config
        self.config = config
```

### 2. **Trading Graph Entry Point** (`trading_graph.py:32-52`)
```python
class TradingAgentsGraph:
    def __init__(self, config=None, selected_analysts=None):
        self.config = config or get_config()        # ← Load config
        
        # Create LLMs from config
        self.quick_thinking_llm = self.llm_factory.create_llm(
            self.config.get("llm_provider", "openai"), 
            self.config.get("quick_thinking_model", "gpt-4o-mini"),  # ← Model config
            self.config
        )
```

### 3. **Model Assignment by Role** (`setup.py:168-258`)

#### **Quick Thinking Model Used By**:
- All analysts: Market, Social, News, Fundamentals (`setup.py:168,184,200,216`)
- Tool routing and decisions
- Fast analysis tasks

#### **Deep Thinking Model Used By**:
- Bull researcher (`setup.py:233`)
- Bear researcher (`setup.py:234`) 
- Research manager (`setup.py:236`)
- Risk debators (`setup.py:247-251`)
- Risk manager (`setup.py:255`)
- Trader (`setup.py:258`)

## 🎯 Common Configuration Scenarios

### Scenario 1: **Performance Optimization**
```python
config = {
    # Use faster models for speed
    "quick_thinking_model": "gpt-3.5-turbo",
    "reasoning_model": "gpt-4o-mini",
    
    # Reduce timeouts and rounds
    "execution_timeout": 90,
    "max_debate_rounds": 1,
    
    # Enable all optimizations
    "enable_parallel_tools": True,
    "enable_smart_caching": True,
    "enable_smart_retry": True,
}
```

### Scenario 2: **Quality Maximization**
```python
config = {
    # Use best models for quality
    "quick_thinking_model": "gpt-4o",
    "reasoning_model": "gpt-4o",
    
    # Allow more time and rounds
    "execution_timeout": 300,
    "max_research_debate_rounds": 3,
    "max_tokens_per_analyst": 4000,
}
```

### Scenario 3: **Cost Optimization**
```python
config = {
    # Use cheapest models
    "quick_thinking_model": "gpt-3.5-turbo",
    "reasoning_model": "gpt-4o-mini",
    
    # Limit token usage
    "max_tokens_per_analyst": 1000,
    
    # Reduce analysts
    "selected_analysts": ["market", "fundamentals"]  # Skip social/news
}
```

### Scenario 4: **Local/Private Deployment**
```python
config = {
    # Use local Ollama
    "llm_provider": "ollama",
    "backend_url": "http://localhost:11434/v1",
    "quick_thinking_model": "llama3:8b",
    "reasoning_model": "llama3:70b",
    
    # Disable online tools
    "online_tools": False,
}
```

## 🚨 Known Configuration Issues

### Issue 1: **Model Config Naming Inconsistency**
- **Problem**: Config uses `"deep_think_llm"` but factory expects `"reasoning_model"`
- **Location**: `default_config.py:31` vs `llm_factory.py:53`
- **Impact**: Deep thinking model falls back to default
- **Fix**: Standardize on one naming convention

### Issue 2: **Missing Configuration Validation**
- **Problem**: No validation of model names or provider compatibility
- **Impact**: Runtime errors with invalid configurations
- **Recommendation**: Add config validation in `llm_factory.py`

### Issue 3: **Hard-coded Model Selection**
- **Problem**: Model assignment to roles is hard-coded in `setup.py`
- **Impact**: Cannot customize which model type each role uses
- **Recommendation**: Make role-model mapping configurable

## 🔍 Configuration Discovery Points

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
SERPER_API_KEY=...

# Directory Overrides
TRADINGAGENTS_PROJECT_DIR=/custom/path
TRADINGAGENTS_DATA_DIR=/data/path
TRADINGAGENTS_RESULTS_DIR=/results/path
```

### File Locations
- **Primary Config**: `src/agent/default_config.py`
- **Config Manager**: `src/agent/dataflows/config.py`
- **LLM Factory**: `src/agent/factories/llm_factory.py`
- **Graph Setup**: `src/agent/graph/setup.py`
- **Main Entry**: `src/agent/graph/trading_graph.py`

### Dynamic Configuration
```python
from agent.dataflows.config import set_config

# Override configuration at runtime
set_config({
    "reasoning_model": "gpt-4o",
    "execution_timeout": 180,
    "max_research_debate_rounds": 2
})
```

## ✅ Recommendations

### 1. **Fix Naming Inconsistency**
Standardize config keys to match factory expectations:
```python
# In default_config.py, change:
"deep_think_llm": "gpt-4o-mini"     # ❌ Current
"quick_think_llm": "gpt-4o-mini"    # ❌ Current

# To:
"reasoning_model": "gpt-4o-mini"     # ✅ Recommended  
"quick_thinking_model": "gpt-4o-mini" # ✅ Recommended
```

### 2. **Add Configuration Validation**
```python
def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize configuration"""
    # Validate required keys
    # Check model availability  
    # Normalize provider names
    # Return validated config
```

### 3. **Add Role-Model Mapping**
```python
config = {
    "role_model_mapping": {
        "analysts": "quick_thinking_model",
        "researchers": "reasoning_model", 
        "debators": "reasoning_model",
        "trader": "reasoning_model"
    }
}
```

### 4. **Environment-Based Profiles**
```python
# config/profiles/
# - development.py
# - production.py
# - local.py
# - performance.py
```

This configuration analysis provides a comprehensive understanding of how to customize the Trading Graph Server for different use cases and requirements.