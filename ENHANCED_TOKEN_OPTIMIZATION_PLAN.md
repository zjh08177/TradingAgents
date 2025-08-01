# Enhanced Token Optimization Plan for TradingAgents

## Executive Summary
Implement comprehensive token optimization across all LLM interactions by adding response word limits to agent prompts, enhancing existing token optimizer/limiter utilities, and establishing system-wide token management policies.

## Current State Analysis

### Existing Token Management Components
1. **TokenOptimizer** (`token_optimizer.py`)
   - Reduces prompt tokens by 25-30% through intelligent compression
   - Preserves quality through validation checks
   - Tracks usage and estimates costs
   - Currently optimizes system prompts only

2. **TokenLimiter** (`token_limiter.py`) 
   - Enforces hard token limits (default 2000)
   - Truncates messages and responses to fit limits
   - Uses tiktoken for accurate counting
   - Thread-safe lazy loading implementation

### Current Issues
1. **No Response Length Control**: Agents generate verbose responses without word/token limits
2. **Reactive Truncation**: Token limiter truncates after generation (wasteful)
3. **Inconsistent Implementation**: Not all agents use optimization
4. **Missing Monitoring**: Limited visibility into actual token usage patterns

## Enhanced Architecture Design

### 1. Agent Prompt Enhancement Strategy

#### Core Principle: Multi-Layer Optimization
Combine proactive response control with advanced compression techniques:

##### Layer 1: Prompt Compression (Pre-Generation)
- **Semantic Compression**: Reduce verbosity by 65% while preserving meaning
- **Abbreviation System**: Domain-specific shortcuts (TA, FA, S/R, MA, RSI)
- **Grammar Optimization**: Remove function words and redundant phrases
- **Structural Efficiency**: Use symbols (→, ↑, ↓, ∴, ∵) instead of words

##### Layer 2: Response Control (During Generation)
Add explicit response length instructions to ALL agent prompts:

```python
# Template for all agent prompts
RESPONSE_CONTROL_TEMPLATE = """
RESPONSE CONSTRAINTS (MANDATORY):
- Maximum response: {max_words} words
- Format: Bullet points preferred over paragraphs
- Focus: Key insights only, no filler content
- Structure: Use headers and tables for clarity
- Conciseness: Every word must add value
"""
```

#### Implementation Pattern
```python
def enhance_agent_prompt(base_prompt: str, agent_type: str) -> str:
    """Add response control to agent prompts"""
    
    # Agent-specific word limits
    WORD_LIMITS = {
        "market_analyst": 300,      # Technical data is concise
        "news_analyst": 250,        # Headlines and impacts
        "social_analyst": 200,      # Sentiment summaries
        "fundamentals_analyst": 350, # Financial data needs more
        "risk_manager": 250,        # Risk points are brief
        "research_manager": 400,    # Synthesis needs space
        "trader": 150              # Decisions are binary
    }
    
    max_words = WORD_LIMITS.get(agent_type, 250)
    
    # Inject response control at the beginning
    enhanced = f"{RESPONSE_CONTROL_TEMPLATE.format(max_words=max_words)}\n\n{base_prompt}"
    
    # Also add reminder at the end
    enhanced += f"\n\nREMEMBER: Keep response under {max_words} words. Be concise and impactful."
    
    return enhanced
```

### 2. Enhanced Token Optimizer

#### New Features
1. **Response Optimization**: Pre-generation guidance for compact responses
2. **Dynamic Limits**: Adjust based on task complexity
3. **Quality Metrics**: Track conciseness vs completeness
4. **Batch Optimization**: Optimize multiple prompts together
5. **Semantic Compression**: 65% reduction through meaning preservation
6. **Multi-Stage Pipeline**: Progressive compression to target levels
7. **Context-Aware Loading**: Load only relevant context dynamically
8. **Grammar-Based Compression**: Automated redundancy removal

