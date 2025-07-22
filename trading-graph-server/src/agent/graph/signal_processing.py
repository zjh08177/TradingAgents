# TradingAgents/graph/signal_processing.py

from langchain_openai import ChatOpenAI


class SignalProcessor:
    """Processes trading signals to extract actionable decisions."""

    def __init__(self, quick_thinking_llm: ChatOpenAI):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Extracted decision (BUY, SELL, or HOLD)
        """
        print(f"🔍 Signal processing input: {len(full_signal)} characters")
        print(f"🔍 Signal preview: {full_signal[:300]}...")
        
        if not full_signal or not full_signal.strip():
            print("❌ Empty signal provided to process_signal")
            return "HOLD - No signal provided"
        
        messages = [
            (
                "system",
                "You are an efficient assistant designed to analyze paragraphs or financial reports provided by a group of analysts. Your task is to extract the investment decision: SELL, BUY, or HOLD. Provide only the extracted decision (SELL, BUY, or HOLD) as your output, without adding any additional text or information.",
            ),
            ("human", full_signal),
        ]

        result = self.quick_thinking_llm.invoke(messages).content
        print(f"🔍 Signal processing result: {result}")
        return result
