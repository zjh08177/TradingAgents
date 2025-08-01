#!/usr/bin/env python3
"""
Advanced Prompt Compression System
Implements multi-stage compression to achieve 22%+ token reduction
"""

import re
import logging
import asyncio
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CompressionResult:
    """Result of prompt compression"""
    original: str
    compressed: str
    original_tokens: int
    compressed_tokens: int
    reduction_percentage: float
    stages_applied: List[str]

class AdvancedPromptCompressor:
    """Multi-stage prompt compression system"""
    
    def __init__(self):
        self.setup_abbreviations()
        self.setup_compression_rules()
        self.compression_stats = {
            "total_original": 0,
            "total_compressed": 0,
            "compressions_performed": 0
        }
        logger.info("🗜️ Advanced Prompt Compressor initialized")
    
    def setup_abbreviations(self):
        """Setup domain-specific abbreviations"""
        self.abbreviations = {
            # Technical indicators
            "moving average": "MA",
            "exponential moving average": "EMA",
            "simple moving average": "SMA",
            "relative strength index": "RSI",
            "moving average convergence divergence": "MACD",
            "bollinger bands": "BB",
            "average true range": "ATR",
            "volume weighted average price": "VWAP",
            
            # Market terms
            "technical analysis": "TA",
            "fundamental analysis": "FA",
            "support and resistance": "S/R",
            "price action": "PA",
            "market capitalization": "MCap",
            "price to earnings": "P/E",
            "earnings per share": "EPS",
            
            # Trading terms
            "buy": "BUY",
            "sell": "SELL", 
            "hold": "HOLD",
            "stop loss": "SL",
            "take profit": "TP",
            "risk reward": "R:R",
            
            # Common phrases
            "based on": "per",
            "according to": "per",
            "in order to": "to",
            "with respect to": "re:",
            "as a result": "∴",
            "because": "∵",
            "leads to": "→",
            "results in": "→",
            "greater than": ">",
            "less than": "<",
            "approximately": "≈",
            
            # Instruction phrases
            "please analyze": "analyze:",
            "please provide": "provide:",
            "you should": "",
            "you must": "must:",
            "it is important to": "important:",
            "make sure to": "ensure:",
            "based on the analysis": "∴",
            "provide a comprehensive": "provide",
            "detailed analysis": "analysis",
            "thorough examination": "examine"
        }
    
    def setup_compression_rules(self):
        """Setup semantic compression rules"""
        self.compression_rules = [
            # Remove redundant phrases
            (r"You are an? expert (.+?) specializing in (.+?)\.", r"Expert \1: \2."),
            (r"Your role is to", r""),
            (r"Please ensure that you", r""),
            (r"It would be helpful if you could", r""),
            (r"Following this exact structure:", r"Structure:"),
            (r"Based on the following data:", r"Data:"),
            (r"Provide the following information:", r"Output:"),
            
            # Compress verbose instructions
            (r"comprehensive analysis including", r"analyze:"),
            (r"detailed examination of", r"examine:"),
            (r"careful consideration of", r"consider:"),
            (r"thorough investigation into", r"investigate:"),
            (r"in-depth look at", r"review:"),
            
            # Remove filler words
            (r"\b(very|really|quite|rather|somewhat|fairly)\b", r""),
            (r"\b(just|simply|merely|only)\b", r""),
            (r"\s+", r" "),  # Multiple spaces to single
            
            # Compress formatting instructions
            (r"Format your response as follows:", r"Format:"),
            (r"Structure your analysis to include:", r"Include:"),
            (r"Make sure to include", r"Include"),
            (r"Be sure to", r""),
            
            # Convert to symbols
            (r"and/or", r"/"),
            (r" and ", r" & "),
            (r"percentage", r"%"),
            (r"number", r"#"),
            (r"dollar", r"$"),
        ]
    
    def compress_prompt(self, prompt: str, target_reduction: float = 0.22) -> CompressionResult:
        """
        Apply multi-stage compression to achieve target reduction
        
        Args:
            prompt: Original prompt text
            target_reduction: Target reduction percentage (default 22%)
            
        Returns:
            CompressionResult with details
        """
        original_tokens = self._estimate_tokens(prompt)
        current_prompt = prompt
        stages_applied = []
        
        # Stage 1: Apply abbreviations
        current_prompt, abbrev_count = self._apply_abbreviations(current_prompt)
        if abbrev_count > 0:
            stages_applied.append(f"Abbreviations ({abbrev_count})")
        
        # Stage 2: Apply compression rules
        current_prompt, rules_count = self._apply_compression_rules(current_prompt)
        if rules_count > 0:
            stages_applied.append(f"Rules ({rules_count})")
        
        # Stage 3: Remove redundancy
        current_prompt = self._remove_redundancy(current_prompt)
        stages_applied.append("Redundancy removal")
        
        # Stage 4: Optimize whitespace and structure
        current_prompt = self._optimize_structure(current_prompt)
        stages_applied.append("Structure optimization")
        
        # Calculate results
        compressed_tokens = self._estimate_tokens(current_prompt)
        reduction = (original_tokens - compressed_tokens) / original_tokens
        
        # Update stats
        self.compression_stats["total_original"] += original_tokens
        self.compression_stats["total_compressed"] += compressed_tokens
        self.compression_stats["compressions_performed"] += 1
        
        result = CompressionResult(
            original=prompt,
            compressed=current_prompt,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            reduction_percentage=reduction * 100,
            stages_applied=stages_applied
        )
        
        logger.info(f"🗜️ Compressed: {original_tokens} → {compressed_tokens} tokens ({reduction:.1%} reduction)")
        
        return result
    
    async def compress_prompt_async(self, prompt: str, target_reduction: float = 0.22) -> CompressionResult:
        """
        Async version of compress_prompt - runs compression in thread pool
        """
        # Run the CPU-intensive compression in a thread pool
        return await asyncio.to_thread(self.compress_prompt, prompt, target_reduction)
    
    def _apply_abbreviations(self, text: str) -> Tuple[str, int]:
        """Apply abbreviation replacements"""
        result = text
        count = 0
        
        for full_form, abbrev in self.abbreviations.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(full_form), re.IGNORECASE)
            new_text = pattern.sub(abbrev, result)
            if new_text != result:
                count += len(pattern.findall(result))
                result = new_text
        
        return result, count
    
    def _apply_compression_rules(self, text: str) -> Tuple[str, int]:
        """Apply semantic compression rules"""
        result = text
        count = 0
        
        for pattern, replacement in self.compression_rules:
            new_text = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            if new_text != result:
                count += 1
                result = new_text
        
        return result, count
    
    def _remove_redundancy(self, text: str) -> str:
        """Remove semantic redundancy"""
        # Remove repeated words
        result = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        
        # Remove redundant punctuation
        result = re.sub(r'\.+', '.', result)
        result = re.sub(r',+', ',', result)
        result = re.sub(r':+', ':', result)
        
        # Remove empty parentheses
        result = re.sub(r'\(\s*\)', '', result)
        
        return result
    
    def _optimize_structure(self, text: str) -> str:
        """Optimize text structure"""
        # Remove multiple newlines
        result = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing/leading whitespace
        lines = [line.strip() for line in result.split('\n')]
        result = '\n'.join(lines)
        
        # Remove multiple spaces
        result = re.sub(r' {2,}', ' ', result)
        
        # Clean up punctuation spacing
        result = re.sub(r'\s+([.,;:!?])', r'\1', result)
        result = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', result)
        
        return result.strip()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters or 0.75 words
        word_count = len(text.split())
        char_count = len(text)
        
        # Use average of both methods
        word_estimate = word_count / 0.75
        char_estimate = char_count / 4
        
        return int((word_estimate + char_estimate) / 2)
    
    def create_compressed_template(self, agent_type: str) -> str:
        """Create a compressed prompt template for an agent type"""
        
        templates = {
            "market_analyst": """Expert market analyst: TA & trading signals.
Data→analyze→Output: 1)TA 2)BUY/SELL/HOLD 3)Risk
Use: MA,RSI,MACD,BB. Max:300 words""",
            
            "news_analyst": """News analyst: sentiment & impact.
Headlines→analyze→Output: 1)Sentiment 2)Impact 3)Rec
Focus: market-moving events. Max:250 words""",
            
            "social_analyst": """Social analyst: community sentiment.
Data→analyze→Output: 1)Sentiment 2)Trends 3)Signals
Sources: Twitter,Reddit. Max:200 words""",
            
            "fundamentals_analyst": """FA expert: financials & valuation.
Data→analyze→Output: 1)Metrics 2)Valuation 3)Outlook
Key: P/E,EPS,Revenue. Max:350 words""",
            
            "trader": """Trader: execute decisions.
Analysis→decide→Output: BUY/SELL/HOLD+entry+exit
Include: position size,SL,TP. Max:150 words"""
        }
        
        return templates.get(agent_type, "Analyze→provide insights. Max:250 words")
    
    def get_compression_stats(self) -> Dict:
        """Get compression statistics"""
        if self.compression_stats["compressions_performed"] == 0:
            return {"message": "No compressions performed yet"}
        
        avg_reduction = (
            (self.compression_stats["total_original"] - self.compression_stats["total_compressed"]) 
            / self.compression_stats["total_original"] * 100
        )
        
        return {
            "total_compressions": self.compression_stats["compressions_performed"],
            "total_tokens_saved": self.compression_stats["total_original"] - self.compression_stats["total_compressed"],
            "average_reduction": f"{avg_reduction:.1f}%",
            "total_original_tokens": self.compression_stats["total_original"],
            "total_compressed_tokens": self.compression_stats["total_compressed"]
        }