```python
class EnhancedTokenOptimizer(TokenOptimizer):
    """Extended optimizer with response control"""
    
    def optimize_for_response_length(self, prompt: str, target_response_tokens: int) -> str:
        """Add response length guidance to prompt"""
        
        # Calculate approximate word count (1 token ≈ 0.75 words)
        target_words = int(target_response_tokens * 0.75)
        
        # Add structured response guidance
        response_guide = f"""
        CRITICAL: Your response must be under {target_words} words.
        
        Structure your response as:
        1. Key Finding (1 sentence)
        2. Supporting Data (bullet points)
        3. Action Item (1 sentence)
        
        Omit: lengthy explanations, repetition, obvious statements
        """
        
        return f"{response_guide}\n\n{prompt}"
    
    def calculate_optimal_limits(self, task_type: str, complexity: float) -> Dict[str, int]:
        """Dynamic token limits based on task"""
        
        BASE_LIMITS = {
            "analysis": {"prompt": 1500, "response": 500},
            "summary": {"prompt": 1000, "response": 300},
            "decision": {"prompt": 800, "response": 200},
            "research": {"prompt": 2000, "response": 700}
        }
        
        limits = BASE_LIMITS.get(task_type, {"prompt": 1200, "response": 400})
        
        # Adjust for complexity (0.5 to 1.5 multiplier)
        complexity_factor = 0.5 + complexity
        limits["prompt"] = int(limits["prompt"] * complexity_factor)
        limits["response"] = int(limits["response"] * complexity_factor)
        
        return limits
```

### 3. Intelligent Token Limiter

#### Enhancements
1. **Predictive Limiting**: Estimate response size before generation
2. **Context-Aware Truncation**: Preserve critical information
3. **Multi-Model Support**: Different limits for different models
4. **Streaming Support**: Token counting during generation

```python
class IntelligentTokenLimiter(TokenLimiter):
    """Smart token limiting with predictive capabilities"""
    
    def __init__(self, model_configs: Dict[str, Dict[str, int]]):
        """Initialize with model-specific configurations"""
        self.model_configs = model_configs
        self.response_history = defaultdict(list)  # Track actual vs predicted
    
    def predict_response_tokens(self, prompt: str, agent_type: str) -> int:
        """Predict response token count based on history"""
        
        # Use historical data if available
        if agent_type in self.response_history and len(self.response_history[agent_type]) > 5:
            avg_ratio = np.mean([h["actual"] / h["prompt_tokens"] 
                                for h in self.response_history[agent_type][-10:]])
            prompt_tokens = self.count_tokens(prompt)
            return int(prompt_tokens * avg_ratio)
        
        # Default predictions by agent type
        DEFAULT_RATIOS = {
            "market_analyst": 0.4,     # Concise technical data
            "news_analyst": 0.35,      # Brief summaries
            "social_analyst": 0.3,     # Short sentiment
            "fundamentals_analyst": 0.5, # More detailed
            "trader": 0.2             # Very brief
        }
        
        ratio = DEFAULT_RATIOS.get(agent_type, 0.4)
        prompt_tokens = self.count_tokens(prompt)
        return int(prompt_tokens * ratio)
    
    def smart_truncate(self, content: str, max_tokens: int, preserve_sections: List[str]) -> str:
        """Intelligently truncate while preserving key sections"""
        
        # Parse content into sections
        sections = self._parse_sections(content)
        
        # Priority queue for sections
        priority_sections = []
        other_sections = []
        
        for section_name, section_content in sections.items():
            if any(preserve in section_name.lower() for preserve in preserve_sections):
                priority_sections.append((section_name, section_content))
            else:
                other_sections.append((section_name, section_content))
        
        # Build truncated content preserving priority sections
        result = []
        current_tokens = 0
        
        # Add priority sections first
        for name, content in priority_sections:
            section_tokens = self.count_tokens(content)
            if current_tokens + section_tokens <= max_tokens * 0.7:  # Reserve 70% for priority
                result.append(f"### {name}\n{content}")
                current_tokens += section_tokens
        
        # Add other sections with remaining space
        remaining_tokens = max_tokens - current_tokens
        for name, content in other_sections:
            section_tokens = self.count_tokens(content)
            if section_tokens <= remaining_tokens:
                result.append(f"### {name}\n{content}")
                remaining_tokens -= section_tokens
            else:
                # Truncate this section
                truncated = self._truncate_to_tokens(content, remaining_tokens - 50)
                result.append(f"### {name}\n{truncated}\n[... truncated]")
                break
        
        return "\n\n".join(result)
```

### 4. System-Wide Token Management

