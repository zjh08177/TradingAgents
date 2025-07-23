# TradingAgents/utils/memory.py

import os
import openai
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FinancialSituationMemory:
    """Simplified memory for financial situation tracking"""

    def __init__(self, memory_type: str, config: Dict[str, Any]):
        self.memory_type = memory_type
        self.config = config
        self.messages: List[str] = []

    def add_message(self, message: str):
        """Add a message to memory"""
        if message and message.strip():
            self.messages.append(message.strip())

    def get_messages(self) -> List[str]:
        """Get all messages"""
        return self.messages[-5:]  # Keep only last 5 for simplicity

    def get_memory_text(self, situation: str) -> str:
        """Get simplified memory text"""
        if not self.messages:
            return "No prior context available."
        
        recent_messages = self.get_messages()
        return f"Recent context:\n" + "\n".join(recent_messages)

    def get_memories(self, situation: str, n_matches: int = 2) -> list:
        """Get memories (simplified compatibility method)"""
        messages = self.get_messages()
        # Return mock recommendations to maintain compatibility
        return [{"recommendation": msg} for msg in messages[:n_matches]]

    def save_memory(self, memory_text: str):
        """Save memory (simplified)"""
        self.add_message(memory_text)

def get_embedding(text: str, client=None) -> List[float]:
    """Get embedding with token limit protection"""
    if not text or not text.strip():
        return [0.0] * 1536  # Default embedding dimension
    
    # Truncate text to avoid token limits
    if len(text) > 6000:  # Conservative limit
        text = text[:6000] + "..."
    
    try:
        if not client:
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return [0.0] * 1536
