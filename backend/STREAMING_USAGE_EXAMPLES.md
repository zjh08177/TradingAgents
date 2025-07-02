# TradingAgents Streaming Analysis - Usage Examples

## Quick Start

### 1. Basic Streaming Analysis
```bash
# Run streaming analysis with default settings
python -m cli.main stream

# Or use the streaming flag with analyze command
python -m cli.main analyze --streaming
```

### 2. Advanced Streaming Analysis
```bash
# Run streaming analysis with advanced configuration
python -m cli.main stream --advanced

# Or combine flags
python -m cli.main analyze --streaming --advanced
```

### 3. Default Command with Streaming
```bash
# Use streaming as default behavior
python -m cli.main --streaming
```

## What to Expect

### Regular Analysis Output
```
data: {"type": "status", "message": "Starting analysis for TEM..."}
data: {"type": "agent_status", "agent": "Market Analyst"}
data: {"type": "progress", "percentage": 16}
...
[Wait for completion, then get all reports at once]
```

### Streaming Analysis Output
```
data: {"type": "status", "message": "Starting analysis for TEM..."}
data: {"type": "agent_status", "agent": "Market Analyst"}
data: {"type": "progress", "percentage": 16}

🔴 Live: Market Analyst
Technical Analysis for TEM:
Based on the recent price action and volume patterns...
[Content streams in real-time as the agent thinks and writes]

Moving to fundamental analysis...
The company's recent earnings report shows...
[More content streaming live]

🔴 Live: Social Media Analyst  
Social sentiment analysis reveals...
[Content continues streaming from next agent]
```

## UI Layout in Streaming Mode

```
┌─ Welcome to TradingAgents ─────────────────┐
│ Welcome to TradingAgents CLI               │
│ © Tauric Research                          │
└────────────────────────────────────────────┘

┌─ Agent Progress ──┬─ Recent Messages ──────┐
│ Market Analyst ✅ │ 14:30:22 [System] TEM  │
│ Social Analyst 🔄 │ 14:30:25 [Reasoning]   │
│ News Analyst   ⏳ │ 14:30:28 [Tool Call]   │
└───────────────────┴────────────────────────┘

┌─ 🔴 Live: Social Media Analyst ────────────┐
│ Analyzing social media sentiment for TEM:  │
│                                            │
│ Recent Twitter mentions show mixed         │
│ sentiment with 60% positive mentions...    │
│ [Content streaming in real-time]           │
└────────────────────────────────────────────┘

┌─ Latest Report Section ────────────────────┐
│ ### Market Analysis                        │
│ Technical indicators suggest...            │
│ [Shows most recently completed section]    │
└────────────────────────────────────────────┘

┌─ TradingAgents Streaming Analysis ─────────┐
│ Press Ctrl+C to stop                       │
└────────────────────────────────────────────┘
```

## Advanced Usage Scenarios

### 1. Development and Debugging
When developing or debugging agent behaviors, streaming allows you to:
- See exactly where agents get stuck
- Monitor real-time thought processes
- Identify performance bottlenecks
- Watch agent decision-making flow

### 2. Educational Use
For learning how the system works:
- Observe AI reasoning in real-time
- Understand multi-agent collaboration
- See how different analysis types build on each other
- Learn from the agents' analytical approaches

### 3. Production Monitoring
In production environments:
- Monitor system health in real-time
- Detect anomalies early
- Provide better user experience with live updates
- Enable real-time decision making

## Comparison: Regular vs Streaming

| Aspect | Regular Analysis | Streaming Analysis |
|--------|------------------|-------------------|
| **Content Delivery** | Batch (sections at once) | Real-time (as generated) |
| **User Experience** | Wait then receive | Continuous feedback |
| **Debugging** | Post-mortem only | Live debugging |
| **Monitoring** | End result only | Process visibility |
| **Engagement** | Passive waiting | Active observation |
| **Resource Usage** | Lower CPU (4 FPS) | Higher CPU (8 FPS) |

## Technical Architecture

### StreamingMessageBuffer
Extends the regular MessageBuffer with:
- Real-time content streaming capabilities
- Agent transition detection
- Content buffering and delivery
- Callback system for live updates

### Layout Differences
- Additional "streaming_content" panel for live updates
- Higher refresh rate (8 FPS vs 4 FPS)
- Enhanced agent status indicators
- Real-time content formatting

### Agent Detection
The system detects agent transitions by:
- Analyzing message content for agent keywords
- Monitoring state changes in the graph
- Tracking section completions
- Managing content buffers per agent

## Best Practices

### 1. When to Use Streaming
- **Development**: Always use streaming for development
- **Production**: Use for high-engagement scenarios
- **Debugging**: Essential for troubleshooting
- **Demos**: Great for showing system capabilities

### 2. When to Use Regular Analysis
- **Batch Processing**: When processing many symbols
- **Resource Constrained**: On slower systems
- **Automated Systems**: When only final results matter
- **Background Processing**: For scheduled runs

### 3. Performance Considerations
- Streaming uses more CPU due to higher refresh rate
- Network usage is similar (same data, different timing)
- Memory usage slightly higher due to buffering
- Terminal performance may vary based on content length

## Troubleshooting

### Common Issues
1. **Slow Terminal**: Reduce content display or use regular mode
2. **Missing Content**: Check agent keyword detection
3. **Jumbled Output**: Ensure terminal supports rich formatting
4. **Performance**: Lower refresh rate or use regular analysis

### Debug Mode
```bash
# Enable debug output
export DEBUG=1
python -m cli.main stream --advanced
```

This will show additional information about:
- Agent detection logic
- Content buffering
- State transitions
- Performance metrics 