#### Global Configuration
```python
# config/token_management.py
TOKEN_MANAGEMENT_CONFIG = {
    "models": {
        "gpt-4o-mini": {
            "max_prompt_tokens": 8000,
            "max_response_tokens": 2000,
            "cost_per_1k_prompt": 0.00015,
            "cost_per_1k_completion": 0.0006
        },
        "gpt-4": {
            "max_prompt_tokens": 6000,
            "max_response_tokens": 1500,
            "cost_per_1k_prompt": 0.03,
            "cost_per_1k_completion": 0.06
        }
    },
    
    "agent_limits": {
        "market_analyst": {"prompt": 1500, "response": 400, "words": 300},
        "news_analyst": {"prompt": 1200, "response": 350, "words": 250},
        "social_analyst": {"prompt": 1000, "response": 300, "words": 200},
        "fundamentals_analyst": {"prompt": 1800, "response": 500, "words": 350},
        "risk_manager": {"prompt": 1200, "response": 350, "words": 250},
        "research_manager": {"prompt": 2000, "response": 600, "words": 400},
        "trader": {"prompt": 800, "response": 200, "words": 150}
    },
    
    "optimization_targets": {
        "total_tokens_per_run": 40000,  # Target from requirements
        "avg_tokens_per_agent": 2500,
        "response_conciseness": 0.7     # Response/prompt ratio
    },
    
    "monitoring": {
        "track_usage": True,
        "alert_threshold": 0.8,          # Alert at 80% of limits
        "report_frequency": "daily"
    }
}
```

#### Central Token Manager
```python
class TokenManagementSystem:
    """Central system for all token management"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.optimizer = EnhancedTokenOptimizer()
        self.limiter = IntelligentTokenLimiter(config["models"])
        self.usage_tracker = TokenUsageTracker()
    
    def prepare_agent_interaction(self, agent_type: str, base_prompt: str, 
                                 messages: List[Dict]) -> Dict[str, Any]:
        """Prepare optimized interaction for an agent"""
        
        # Get agent-specific limits
        limits = self.config["agent_limits"][agent_type]
        
        # Optimize prompt
        optimized_prompt = self.optimizer.optimize_system_prompt(base_prompt, agent_type)
        
        # Add response control
        controlled_prompt = self.optimizer.optimize_for_response_length(
            optimized_prompt, 
            limits["response"]
        )
        
        # Add word limit instruction
        final_prompt = enhance_agent_prompt(controlled_prompt, agent_type)
        
        # Predict total tokens
        predicted_tokens = self.limiter.predict_response_tokens(final_prompt, agent_type)
        
        # Check if within limits
        if predicted_tokens > limits["response"]:
            logger.warning(f"Predicted tokens ({predicted_tokens}) exceed limit for {agent_type}")
        
        return {
            "prompt": final_prompt,
            "max_tokens": limits["response"],
            "word_limit": limits["words"],
            "predicted_usage": predicted_tokens,
            "optimization_applied": True
        }
    
    def post_interaction_analysis(self, agent_type: str, actual_response: str, 
                                 prompt_tokens: int, completion_tokens: int):
        """Analyze and learn from actual usage"""
        
        # Track usage
        self.usage_tracker.record(agent_type, prompt_tokens, completion_tokens)
        
        # Update prediction model
        self.limiter.response_history[agent_type].append({
            "prompt_tokens": prompt_tokens,
            "actual": completion_tokens,
            "timestamp": time.time()
        })
        
        # Check if response was within word limit
        word_count = len(actual_response.split())
        word_limit = self.config["agent_limits"][agent_type]["words"]
        
        if word_count > word_limit * 1.1:  # 10% tolerance
            logger.warning(f"{agent_type} exceeded word limit: {word_count} > {word_limit}")
            
            # Auto-adjust for next time
            self._adjust_agent_instructions(agent_type, word_count, word_limit)
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        
        return {
            "total_usage": self.usage_tracker.get_total_usage(),
            "by_agent": self.usage_tracker.get_agent_breakdown(),
            "optimization_effectiveness": self._calculate_optimization_metrics(),
            "cost_analysis": self._calculate_costs(),
            "recommendations": self._generate_recommendations()
        }
```

### 5. Implementation Strategy

