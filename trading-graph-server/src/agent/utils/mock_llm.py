"""
Mock LLM for testing without API keys
"""
import random
from typing import List, Dict, Any
from langchain_core.messages import AIMessage, BaseMessage


class MockLLM:
    """Mock LLM that returns realistic responses for testing"""
    
    def __init__(self, model_name="mock-gpt-4"):
        self.model_name = model_name
        self.call_count = 0
    
    def invoke(self, input_data, **kwargs) -> AIMessage:
        """Mock invoke method that returns realistic responses"""
        self.call_count += 1
        
        # Handle different input types
        if isinstance(input_data, str):
            prompt = input_data
        elif isinstance(input_data, list):
            # Extract prompt from messages
            prompt = str(input_data[-1]) if input_data else ""
        else:
            prompt = str(input_data)
        
        # Generate appropriate mock response based on context
        response_content = self._generate_mock_response(prompt)
        
        return AIMessage(content=response_content)
    
    def bind_tools(self, tools):
        """Mock bind_tools method"""
        return MockLLMWithTools(self, tools)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response based on prompt content"""
        prompt_lower = prompt.lower()
        
        # Market Analyst response
        if "market" in prompt_lower and "indicator" in prompt_lower:
            return """Based on the technical analysis of AAPL:

**Technical Indicators Summary:**
- 50 SMA: $175.23 (Price above SMA - Bullish)
- 200 SMA: $165.45 (Price well above - Strong uptrend)
- RSI: 58.3 (Neutral territory)
- MACD: Positive crossover detected
- Bollinger Bands: Price near upper band

**Market Trend Analysis:**
The stock is showing strong bullish momentum with price trading above both key moving averages. The recent MACD crossover suggests continued upward movement.

| Indicator | Value | Signal |
|-----------|-------|--------|
| 50 SMA | $175.23 | Bullish |
| RSI | 58.3 | Neutral |
| MACD | Positive | Buy |"""

        # Social Media Analyst response
        elif "social" in prompt_lower or "sentiment" in prompt_lower:
            return """**Social Media Sentiment Analysis for AAPL:**

Overall Sentiment: POSITIVE (72% positive, 18% neutral, 10% negative)

Key Themes:
- Strong excitement about new product launches
- Positive reactions to recent earnings
- Growing institutional interest

Top Mentions:
1. "Apple Vision Pro exceeding expectations"
2. "Services revenue hitting new records"
3. "Strong iPhone 15 demand"

| Platform | Sentiment | Volume |
|----------|-----------|---------|
| Twitter | Positive | High |
| Reddit | Bullish | Medium |
| StockTwits | Very Bullish | High |"""

        # News Analyst response
        elif "news" in prompt_lower or "world affairs" in prompt_lower:
            return """**News Analysis for AAPL:**

Recent Developments:
1. Apple announces record Q4 earnings beating estimates
2. New AI features planned for next iOS update
3. Expansion in emerging markets showing strong growth

Market Impact:
- Positive earnings surprise likely to drive price higher
- AI integration positions Apple competitively
- International growth reduces dependency on US market

| News Type | Impact | Timeframe |
|-----------|---------|-----------|
| Earnings | Positive | Immediate |
| Product | Positive | Medium-term |
| Expansion | Positive | Long-term |"""

        # Fundamentals Analyst response
        elif "fundamental" in prompt_lower:
            return """**Fundamental Analysis for AAPL:**

Financial Metrics:
- P/E Ratio: 28.5 (slightly above sector average)
- Revenue Growth: 8.1% YoY
- Profit Margin: 25.3%
- ROE: 147.9%
- Debt/Equity: 1.95

Valuation Assessment:
Company shows strong fundamentals with consistent revenue growth and exceptional profitability. High ROE indicates efficient capital utilization.

| Metric | Value | Industry Avg | Rating |
|--------|-------|--------------|---------|
| P/E | 28.5 | 25.2 | Fair |
| ROE | 147.9% | 22.5% | Excellent |
| Margin | 25.3% | 18.7% | Strong |"""

        # Bull Researcher response
        elif "bull" in prompt_lower:
            return """Bull Analyst: I strongly believe AAPL presents an exceptional buying opportunity. The technical indicators are flashing green across the board - we've got positive MACD crossover, price above both 50 and 200 SMAs, and RSI in healthy territory with room to run.

