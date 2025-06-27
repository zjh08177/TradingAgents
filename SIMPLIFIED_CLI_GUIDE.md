# TradingAgents Simplified CLI Guide

## 🚀 Quick Start (Simplified Mode)

The TradingAgents CLI has been simplified for faster and easier usage. Now you only need to provide one input: **the ticker symbol**.

### Basic Usage

```bash
# Run with default settings
python -m cli.main

# The CLI will prompt you for just the ticker symbol:
# Enter ticker symbol (default: SPY): AAPL
```

### What Gets Applied Automatically

When you use the simplified mode, these optimal defaults are automatically applied:

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| **Date** | Today's date | Uses the latest trading day |
| **Analysts** | All 4 analysts | Market, Social, News, Fundamentals |
| **Research Depth** | 5 rounds | Deep analysis with comprehensive debates |
| **LLM Provider** | OpenAI | Most reliable and capable provider |
| **Quick Thinking** | GPT-4o | Fast model for routine tasks |
| **Deep Thinking** | o3 | Advanced reasoning model for complex analysis |

### Example Workflow

1. **Run the command:**
   ```bash
   python -m cli.main
   ```

2. **See the welcome screen** with project information

3. **Enter your ticker symbol:**
   ```
   Enter Ticker Symbol
   Enter the stock ticker you want to analyze (e.g., AAPL, TSLA, SPY)
   Default: SPY
   
   [SPY]: AAPL
   ```

4. **Review the auto-configuration:**
   ```
   Configuration:
   • Ticker: AAPL
   • Date: 2025-01-26 (latest trading day)
   • Analysts: All analysts (Market, Social, News, Fundamentals)
   • Research Depth: Deep (5 rounds of debate)
   • LLM Provider: OpenAI
   • Quick Thinking: GPT-4o
   • Deep Thinking: o3
   
   Starting analysis with optimized settings...
   ```

5. **Watch the analysis proceed** through all stages automatically

## 🔧 Advanced Mode (Optional)

If you need full control over the configuration, use the advanced mode:

```bash
# Run with advanced configuration options
python -m cli.main --advanced
```

This will present the full step-by-step configuration interface where you can customize:
- Analysis date
- Specific analysts to include
- Research depth levels
- LLM provider choice
- Specific model selections

## 💡 Benefits of Simplified Mode

- **⚡ Faster**: No need to go through 6 configuration steps
- **🎯 Focused**: Just enter the stock you want to analyze
- **🧠 Optimized**: Uses the best-performing configuration
- **👥 Beginner-friendly**: Perfect for new users
- **🔄 Consistent**: Same high-quality analysis every time

## 🛠️ Command Options

```bash
# Default simplified mode
python -m cli.main

# Advanced configuration mode
python -m cli.main --advanced
python -m cli.main -a

# Specific analyze command (same as default)
python -m cli.main analyze

# Advanced analyze command
python -m cli.main analyze --advanced

# Help and usage
python -m cli.main --help
```

## 📊 What You Get

The simplified mode provides the same comprehensive analysis as the advanced mode:

1. **📈 Market Analysis**: Technical indicators, price trends, trading volume
2. **💭 Social Sentiment**: Reddit discussions, social media sentiment
3. **📰 News Analysis**: Recent news impact, global events
4. **💰 Fundamentals**: Financial metrics, company performance
5. **🔬 Research Debate**: Bull vs Bear perspectives
6. **💼 Trading Plan**: Specific investment recommendations
7. **⚖️ Risk Assessment**: Multi-perspective risk evaluation
8. **📋 Final Decision**: Portfolio management recommendation

## 🎯 Perfect For

- **Day traders** who need quick analysis
- **Researchers** doing multiple stock analyses
- **Students** learning about algorithmic trading
- **Developers** integrating into automated workflows
- **Anyone** who wants powerful analysis without complexity

## 🔄 Migration from Old Interface

If you were using the old multi-step interface:

**Before (6 steps):**
```bash
python -m cli.main
# Step 1: Enter ticker
# Step 2: Enter date
# Step 3: Select analysts
# Step 4: Select research depth
# Step 5: Select LLM provider
# Step 6: Select thinking agents
```

**Now (1 step):**
```bash
python -m cli.main
# Just enter ticker - everything else is optimized automatically!
```

The new simplified interface reduces user input by 83% while maintaining the same analytical power! 