#### Phase 1: Agent Prompt Updates (Week 1)
1. Update all agent prompts with word limits
2. Add response control templates
3. Test with different word limits to find optimal values

#### Phase 2: Enhanced Utilities (Week 2)
1. Upgrade TokenOptimizer with response optimization
2. Implement IntelligentTokenLimiter
3. Create TokenManagementSystem

#### Phase 3: Integration & Testing (Week 3)
1. Integrate with all agents
2. A/B test optimized vs non-optimized
3. Measure quality impact

#### Phase 4: Monitoring & Tuning (Week 4)
1. Deploy monitoring dashboard
2. Collect usage metrics
3. Fine-tune limits based on data

## Advanced Optimization Techniques

### 1. Prompt Compression Examples

#### Before (Traditional Prompt - 150 tokens):
```
You are an expert market analyst with deep knowledge of technical analysis.
Please analyze the following stock data and provide comprehensive insights:
- Current Price: $150.00
- Daily Change: +2.5%
- Volume: 1.5M
Based on this data, provide detailed technical analysis with explanations,
trading recommendations with full justification, and risk assessment.
```

#### After (Optimized Prompt - 45 tokens):
```
Market analyst→analyze:
AAPL|$150|+2.5%|1.5M vol
Output: 1)TA 2)BUY/SELL/HOLD+reason 3)Risk
Max:300 words
```

### 2. Abbreviation System Implementation

```python
TRADING_ABBREVIATIONS = {
    # Technical Indicators
    "moving average": "MA",
    "exponential moving average": "EMA", 
    "relative strength index": "RSI",
    "moving average convergence divergence": "MACD",
    "bollinger bands": "BB",
    
    # Analysis Terms
    "technical analysis": "TA",
    "fundamental analysis": "FA",
    "support and resistance": "S/R",
    "price action": "PA",
    
    # Common Instructions
    "analyze and report": "analyze→",
    "provide recommendation": "rec:",
    "based on analysis": "∴",
    "considering the data": "per data"
}
```

### 3. Dynamic Context Loading

```python
def load_minimal_context(task_type: str, ticker: str) -> str:
    """Load only essential context based on task"""
    
    MINIMAL_CONTEXTS = {
        "price_check": f"{ticker}|price",
        "technical": f"{ticker}|TA|indicators",
        "sentiment": f"{ticker}|sentiment",
        "news": f"{ticker}|headlines|1d"
    }
    
    return MINIMAL_CONTEXTS.get(task_type, f"{ticker}|general")
```

## Expected Benefits

### Quantitative
- **Token Reduction**: 40-50% overall reduction
- **Cost Savings**: ~45% reduction in API costs
- **Performance**: 30% faster response times
- **Target Achievement**: Stay under 40K tokens per run
- **Prompt Compression**: Additional 22% reduction (~8,783 tokens)

### Qualitative
- **Better UX**: Faster, more concise responses
- **Improved Quality**: Focused on key insights
- **Easier Debugging**: Shorter logs and outputs
- **Scalability**: Can handle more concurrent requests

## Risk Mitigation

### Quality Preservation
1. **Gradual Rollout**: Start with one agent, expand gradually
2. **Quality Metrics**: Track decision accuracy and completeness
3. **Fallback Mode**: Allow verbose mode for complex analysis
4. **Human Review**: Regular quality audits

### Technical Risks
1. **Model Compatibility**: Test with different models
2. **Edge Cases**: Handle very short/long inputs gracefully
3. **Performance**: Ensure optimization doesn't slow down
4. **Integration**: Backward compatibility with existing code

## Success Metrics

### Primary KPIs
1. **Token Usage**: < 40K tokens per complete run
2. **Cost per Run**: < $0.06 (50% reduction)
3. **Response Time**: < 2 seconds per agent
4. **Quality Score**: > 95% accuracy maintained

### Secondary KPIs
1. **Word Limit Compliance**: > 90% of responses within limit
2. **Optimization Effectiveness**: > 35% token reduction
3. **User Satisfaction**: No increase in clarification requests
4. **System Stability**: No increase in errors

## Conclusion

This enhanced token optimization plan provides a comprehensive approach to reducing token usage while maintaining quality. By adding explicit word limits to agent prompts and implementing intelligent token management, we can achieve the 40K token target while improving system performance and reducing costs.