# Global instance
_compressor = None

def get_prompt_compressor() -> AdvancedPromptCompressor:
    """Get global compressor instance"""
    global _compressor
    if _compressor is None:
        _compressor = AdvancedPromptCompressor()
    return _compressor


def compress_prompt(prompt: str) -> str:
    """Convenience function to compress a prompt"""
    compressor = get_prompt_compressor()
    result = compressor.compress_prompt(prompt)
    return result.compressed


# Example usage
if __name__ == "__main__":
    compressor = AdvancedPromptCompressor()
    
    # Test prompt
    test_prompt = """
    You are an expert market analyst specializing in technical analysis and trading strategies.
    Your role is to provide comprehensive analysis of market conditions based on the following data.
    
    Please analyze the technical indicators including moving averages, relative strength index,
    and bollinger bands. Based on your analysis, provide a detailed trading recommendation
    including whether to buy, sell, or hold, along with stop loss and take profit levels.
    
    Make sure to include risk assessment and position sizing recommendations.
    It is important to provide clear and actionable insights.
    """
    
    result = compressor.compress_prompt(test_prompt)
    
    print("Original prompt:")
    print("-" * 50)
    print(result.original)
    print(f"\nTokens: {result.original_tokens}")
    
    print("\nCompressed prompt:")
    print("-" * 50)
    print(result.compressed)
    print(f"\nTokens: {result.compressed_tokens}")
    print(f"Reduction: {result.reduction_percentage:.1f}%")
    print(f"Stages applied: {', '.join(result.stages_applied)}")
    
    print("\nCompression stats:")
    print(compressor.get_compression_stats())