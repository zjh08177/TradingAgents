#!/usr/bin/env python3
"""
Batch Prompt Processor for Graph Setup - Phase 3.2 Performance Optimization
Collects and processes all analyst prompts in parallel during graph initialization
"""

import asyncio
import logging
import time
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

# Removed stale imports:
# - batch_optimizer (deleted - unused)
# - token_optimizer (to be reviewed for deletion)
from ..utils.prompt_compressor import get_prompt_compressor
from ..utils.agent_prompt_enhancer import get_prompt_enhancer

logger = logging.getLogger(__name__)

@dataclass
class ProcessedPrompts:
    """Container for processed prompts with metadata"""
    prompts: Dict[str, str]  # agent_type -> processed_prompt
    processing_time: float
    token_savings: int
    speedup: float


class GraphPromptBatchProcessor:
    """
    Batch processes all analyst prompts during graph initialization
    Implements Phase 3.2 of the performance optimization plan
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the batch processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        # STALE CODE - DISABLED: These optimizers were removed during cleanup
        # self.batch_optimizer = get_batch_optimizer()
        self.compressor = get_prompt_compressor()
        self.enhancer = get_prompt_enhancer()
        # self.token_optimizer = get_token_optimizer()
        
        # Cache for processed prompts to avoid reprocessing
        self._prompt_cache: Dict[str, str] = {}
        
        logger.debug("🚀 GraphPromptBatchProcessor initialized")
    
    async def process_analyst_prompts_batch(
        self, 
        analyst_configs: Dict[str, Dict[str, Any]]
    ) -> ProcessedPrompts:
        """
        Process all analyst prompts in parallel batch
        
        Args:
            analyst_configs: Dictionary of analyst configurations
                {
                    "market": {"base_prompt": "...", "config": {...}},
                    "news": {"base_prompt": "...", "config": {...}},
                    ...
                }
        
        Returns:
            ProcessedPrompts with optimized prompts and metadata
        """
        if not analyst_configs:
            return ProcessedPrompts(
                prompts={},
                processing_time=0.0,
                token_savings=0,
                speedup=1.0
            )
        
        logger.info(f"📦 Batch processing {len(analyst_configs)} analyst prompts")
        
        # Start timing
        start_time = time.time()
        
        # Extract prompts for batch processing
        prompts_to_process = []
        agent_types = []
        original_tokens = 0
        
        for agent_type, config in analyst_configs.items():
            # Check cache first
            cache_key = f"{agent_type}:{hash(config.get('base_prompt', ''))}"
            if cache_key in self._prompt_cache:
                logger.debug(f"✅ Using cached prompt for {agent_type}")
                continue
                
            base_prompt = config.get('base_prompt', '')
            if base_prompt:
                prompts_to_process.append((base_prompt, agent_type))
                agent_types.append(agent_type)
                original_tokens += len(base_prompt) // 4  # Simple token estimate
        
        # If all prompts are cached, return cached results
        if not prompts_to_process:
            logger.info("📦 All prompts already cached")
            cached_prompts = {}
            for agent_type in analyst_configs:
                cache_key = f"{agent_type}:{hash(analyst_configs[agent_type].get('base_prompt', ''))}"
                if cache_key in self._prompt_cache:
                    cached_prompts[agent_type] = self._prompt_cache[cache_key]
            
            return ProcessedPrompts(
                prompts=cached_prompts,
                processing_time=0.0,
                token_savings=0,
                speedup=100.0  # Cached is essentially infinite speedup
            )
        
        # Process prompts in parallel
        logger.info(f"⚡ Processing {len(prompts_to_process)} prompts in parallel")
        
        # STALE CODE - DISABLED: Batch optimizer was removed, using fallback
        # result = await self.batch_optimizer.process_prompts_parallel(
        #     prompts_to_process,
        #     max_concurrent=8  # Increased concurrency for analyst prompts
        # )
        
        # Simple fallback: return original prompts
        from dataclasses import dataclass
        @dataclass
        class FallbackResult:
            processed_prompts: List[str]
            errors: List[None]
            speedup: float
        
        processed_prompts_list = [prompt for prompt, _ in prompts_to_process]
        result = FallbackResult(
            processed_prompts=processed_prompts_list,
            errors=[None] * len(prompts_to_process),
            speedup=1.0
        )
        
        # Build processed prompts dictionary
        processed_prompts = {}
        compressed_tokens = 0
        
        for i, agent_type in enumerate(agent_types):
            if result.errors[i] is None:
                processed_prompt = result.processed_prompts[i]
                processed_prompts[agent_type] = processed_prompt
                
                # Cache the processed prompt
                cache_key = f"{agent_type}:{hash(analyst_configs[agent_type].get('base_prompt', ''))}"
                self._prompt_cache[cache_key] = processed_prompt
                
                compressed_tokens += len(processed_prompt) // 4  # Simple token estimate
            else:
                # Fallback to original prompt on error
                logger.warning(f"⚠️ Failed to process {agent_type} prompt: {result.errors[i]}")
                processed_prompts[agent_type] = analyst_configs[agent_type].get('base_prompt', '')
                compressed_tokens += len(analyst_configs[agent_type].get('base_prompt', '')) // 4  # Simple token estimate
        
        # Add cached prompts that weren't reprocessed
        for agent_type in analyst_configs:
            if agent_type not in processed_prompts:
                cache_key = f"{agent_type}:{hash(analyst_configs[agent_type].get('base_prompt', ''))}"
                if cache_key in self._prompt_cache:
                    processed_prompts[agent_type] = self._prompt_cache[cache_key]
        
        # Calculate metrics
        processing_time = time.time() - start_time
        token_savings = original_tokens - compressed_tokens if original_tokens > 0 else 0
        
        logger.info(f"📦 Batch processing complete:")
        logger.info(f"   - Time: {processing_time:.3f}s")
        logger.info(f"   - Speedup: {result.speedup:.1f}x")
        logger.info(f"   - Token savings: {token_savings} tokens")
        logger.info(f"   - Prompts processed: {len(processed_prompts)}")
        
        return ProcessedPrompts(
            prompts=processed_prompts,
            processing_time=processing_time,
            token_savings=token_savings,
            speedup=result.speedup
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the prompt cache"""
        return {
            "cached_prompts": len(self._prompt_cache),
            "cache_keys": list(self._prompt_cache.keys()),
            "memory_usage": sum(len(v) for v in self._prompt_cache.values())
        }
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._prompt_cache.clear()
        logger.info("🗑️ Prompt cache cleared")


# Global instance for easy access
_graph_prompt_processor: Optional[GraphPromptBatchProcessor] = None

def get_graph_prompt_processor(config: Optional[Dict[str, Any]] = None) -> GraphPromptBatchProcessor:
    """Get the global graph prompt processor instance"""
    global _graph_prompt_processor
    if _graph_prompt_processor is None:
        _graph_prompt_processor = GraphPromptBatchProcessor(config)
    return _graph_prompt_processor


async def batch_process_graph_prompts(
    analyst_configs: Dict[str, Dict[str, Any]]
) -> ProcessedPrompts:
    """Convenience function for batch processing graph prompts"""
    processor = get_graph_prompt_processor()
    return await processor.process_analyst_prompts_batch(analyst_configs)