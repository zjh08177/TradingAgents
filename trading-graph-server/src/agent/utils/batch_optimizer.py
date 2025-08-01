#!/usr/bin/env python3
"""
Batch Prompt Optimizer - Phase 3 Performance Optimization
Processes multiple prompts in parallel to reduce overall processing time
"""

import asyncio
import logging
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    """Result of batch prompt processing"""
    processed_prompts: List[str]
    processing_times: List[float]
    total_time: float
    speedup: float
    errors: List[Optional[str]]

class BatchPromptOptimizer:
    """
    Processes multiple agent prompts in parallel to improve performance
    Coordinates token optimization, compression, and enhancement
    """
    
    def __init__(self, optimizer=None, compressor=None, enhancer=None):
        """
        Initialize batch optimizer with processing components
        
        Args:
            optimizer: TokenOptimizer instance (will be imported if not provided)
            compressor: PromptCompressor instance (will be imported if not provided)
            enhancer: AgentPromptEnhancer instance (will be imported if not provided)
        """
        # Lazy imports to avoid circular dependencies
        if optimizer is None:
            from .token_optimizer import get_token_optimizer
            self.optimizer = get_token_optimizer()
        else:
            self.optimizer = optimizer
            
        if compressor is None:
            from .prompt_compressor import AdvancedPromptCompressor
            self.compressor = AdvancedPromptCompressor()
        else:
            self.compressor = compressor
            
        if enhancer is None:
            from .agent_prompt_enhancer import AgentPromptEnhancer
            self.enhancer = AgentPromptEnhancer()
        else:
            self.enhancer = enhancer
        
        logger.debug("🚀 BatchPromptOptimizer initialized")
    
    async def process_prompts_parallel(
        self, 
        prompts: List[Tuple[str, str]],  # [(prompt, agent_type), ...]
        max_concurrent: int = 10
    ) -> BatchResult:
        """
        Process multiple prompts in parallel with concurrency control
        
        Args:
            prompts: List of (prompt, agent_type) tuples
            max_concurrent: Maximum number of concurrent processing tasks
            
        Returns:
            BatchResult with processed prompts and performance metrics
        """
        if not prompts:
            return BatchResult(
                processed_prompts=[],
                processing_times=[],
                total_time=0.0,
                speedup=1.0,
                errors=[]
            )
        
        logger.debug(f"🎯 Processing {len(prompts)} prompts in parallel (max concurrent: {max_concurrent})")
        
        # Start timing
        start_time = time.time()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Process all prompts with controlled concurrency
        tasks = []
        for i, (prompt, agent_type) in enumerate(prompts):
            task = self._process_with_semaphore(semaphore, i, prompt, agent_type)
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_prompts = []
        processing_times = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle errors gracefully
                logger.warning(f"⚠️ Error processing prompt {i}: {result}")
                processed_prompts.append(prompts[i][0])  # Use original prompt as fallback
                processing_times.append(0.0)
                errors.append(str(result))
            else:
                processed_prompt, proc_time = result
                processed_prompts.append(processed_prompt)
                processing_times.append(proc_time)
                errors.append(None)
        
        # Calculate total time and speedup
        total_time = time.time() - start_time
        sequential_estimate = sum(processing_times) if processing_times else total_time
        speedup = sequential_estimate / total_time if total_time > 0 else 1.0
        
        logger.debug(f"✅ Batch processing complete: {len(prompts)} prompts in {total_time:.3f}s (speedup: {speedup:.1f}x)")
        
        return BatchResult(
            processed_prompts=processed_prompts,
            processing_times=processing_times,
            total_time=total_time,
            speedup=speedup,
            errors=errors
        )
    
    async def _process_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        index: int,
        prompt: str, 
        agent_type: str
    ) -> Tuple[str, float]:
        """Process a single prompt with semaphore for concurrency control"""
        async with semaphore:
            return await self._process_single_prompt(index, prompt, agent_type)
    
    async def _process_single_prompt(self, index: int, prompt: str, agent_type: str) -> Tuple[str, float]:
        """
        Process a single prompt through the optimization pipeline
        
        Returns:
            Tuple of (processed_prompt, processing_time)
        """
        start_time = time.time()
        
        try:
            # Step 1: Compress the prompt
            if hasattr(self.compressor, 'compress_prompt_async'):
                compressed_result = await self.compressor.compress_prompt_async(prompt)
                compressed_prompt = compressed_result.compressed if hasattr(compressed_result, 'compressed') else compressed_result
            else:
                # Fallback to sync version in thread
                compressed_result = await asyncio.to_thread(self.compressor.compress_prompt, prompt)
                compressed_prompt = compressed_result.compressed if hasattr(compressed_result, 'compressed') else compressed_result
            
            # Step 2: Enhance the prompt for the specific agent
            if hasattr(self.enhancer, 'enhance_prompt_async'):
                enhanced_prompt = await self.enhancer.enhance_prompt_async(compressed_prompt, agent_type)
            else:
                # Fallback to sync version in thread
                enhanced_prompt = await asyncio.to_thread(self.enhancer.enhance_prompt, compressed_prompt, agent_type)
            
            # Step 3: Optimize tokens if the optimizer has async support
            if hasattr(self.optimizer, 'optimize_system_prompt_async'):
                optimization = await self.optimizer.optimize_system_prompt_async(enhanced_prompt, agent_type)
                final_prompt = optimization.optimized_prompt if optimization.quality_preserved else enhanced_prompt
            else:
                # Use enhanced prompt as-is
                final_prompt = enhanced_prompt
            
            processing_time = time.time() - start_time
            logger.debug(f"  Prompt {index} ({agent_type}): {processing_time:.3f}s")
            
            return final_prompt, processing_time
            
        except Exception as e:
            logger.error(f"Error processing prompt {index} ({agent_type}): {e}")
            raise
    
    async def batch_optimize_agents(
        self,
        agent_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Optimize prompts for multiple agents based on their configurations
        
        Args:
            agent_configs: Dictionary mapping agent_type to config dict with 'prompt' key
            
        Returns:
            Dictionary mapping agent_type to optimized prompt
        """
        # Extract prompts and agent types
        prompts = []
        agent_types = []
        
        for agent_type, config in agent_configs.items():
            if 'prompt' in config:
                prompts.append((config['prompt'], agent_type))
                agent_types.append(agent_type)
        
        # Process in batch
        result = await self.process_prompts_parallel(prompts)
        
        # Build result dictionary
        optimized_prompts = {}
        for i, agent_type in enumerate(agent_types):
            if result.errors[i] is None:
                optimized_prompts[agent_type] = result.processed_prompts[i]
            else:
                # Fallback to original prompt on error
                optimized_prompts[agent_type] = agent_configs[agent_type]['prompt']
                logger.warning(f"Using original prompt for {agent_type} due to error: {result.errors[i]}")
        
        return optimized_prompts
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for batch processing"""
        # This could be extended to track historical performance
        return {
            "optimizer": "BatchPromptOptimizer",
            "supported_operations": ["compress", "enhance", "optimize"],
            "max_concurrent": 10,
            "async_enabled": True
        }

# Global instance for easy access
_batch_optimizer: Optional[BatchPromptOptimizer] = None

def get_batch_optimizer() -> BatchPromptOptimizer:
    """Get the global batch optimizer instance"""
    global _batch_optimizer
    if _batch_optimizer is None:
        _batch_optimizer = BatchPromptOptimizer()
    return _batch_optimizer

async def batch_process_prompts(
    prompts: List[Tuple[str, str]], 
    max_concurrent: int = 10
) -> BatchResult:
    """Convenience function for batch processing prompts"""
    optimizer = get_batch_optimizer()
    return await optimizer.process_prompts_parallel(prompts, max_concurrent)