The fundamentals back this up completely. With a 147.9% ROE, Apple is generating incredible returns on equity. The 25.3% profit margin is well above industry average, showing pricing power and operational efficiency.

The bear's concerns about valuation are overblown. Yes, P/E is slightly elevated at 28.5, but this is justified by the growth trajectory and market position. The social sentiment is overwhelmingly positive at 72%, and recent news about AI integration positions Apple perfectly for the next tech cycle.

This is a clear BUY signal with a target of $195 in the next quarter."""

        # Bear Researcher response
        elif "bear" in prompt_lower:
            return """Bear Analyst: I must caution against the excessive optimism here. While the numbers look good on surface, there are significant risks being overlooked.

First, the P/E ratio of 28.5 is concerning in the current rate environment. With the Fed maintaining higher rates, growth stocks like Apple face valuation pressure. The debt/equity ratio of 1.95 is also quite high, making the company vulnerable to rate changes.

The technical picture isn't as rosy as the bull suggests. We're near the upper Bollinger Band, indicating overbought conditions. The RSI at 58.3 is approaching overbought territory, and we could see a pullback soon.

Market saturation is a real concern - iPhone sales growth is slowing, and the company is increasingly dependent on services revenue. Competition from Android and emerging Chinese brands is intensifying.

I recommend HOLD at best, with downside risk to $165 if market conditions deteriorate."""

        # Research Manager response
        elif "portfolio manager" in prompt_lower or "debate facilitator" in prompt_lower:
            return """After careful evaluation of both perspectives, I'm making a decisive call: BUY.

The bull case is more compelling here. While the bear raises valid concerns about valuation and market saturation, the fundamental strength of Apple cannot be ignored. The 147.9% ROE is exceptional, and the company's ability to maintain 25.3% margins demonstrates pricing power that few companies possess.

The technical setup supports this decision - positive MACD crossover and price above key moving averages indicate strong momentum. The 72% positive social sentiment suggests retail and institutional alignment.

Investment Plan:
1. Initiate position at current levels
2. Set stop loss at $168 (below 50 SMA)
3. Target $190-195 in 3-6 months
4. Consider adding on any dips to $172-175 range

Risk Management: Position size should be 5-7% of portfolio given current market conditions."""

        # Trader response
        elif "trader" in prompt_lower or "trading agent" in prompt_lower:
            return """Based on the comprehensive analysis provided, I'm executing a BUY decision for AAPL.

The convergence of positive technical indicators, strong fundamentals, and bullish sentiment creates a high-probability setup. The risk/reward ratio is favorable with support at $168 and upside potential to $195.

Key factors driving this decision:
1. Technical momentum confirmed by MACD crossover
2. Exceptional ROE of 147.9% demonstrating operational excellence  
3. Positive catalyst from AI integration plans
4. Strong social sentiment at 72% positive

Position sizing: 6% of portfolio
Entry: Market order at open
Stop loss: $168
Take profit levels: 50% at $185, 50% at $195

