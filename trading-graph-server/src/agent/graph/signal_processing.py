# TradingAgents/graph/signal_processing.py

from langchain_openai import ChatOpenAI


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    async def process_signal(self, full_signal: str) -> str:
        """Process a full trading signal to extract the core decision."""
        if not full_signal or not full_signal.strip():
            return "HOLD - No signal provided"
        
        messages = [
            ("system", "Extract the investment decision: SELL, BUY, or HOLD. Provide only the decision without additional text."),
            ("human", full_signal),
        ]

        result = await self.quick_thinking_llm.ainvoke(messages)
        return result.content
