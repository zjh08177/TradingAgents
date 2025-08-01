# Token Optimization Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Token Management System"
        TMS[Token Management System<br/>Central Controller]
        
        subgraph "Pre-Generation Phase"
            PE[Prompt Enhancer<br/>+Word Limits]
            TO[Token Optimizer<br/>-30% Reduction]
            PL[Predictive Limiter<br/>Estimates Usage]
        end
        
        subgraph "Generation Phase"
            AG[Agent<br/>Interaction]
            RC[Response Control<br/>Word Limits]
            ST[Stream Monitor<br/>Real-time Tracking]
        end
        
        subgraph "Post-Generation Phase"
            TL[Token Limiter<br/>Enforcement]
            UT[Usage Tracker<br/>Analytics]
            LM[Learning Module<br/>Optimization]
        end
    end
    
    subgraph "Agent Layer"
        MA[Market Analyst<br/>300 words]
        NA[News Analyst<br/>250 words]
        SA[Social Analyst<br/>200 words]
        FA[Fundamentals<br/>350 words]
        TR[Trader<br/>150 words]
    end
    
    subgraph "Configuration"
        GC[Global Config<br/>Token Limits]
        AC[Agent Config<br/>Word Limits]
        MC[Model Config<br/>Costs & Limits]
    end
    
    %% Flow connections
    TMS --> PE
    PE --> TO
    TO --> PL
    PL --> AG
    AG --> RC
    RC --> ST
    ST --> TL
    TL --> UT
    UT --> LM
    LM --> TMS
    
    %% Agent connections
    AG --> MA
    AG --> NA
    AG --> SA
    AG --> FA
    AG --> TR
    
    %% Config connections
    GC --> TMS
    AC --> PE
    MC --> PL
    
    %% Styling
    classDef controller fill:#ff6b6b,stroke:#fff,stroke-width:2px
    classDef preGen fill:#4ecdc4,stroke:#fff,stroke-width:2px
    classDef genPhase fill:#45b7d1,stroke:#fff,stroke-width:2px
    classDef postGen fill:#96ceb4,stroke:#fff,stroke-width:2px
    classDef agent fill:#dfe6e9,stroke:#2d3436,stroke-width:1px
    classDef config fill:#ffeaa7,stroke:#fdcb6e,stroke-width:1px
    
    class TMS controller
    class PE,TO,PL preGen
    class AG,RC,ST genPhase
    class TL,UT,LM postGen
    class MA,NA,SA,FA,TR agent
    class GC,AC,MC config
```

## Component Interactions

### 1. Pre-Generation Phase Flow
```
User Request → Token Management System → Prompt Enhancer
                                     ↓
                              Token Optimizer
                                     ↓
                            Predictive Limiter
                                     ↓
                            Agent (with controls)
```

### 2. Generation Phase Flow
```
Agent Prompt (with word limits) → LLM API
                              ↓
                    Response Generation
                              ↓
                 Stream Monitor (real-time)
                              ↓
              Response Control Enforcement
```

### 3. Post-Generation Phase Flow
```
Generated Response → Token Limiter (if needed)
                 ↓
           Usage Tracker
                 ↓
        Learning Module
                 ↓
    Update Predictions
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant TMS as Token Manager
    participant PE as Prompt Enhancer
    participant TO as Token Optimizer
    participant A as Agent
    participant LLM as LLM API
    participant TL as Token Limiter
    participant UT as Usage Tracker
    
    U->>TMS: Request Analysis
    TMS->>PE: Get Enhanced Prompt
    PE->>PE: Add Word Limits (300 words)
    PE->>TO: Optimize Prompt
    TO->>TO: Reduce Tokens (-30%)
    TO->>TMS: Return Optimized
    TMS->>A: Execute with Controls
    A->>LLM: API Call
    LLM->>A: Response
    A->>TL: Check Response
    TL->>TL: Enforce Limits
    TL->>UT: Track Usage
    UT->>TMS: Update Stats
    TMS->>U: Final Response