FINAL TRANSACTION PROPOSAL: **BUY**"""

        # Risk Analyst responses
        elif "risky" in prompt_lower and "risk analyst" in prompt_lower:
            return """Risky Analyst: The trader's BUY decision is absolutely the right call, and I'd even argue for a larger position! This is a generational opportunity with Apple. The AI integration alone could add $50-100 billion in market cap. With 72% positive sentiment and technical momentum, we should be aggressive here. The upside to $195 is conservative - I see $210+ potential. We should size up to 10% of portfolio to maximize returns on this high-conviction trade."""

        elif "safe" in prompt_lower and "conservative" in prompt_lower:
            return """Safe Analyst: While I understand the enthusiasm, we must be cautious. The P/E of 28.5 in a high-rate environment is concerning. The debt/equity ratio of 1.95 means significant interest rate sensitivity. I'd recommend reducing position size to 3-4% maximum, tightening the stop loss to $170, and taking profits earlier at $180. Market conditions can change rapidly, and capital preservation should be our priority."""

        elif "neutral" in prompt_lower and "risk analyst" in prompt_lower:
            return """Neutral Analyst: Both perspectives have merit. The bullish case is strong with solid fundamentals and momentum, but the valuation concerns are real. I suggest sticking with the trader's 6% position size but implementing a scaled entry - buy 3% now, and add the remaining 3% on any pullback to $172-175. This balances opportunity capture with risk management. Keep the $195 target but be prepared to take partial profits at $185."""

        # Risk Manager response
        elif "risk management judge" in prompt_lower:
            return """**Risk Management Decision: BUY**

After evaluating all perspectives, I approve the BUY recommendation with the following risk-adjusted parameters:

Position Size: 5% of portfolio (slightly reduced from trader's 6% for risk management)
Entry Strategy: Scale in with 3% initial position, add 2% on confirmation above $178
Stop Loss: $170 (tighter than proposed $168)
Take Profit: 40% at $185, 40% at $192, let 20% run with trailing stop

Rationale:
- Strong fundamental backdrop supports bullish case
- Technical momentum is clearly positive
- Risk/reward ratio of approximately 1:3 is acceptable
- Scaled entry provides downside protection while maintaining upside exposure

The conservative analyst's concerns about valuation are noted, but the growth trajectory and market position justify current multiples. The neutral analyst's balanced approach aligns well with prudent risk management.

Monitor closely for any deterioration in market conditions or company-specific news."""

        # Default response
        else:
            return f"Mock response for prompt: {prompt[:100]}... Analysis complete with positive outlook."


class MockLLMWithTools(MockLLM):
    """Mock LLM that can handle tool calls"""
    
    def __init__(self, base_llm: MockLLM, tools: List[Any]):
        super().__init__(base_llm.model_name)
        self.base_llm = base_llm
        self.tools = tools
        self.tool_call_count = 0
    
    def invoke(self, input_data: Dict[str, Any], **kwargs) -> AIMessage:
        """Mock invoke that can return tool calls"""
        self.call_count += 1
        
        # Extract messages
        messages = input_data.get("messages", [])
        
        # Check if we should make tool calls based on context
        should_call_tools = self._should_call_tools(messages)
        
        if should_call_tools and self.tool_call_count < 2:  # Limit tool calls
            self.tool_call_count += 1
            # Return a message with tool calls
            tool_calls = self._generate_mock_tool_calls()
            return AIMessage(content="", tool_calls=tool_calls)
        else:
            # Return regular response
            prompt = str(messages[-1]) if messages else ""
            return self.base_llm.invoke(prompt)
    
    def _should_call_tools(self, messages: List[BaseMessage]) -> bool:
        """Determine if we should make tool calls"""
        # Check if we haven't made any tool calls yet
        if not messages:
            return True
        
        # Check if the last message was a tool response
        for msg in messages:
            if hasattr(msg, 'type') and str(msg.type) == 'tool':
                return False  # Already have tool responses
        
        return self.tool_call_count < 2
    
    def _generate_mock_tool_calls(self) -> List[Dict[str, Any]]:
        """Generate mock tool calls"""
        # Mock tool calls based on available tools
        tool_calls = []
        
        for tool in self.tools[:2]:  # Limit to 2 tool calls
            if hasattr(tool, 'name'):
                tool_name = tool.name
                
                # Generate appropriate args based on tool name
                if 'YFin' in tool_name:
                    args = {"symbol": "AAPL"}
                elif 'stockstats' in tool_name:
                    args = {"indicators": ["close_50_sma", "rsi", "macd"]}
                elif 'social' in tool_name:
                    args = {"query": "AAPL stock", "limit": 10}
                elif 'news' in tool_name:
                    args = {"query": "Apple stock news", "limit": 5}
                else:
                    args = {}
                
                tool_calls.append({
                    "name": tool_name,
                    "args": args,
                    "id": f"call_{self.tool_call_count}_{tool_name}"
                })
        
        return tool_calls