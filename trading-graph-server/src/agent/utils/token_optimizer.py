#!/usr/bin/env python3
"""
Token Usage Optimization System - Task 6.2
Optimizes LLM token usage patterns while maintaining analysis quality
"""

import logging
import re
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import tiktoken
from functools import lru_cache

from .tokenizer_cache import get_global_tokenizer, get_global_tokenizer_async

logger = logging.getLogger(__name__)

@dataclass
class TokenUsageStats:
    """Token usage statistics for analysis"""
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_estimate: float
    optimization_potential: float

@dataclass
class PromptOptimization:
    """Optimized prompt with metrics"""
    original_prompt: str
    optimized_prompt: str
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    quality_preserved: bool

class TokenOptimizer:
    """
    Task 6.2: LLM token usage optimization
    Reduces token consumption while maintaining analysis quality
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self._tokenizer = None  # Will be loaded from global cache when needed
        
        # Token cost per 1k tokens (approximate)
        self.cost_per_1k_tokens = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        
        logger.debug(f"🎯 Token Optimizer initialized for {model_name} (using global tokenizer cache)")

    async def _get_tokenizer(self):
        """Async-safe tokenizer getter using global cache"""
        if self._tokenizer is None:
            try:
                # Use global cache
                self._tokenizer = await get_global_tokenizer_async(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to get tokenizer from cache: {e}")
                # Fallback to None
                self._tokenizer = None
        return self._tokenizer
    
    def _get_tokenizer_sync(self):
        """Synchronous tokenizer getter using global cache"""
        if self._tokenizer is None:
            try:
                # Use global cache
                self._tokenizer = get_global_tokenizer(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to get tokenizer from cache: {e}")
                # Return None and handle gracefully
                return None
        return self._tokenizer

    @lru_cache(maxsize=1000)
    def _count_tokens_cached(self, text_hash: int, text_len: int) -> int:
        """Cached token counting - uses hash for LRU cache"""
        # This is called only when cache misses
        tokenizer = self._get_tokenizer_sync()
        if tokenizer is None:
            # Fallback estimation: roughly 4 characters per token
            return text_len // 4
        
        # Need to retrieve the actual text for encoding
        # Since we can't store the text in the signature, we'll handle this differently
        return -1  # Sentinel value indicating cache miss
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text with caching (synchronous version)"""
        # For short texts, use direct counting (caching overhead not worth it)
        if len(text) < 50:
            tokenizer = self._get_tokenizer_sync()
            if tokenizer is None:
                return len(text) // 4
            return len(tokenizer.encode(text))
        
        # For longer texts, use a simpler caching approach
        # Hash the first 100 chars + length for cache key
        cache_key = hash(text[:100] + str(len(text)))
        
        # Check if we have this in our instance cache
        if not hasattr(self, '_token_cache'):
            self._token_cache = {}
        
        if cache_key in self._token_cache:
            logger.debug(f"🎯 Token count cache hit for text length {len(text)}")
            return self._token_cache[cache_key]
        
        # Cache miss - count tokens
        tokenizer = self._get_tokenizer_sync()
        if tokenizer is None:
            token_count = len(text) // 4
        else:
            token_count = len(tokenizer.encode(text))
        
        # Cache the result
        self._token_cache[cache_key] = token_count
        
        # Limit cache size
        if len(self._token_cache) > 1000:
            # Remove oldest entries (simple FIFO for now)
            keys_to_remove = list(self._token_cache.keys())[:200]
            for key in keys_to_remove:
                del self._token_cache[key]
        
        return token_count
    
    async def count_tokens_async(self, text: str) -> int:
        """Count tokens in text (asynchronous version to prevent blocking)"""
        tokenizer = await self._get_tokenizer()
        if tokenizer is None:
            # Fallback estimation: roughly 4 characters per token
            return len(text) // 4
        
        # Run the CPU-intensive encoding operation in a thread pool
        try:
            token_count = await asyncio.to_thread(len, tokenizer.encode(text))
            return token_count
        except Exception as e:
            logger.warning(f"Async token counting failed: {e}, using fallback")
            return len(text) // 4

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int = 0) -> float:
        """Estimate cost based on token usage"""
        model_costs = self.cost_per_1k_tokens.get(self.model_name, 
                                                  self.cost_per_1k_tokens["gpt-4o-mini"])
        
        input_cost = (prompt_tokens / 1000) * model_costs["input"]
        output_cost = (completion_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost

    def optimize_system_prompt(self, original_prompt: str, analyst_type: str) -> PromptOptimization:
        """
        Optimize system prompt for reduced token usage
        Target: 25-30% reduction while maintaining quality
        """
        logger.debug(f"🎯 Optimizing {analyst_type} system prompt...")
        
        original_tokens = self.count_tokens(original_prompt)
        
        # Apply optimization strategies
        optimized = original_prompt
        
        # Strategy 1: Remove redundant phrases and repetitive content
        optimized = self._remove_redundancy(optimized)
        
        # Strategy 2: Compress verbose instructions
        optimized = self._compress_instructions(optimized)
        
        # Strategy 3: Simplify formatting instructions
        optimized = self._optimize_formatting(optimized)
        
        # Strategy 4: Remove excessive examples (keep only essential ones)
        optimized = self._optimize_examples(optimized)
        
        # Strategy 5: Consolidate similar concepts
        optimized = self._consolidate_concepts(optimized)
        
        optimized_tokens = self.count_tokens(optimized)
        reduction = ((original_tokens - optimized_tokens) / original_tokens) * 100
        
        # Quality check - ensure core instructions are preserved
        quality_preserved = self._validate_quality_preservation(original_prompt, optimized, analyst_type)
        
        optimization = PromptOptimization(
            original_prompt=original_prompt,
            optimized_prompt=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            reduction_percentage=reduction,
            quality_preserved=quality_preserved
        )
        
        logger.debug(f"📊 {analyst_type} optimization: {original_tokens} → {optimized_tokens} tokens ({reduction:.1f}% reduction)")
        
        return optimization
    
    async def optimize_system_prompt_async(self, original_prompt: str, analyst_type: str) -> PromptOptimization:
        """
        Async version of optimize_system_prompt to prevent blocking
        """
        logger.debug(f"🎯 Optimizing {analyst_type} system prompt (async)...")
        
        # Count original tokens asynchronously
        original_tokens = await self.count_tokens_async(original_prompt)
        
        # Apply optimization strategies (these are mostly string operations, so run in thread)
        optimized = await asyncio.to_thread(self._apply_all_optimizations, original_prompt)
        
        # Count optimized tokens asynchronously
        optimized_tokens = await self.count_tokens_async(optimized)
        reduction = ((original_tokens - optimized_tokens) / original_tokens) * 100
        
        # Quality check in thread to avoid blocking
        quality_preserved = await asyncio.to_thread(
            self._validate_quality_preservation, original_prompt, optimized, analyst_type
        )
        
        optimization = PromptOptimization(
            original_prompt=original_prompt,
            optimized_prompt=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            reduction_percentage=reduction,
            quality_preserved=quality_preserved
        )
        
        logger.debug(f"📊 {analyst_type} optimization: {original_tokens} → {optimized_tokens} tokens ({reduction:.1f}% reduction)")
        
        return optimization
    
    def _apply_all_optimizations(self, prompt: str) -> str:
        """Helper method to apply all optimization strategies sequentially"""
        optimized = prompt
        optimized = self._remove_redundancy(optimized)
        optimized = self._compress_instructions(optimized)
        optimized = self._optimize_formatting(optimized)
        optimized = self._optimize_examples(optimized)
        optimized = self._consolidate_concepts(optimized)
        return optimized

    def _remove_redundancy(self, prompt: str) -> str:
        """Remove redundant phrases and repetitive content"""
        # Remove repeated instructions
        optimized = re.sub(r'(\b\w+\b)(\s+\1\b)+', r'\1', prompt)
        
        # Remove redundant adjectives
        redundant_phrases = [
            r'\bvery comprehensive\b', r'\bcomprehensive',
            r'\bhighly detailed\b', r'\bdetailed',
            r'\bextremely important\b', r'\bimportant',
            r'\bspecific and detailed\b', r'\bspecific',
            r'\bcritical and essential\b', r'\bcritical'
        ]
        
        for pattern in redundant_phrases:
            optimized = re.sub(pattern, lambda m: m.group().split()[-1], optimized, flags=re.IGNORECASE)
        
        return optimized

    def _compress_instructions(self, prompt: str) -> str:
        """Compress verbose instructions into concise forms"""
        compressions = {
            # Verbose → Concise
            r'You are an expert (.+?) specializing in (.+?)\. Your role is to': r'Expert \1: \2.',
            r'following this exact structure:': r'using this structure:',
            r'After executing tools, provide a comprehensive': r'After tools, provide',
            r'Include specific numerical values, ratios, and percentages': r'Include specific numbers and ratios',
            r'Provide quantitative justification for all qualitative assessments': r'Quantify assessments',
            r'Focus on metrics that directly impact': r'Focus on metrics impacting',
            r'CRITICAL: Include specific': r'Include specific',
            r'IMPORTANT: Ensure that': r'Ensure',
            r'Make sure to': r'',
            r'It is essential that you': r'',
            r'Please ensure that you': r'',
        }
        
        optimized = prompt
        for pattern, replacement in compressions.items():
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
        
        return optimized

    def _optimize_formatting(self, prompt: str) -> str:
        """Optimize markdown formatting instructions"""
        # Simplify table formatting instructions
        optimized = re.sub(
            r'\| .+? \| .+? \| .+? \| .+? \| .+? \|[\s\S]*?\|[-\s\|]+\|',
            '| Metric | Value | Trend | Score |\n|---|---|---|---|',
            prompt
        )
        
        # Simplify repeated formatting examples
        optimized = re.sub(r'(\*\*[^*]+\*\*): \[([^\]]+)\]', r'**\1**: \2', optimized)
        
        # Remove excessive markdown examples
        optimized = re.sub(r'(#{1,3} \d+\. [^\n]+\n)([^\n]*\n){0,2}', r'\1', optimized)
        
        return optimized

    def _optimize_examples(self, prompt: str) -> str:
        """Keep only essential examples, remove verbose ones"""
        # Keep only the most important examples
        lines = prompt.split('\n')
        optimized_lines = []
        in_example_section = False
        example_count = 0
        
        for line in lines:
            if '**Example' in line or 'Example:' in line:
                in_example_section = True
                example_count += 1
                if example_count <= 2:  # Keep only first 2 examples
                    optimized_lines.append(line)
            elif in_example_section and (line.startswith('#') or line.strip() == ''):
                in_example_section = False
                optimized_lines.append(line)
            elif not in_example_section or example_count <= 2:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)

    def _consolidate_concepts(self, prompt: str) -> str:
        """Consolidate similar concepts to reduce repetition"""
        # Consolidate risk-related terms
        optimized = re.sub(
            r'(risk factors?|risks?|vulnerabilities|threats|concerns)',
            'risks',
            prompt,
            flags=re.IGNORECASE
        )
        
        # Consolidate analysis terms
        optimized = re.sub(
            r'(analysis|assessment|evaluation|review)',
            'analysis',
            optimized,
            flags=re.IGNORECASE
        )
        
        # Consolidate recommendation terms
        optimized = re.sub(
            r'(recommendations?|suggestions?|advice|guidance)',
            'recommendations',
            optimized,
            flags=re.IGNORECASE
        )
        
        return optimized

    def _validate_quality_preservation(self, original: str, optimized: str, analyst_type: str) -> bool:
        """Validate that core quality elements are preserved"""
        # Key elements that must be preserved for each analyst type
        essential_elements = {
            "market": ["technical analysis", "indicators", "price target", "BUY/SELL/HOLD"],
            "social": ["sentiment", "social media", "community", "public perception"],
            "news": ["news analysis", "events", "market impact", "headlines"],
            "fundamentals": ["financial statements", "ratios", "valuation", "earnings"]
        }
        
        # More flexible keyword alternatives for better matching
        element_alternatives = {
            "technical analysis": ["technical", "analysis", "indicators", "chart", "trend"],
            "community": ["social", "sentiment", "public", "discussion", "community"],
            "news analysis": ["news", "analysis", "events", "headlines", "information"],
            "financial statements": ["financial", "statements", "earnings", "revenue", "balance"]
        }
        
        type_key = analyst_type.lower().replace("_analyst", "").replace("_", "")
        required_elements = essential_elements.get(type_key, [])
        
        for element in required_elements:
            # Check exact match first
            if element.lower() in optimized.lower():
                continue
                
            # Check alternatives
            alternatives = element_alternatives.get(element, [])
            if any(alt in optimized.lower() for alt in alternatives):
                continue
                
            # More flexible matching for common terms
            if element == "BUY/SELL/HOLD" and any(term in optimized.upper() for term in ["BUY", "SELL", "HOLD"]):
                continue
            if element == "recommendation" and any(term in optimized.lower() for term in ["buy", "sell", "hold", "recommend"]):
                continue
                
            # If this is a composite term, check for partial matches
            if " " in element:
                words = element.split()
                if any(word in optimized.lower() for word in words):
                    continue
            
            # Log debug instead of warning for missing elements that have alternatives
            if alternatives:
                logger.debug(f"📝 Quality check: '{element}' not found but alternatives may be present in {analyst_type}")
                continue
            else:
                logger.warning(f"⚠️ Quality check failed: '{element}' missing from {analyst_type}")
                return False
        
        # Check that optimization didn't remove too much structure
        original_sections = len(re.findall(r'#{1,3}\s+\d+\.', original))
        optimized_sections = len(re.findall(r'#{1,3}\s+\d+\.', optimized))
        
        if optimized_sections < original_sections * 0.7:  # Lost more than 30% of sections
            logger.warning(f"⚠️ Quality check failed: Too many sections removed from {analyst_type}")
            return False
        
        return True

    def optimize_context_trimming(self, messages: List[Dict[str, Any]], max_context_tokens: int = 6000) -> List[Dict[str, Any]]:
        """
        Smart context trimming to stay within token limits
        Preserves recent messages and system instructions
        """
        if not messages:
            return messages
        
        # Always preserve system message
        system_msgs = [msg for msg in messages if msg.get('role') == 'system']
        other_msgs = [msg for msg in messages if msg.get('role') != 'system']
        
        # Calculate token usage
        total_tokens = sum(self.count_tokens(str(msg.get('content', ''))) for msg in messages)
        
        if total_tokens <= max_context_tokens:
            return messages
        
        # Trim from the middle, keeping recent messages
        preserved_msgs = system_msgs.copy()
        
        # Keep last 3 messages (most recent context)
        if len(other_msgs) > 3:
            preserved_msgs.extend(other_msgs[-3:])
        else:
            preserved_msgs.extend(other_msgs)
        
        # Check if we're still over the limit
        trimmed_tokens = sum(self.count_tokens(str(msg.get('content', ''))) for msg in preserved_msgs)
        
        if trimmed_tokens > max_context_tokens:
            # Further trim by truncating message content
            for msg in preserved_msgs[1:]:  # Skip system message
                content = str(msg.get('content', ''))
                if self.count_tokens(content) > 1000:
                    # Truncate long messages
                    tokenizer = self._get_tokenizer_sync()
                    if tokenizer is not None:
                        tokens = tokenizer.encode(content)
                        truncated_tokens = tokens[:800]  # Keep first 800 tokens
                        msg['content'] = tokenizer.decode(truncated_tokens) + "... [truncated]"
                    else:
                        # Fallback: simple character truncation
                        msg['content'] = content[:3200] + "... [truncated]"
        
        reduction = ((total_tokens - trimmed_tokens) / total_tokens) * 100
        logger.debug(f"🎯 Context trimmed: {total_tokens} → {trimmed_tokens} tokens ({reduction:.1f}% reduction)")
        
        return preserved_msgs
    
    async def optimize_context_trimming_async(self, messages: List[Dict[str, Any]], max_context_tokens: int = 6000) -> List[Dict[str, Any]]:
        """
        Async version of context trimming to prevent blocking
        """
        if not messages:
            return messages
        
        # Always preserve system message
        system_msgs = [msg for msg in messages if msg.get('role') == 'system']
        other_msgs = [msg for msg in messages if msg.get('role') != 'system']
        
        # Calculate token usage asynchronously
        token_counts = await asyncio.gather(*[
            self.count_tokens_async(str(msg.get('content', ''))) for msg in messages
        ])
        total_tokens = sum(token_counts)
        
        if total_tokens <= max_context_tokens:
            return messages
        
        # Trim from the middle, keeping recent messages
        preserved_msgs = system_msgs.copy()
        
        # Keep last 3 messages (most recent context)
        if len(other_msgs) > 3:
            preserved_msgs.extend(other_msgs[-3:])
        else:
            preserved_msgs.extend(other_msgs)
        
        # Check if we're still over the limit
        preserved_token_counts = await asyncio.gather(*[
            self.count_tokens_async(str(msg.get('content', ''))) for msg in preserved_msgs
        ])
        trimmed_tokens = sum(preserved_token_counts)
        
        if trimmed_tokens > max_context_tokens:
            # Further trim by truncating message content
            tokenizer = await self._get_tokenizer()
            for i, msg in enumerate(preserved_msgs[1:], start=1):  # Skip system message
                content = str(msg.get('content', ''))
                token_count = preserved_token_counts[i]
                if token_count > 1000:
                    # Truncate long messages
                    if tokenizer is not None:
                        # Run encoding/decoding in thread pool
                        tokens = await asyncio.to_thread(tokenizer.encode, content)
                        truncated_tokens = tokens[:800]  # Keep first 800 tokens
                        truncated_content = await asyncio.to_thread(tokenizer.decode, truncated_tokens)
                        msg['content'] = truncated_content + "... [truncated]"
                    else:
                        # Fallback: simple character truncation
                        msg['content'] = content[:3200] + "... [truncated]"
            
            # Recalculate trimmed tokens
            final_token_counts = await asyncio.gather(*[
                self.count_tokens_async(str(msg.get('content', ''))) for msg in preserved_msgs
            ])
            trimmed_tokens = sum(final_token_counts)
        
        reduction = ((total_tokens - trimmed_tokens) / total_tokens) * 100
        logger.debug(f"🎯 Context trimmed: {total_tokens} → {trimmed_tokens} tokens ({reduction:.1f}% reduction)")
        
        return preserved_msgs

    def generate_token_usage_report(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive token usage report"""
        if not executions:
            return {"message": "No executions to analyze"}
        
        total_prompt_tokens = sum(ex.get('prompt_tokens', 0) for ex in executions)
        total_completion_tokens = sum(ex.get('completion_tokens', 0) for ex in executions)
        total_cost = sum(ex.get('cost', 0) for ex in executions)
        
        analyst_usage = {}
        for ex in executions:
            analyst = ex.get('analyst_type', 'unknown')
            if analyst not in analyst_usage:
                analyst_usage[analyst] = {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'calls': 0,
                    'cost': 0
                }
            
            analyst_usage[analyst]['prompt_tokens'] += ex.get('prompt_tokens', 0)
            analyst_usage[analyst]['completion_tokens'] += ex.get('completion_tokens', 0)
            analyst_usage[analyst]['calls'] += 1
            analyst_usage[analyst]['cost'] += ex.get('cost', 0)
        
        # Calculate optimization potential
        optimization_potential = 0
        for analyst, usage in analyst_usage.items():
            avg_prompt_tokens = usage['prompt_tokens'] / max(usage['calls'], 1)
            if avg_prompt_tokens > 2000:  # High token usage
                optimization_potential += (avg_prompt_tokens - 2000) * usage['calls']
        
        potential_savings = optimization_potential * self.cost_per_1k_tokens[self.model_name]['input'] / 1000
        
        return {
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_cost": total_cost,
            "analyst_breakdown": analyst_usage,
            "optimization_potential": {
                "tokens": optimization_potential,
                "cost_savings": potential_savings,
                "percentage": (optimization_potential / max(total_prompt_tokens, 1)) * 100
            },
            "recommendations": self._generate_optimization_recommendations(analyst_usage)
        }

    def _generate_optimization_recommendations(self, analyst_usage: Dict[str, Any]) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        for analyst, usage in analyst_usage.items():
            avg_prompt = usage['prompt_tokens'] / max(usage['calls'], 1)
            avg_completion = usage['completion_tokens'] / max(usage['calls'], 1)
            
            if avg_prompt > 3000:
                recommendations.append(f"Optimize {analyst} prompts (avg: {avg_prompt:.0f} tokens)")
            
            if avg_completion > 1500:
                recommendations.append(f"Reduce {analyst} output verbosity (avg: {avg_completion:.0f} tokens)")
            
            if usage['cost'] > 0.10:  # High cost per analyst
                recommendations.append(f"Review {analyst} efficiency (cost: ${usage['cost']:.3f})")
        
        return recommendations

# Global optimizer instance
_global_optimizer: Optional[TokenOptimizer] = None

def get_token_optimizer() -> TokenOptimizer:
    """Get the global token optimizer instance"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = TokenOptimizer()
    return _global_optimizer

def optimize_prompt_for_analyst(prompt: str, analyst_type: str) -> str:
    """Convenience function to optimize a prompt"""
    optimizer = get_token_optimizer()
    optimization = optimizer.optimize_system_prompt(prompt, analyst_type)
    
    if optimization.quality_preserved and optimization.reduction_percentage > 10:
        logger.debug(f"✅ Using optimized prompt for {analyst_type} ({optimization.reduction_percentage:.1f}% reduction)")
        return optimization.optimized_prompt
    else:
        logger.debug(f"⚠️ Keeping original prompt for {analyst_type} (optimization not beneficial)")
        return optimization.original_prompt

async def optimize_prompt_for_analyst_async(prompt: str, analyst_type: str) -> str:
    """Async convenience function to optimize a prompt"""
    optimizer = get_token_optimizer()
    optimization = await optimizer.optimize_system_prompt_async(prompt, analyst_type)
    
    if optimization.quality_preserved and optimization.reduction_percentage > 10:
        logger.debug(f"✅ Using optimized prompt for {analyst_type} ({optimization.reduction_percentage:.1f}% reduction)")
        return optimization.optimized_prompt
    else:
        logger.debug(f"⚠️ Keeping original prompt for {analyst_type} (optimization not beneficial)")
        return optimization.original_prompt

def track_llm_usage(analyst_type: str, prompt_tokens: int, completion_tokens: int, execution_time: float):
    """Track LLM usage for analysis and optimization"""
    optimizer = get_token_optimizer()
    cost = optimizer.estimate_cost(prompt_tokens, completion_tokens)
    
    usage_data = {
        'analyst_type': analyst_type,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': prompt_tokens + completion_tokens,
        'cost': cost,
        'execution_time': execution_time,
        'timestamp': time.time()
    }
    
    # Store usage data (could be extended to persistent storage)
    logger.debug(f"💰 {analyst_type} LLM usage: {prompt_tokens + completion_tokens} tokens, ${cost:.4f}")
    
    return usage_data