```

## Token Budget Allocation

```mermaid
pie title Token Budget per Run (40K Total)
    "System & Context" : 5000
    "Market Analyst" : 3000
    "News Analyst" : 2500
    "Social Analyst" : 2000
    "Fundamentals Analyst" : 3500
    "Risk Manager" : 2500
    "Research Manager" : 4000
    "Trader" : 1500
    "Debators (3x)" : 9000
    "Summary & Output" : 2000
    "Buffer & Overhead" : 5000
```

## Implementation Layers

### Layer 1: Infrastructure
- **Token Counting**: Tiktoken integration
- **Model Configuration**: Per-model limits and costs
- **Threading**: Async-safe operations
- **Caching**: Token count caching

### Layer 2: Optimization
- **Prompt Compression**: 25-30% reduction
- **Response Control**: Word limit enforcement
- **Context Trimming**: Smart message pruning
- **Batch Processing**: Multi-prompt optimization

### Layer 3: Intelligence
- **Predictive Modeling**: Response size estimation
- **Learning System**: Historical pattern analysis
- **Dynamic Adjustment**: Real-time limit tuning
- **Quality Preservation**: Accuracy monitoring

### Layer 4: Monitoring
- **Usage Analytics**: Token consumption tracking
- **Cost Analysis**: Real-time cost calculation
- **Alert System**: Threshold breach detection
- **Reporting**: Daily optimization reports

## Integration Points

### 1. Agent Integration
```python
# In each agent's node function
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
from agent.utils.token_optimizer import optimize_prompt_for_analyst

async def analyst_node(state):
    # Get base prompt
    base_prompt = get_analyst_prompt()
    
    # Enhance with word limits
    enhanced_prompt = enhance_agent_prompt(base_prompt, "market_analyst")
    
    # Optimize tokens
    optimized_prompt = optimize_prompt_for_analyst(enhanced_prompt, "market_analyst")
    
    # Execute with limits
    response = await llm.ainvoke(
        optimized_prompt,
        max_tokens=300  # Enforce at API level too
    )
```

### 2. Configuration Integration
```python
# config/token_management.py
from dataclasses import dataclass

@dataclass
class TokenConfig:
    max_total_tokens: int = 40000
    max_prompt_tokens: int = 8000
    max_response_tokens: int = 2000
    word_limit_compliance: float = 0.9
    optimization_target: float = 0.3
```

### 3. Monitoring Integration
```python
# monitoring/token_dashboard.py
class TokenDashboard:
    def display_metrics(self):
        return {
            "current_run": {
                "total_tokens": self.current_tokens,
                "vs_target": f"{(self.current_tokens / 40000) * 100:.1f}%",
                "agents_completed": self.agents_completed
            },
            "optimization": {
                "prompt_reduction": f"{self.prompt_reduction:.1f}%",
                "response_compliance": f"{self.word_compliance:.1f}%"
            }
        }
```

## Success Metrics Visualization

```mermaid
graph LR
    subgraph "Before Optimization"
        B1[60K+ Tokens]
        B2[High Costs]
        B3[Slow Response]
        B4[Verbose Output]
    end
    
    subgraph "After Optimization"
        A1[<40K Tokens]
        A2[45% Cost Reduction]
        A3[30% Faster]
        A4[Concise Output]
    end
    
    B1 --> A1
    B2 --> A2
    B3 --> A3
    B4 --> A4
    
    style B1 fill:#e74c3c
    style B2 fill:#e74c3c
    style B3 fill:#e74c3c
    style B4 fill:#e74c3c
    style A1 fill:#27ae60
    style A2 fill:#27ae60
    style A3 fill:#27ae60
    style A4 fill:#27ae60
```

## Deployment Strategy

### Phase 1: Foundation (Week 1)
- Deploy Prompt Enhancer
- Update agent prompts with word limits
- Basic monitoring

### Phase 2: Optimization (Week 2)
- Integrate Token Optimizer
- Deploy Predictive Limiter
- A/B testing

### Phase 3: Intelligence (Week 3)
- Learning system activation
- Dynamic adjustment
- Quality validation

### Phase 4: Scale (Week 4)
- Full production deployment
- Dashboard and alerts
- Continuous optimization

## Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Quality Loss | High | Low | Quality metrics, fallback mode |
| Integration Issues | Medium | Medium | Gradual rollout, testing |
| Model Changes | Medium | Low | Configurable limits |
| Performance Impact | Low | Low | Async operations, caching |