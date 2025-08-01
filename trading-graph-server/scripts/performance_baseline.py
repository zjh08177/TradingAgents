#!/usr/bin/env python3
"""
Performance baseline measurement script
Captures current performance metrics before optimization
"""

import time
import sys
import os
import asyncio
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def measure_sync_token_counting():
    """Measure current synchronous token counting performance"""
    from agent.utils.token_optimizer import TokenOptimizer
    
    optimizer = TokenOptimizer()
    test_texts = [
        "Short text",
        "Medium length text that contains more words and should take more tokens to process",
        "A very long text that simulates a typical agent prompt with lots of context and instructions " * 10
    ]
    
    results = []
    for text in test_texts:
        start = time.time()
        tokens = optimizer.count_tokens(text)
        duration = time.time() - start
        results.append({
            "text_length": len(text),
            "tokens": tokens,
            "duration": duration
        })
    
    return results

def measure_prompt_optimization():
    """Measure current prompt optimization performance"""
    from agent.utils.token_optimizer import TokenOptimizer
    
    optimizer = TokenOptimizer()
    test_prompt = """
    You are a market analyst tasked with analyzing the current market conditions.
    Please provide comprehensive analysis including technical indicators, market sentiment,
    recent news impact, and your trading recommendation.
    """
    
    start = time.time()
    result = optimizer.optimize_system_prompt(test_prompt, "market_analyst")
    duration = time.time() - start
    
    return {
        "original_tokens": result.original_tokens,
        "optimized_tokens": result.optimized_tokens,
        "reduction": result.reduction_percentage,
        "duration": duration
    }

def measure_tokenizer_initialization():
    """Measure tokenizer initialization time"""
    import tiktoken
    
    models = ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
    results = []
    
    for model in models:
        start = time.time()
        try:
            tokenizer = tiktoken.encoding_for_model(model)
        except:
            tokenizer = tiktoken.get_encoding("cl100k_base")
        duration = time.time() - start
        
        results.append({
            "model": model,
            "init_duration": duration
        })
    
    return results

async def measure_agent_processing():
    """Simulate agent prompt processing"""
    from agent.utils.token_optimizer import TokenOptimizer
    from agent.utils.prompt_compressor import AdvancedPromptCompressor
    from agent.utils.agent_prompt_enhancer import AgentPromptEnhancer
    
    agents = [
        "market_analyst", "news_analyst", "social_media_analyst",
        "fundamentals_analyst", "risk_manager", "trader"
    ]
    
    optimizer = TokenOptimizer()
    compressor = AdvancedPromptCompressor()
    enhancer = AgentPromptEnhancer()
    
    results = []
    for agent in agents:
        prompt = f"Test prompt for {agent} with some context"
        
        start = time.time()
        # Compress
        compressed = compressor.compress_prompt(prompt)
        # Enhance
        enhanced = enhancer.enhance_prompt(compressed.compressed, agent)
        # Count tokens
        tokens = optimizer.count_tokens(enhanced)
        duration = time.time() - start
        
        results.append({
            "agent": agent,
            "duration": duration,
            "tokens": tokens
        })
    
    return results

def generate_baseline_report():
    """Generate comprehensive baseline report"""
    print("="*60)
    print("Performance Baseline Measurement")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "measurements": {}
    }
    
    # Test 1: Token Counting
    print("\n1. Token Counting Performance:")
    token_results = measure_sync_token_counting()
    for result in token_results:
        print(f"   Text length {result['text_length']}: {result['duration']:.4f}s ({result['tokens']} tokens)")
    baseline["measurements"]["token_counting"] = token_results
    
    # Test 2: Prompt Optimization
    print("\n2. Prompt Optimization Performance:")
    opt_result = measure_prompt_optimization()
    print(f"   Duration: {opt_result['duration']:.4f}s")
    print(f"   Reduction: {opt_result['reduction']:.1f}%")
    baseline["measurements"]["prompt_optimization"] = opt_result
    
    # Test 3: Tokenizer Initialization
    print("\n3. Tokenizer Initialization:")
    init_results = measure_tokenizer_initialization()
    for result in init_results:
        print(f"   {result['model']}: {result['init_duration']:.4f}s")
    baseline["measurements"]["tokenizer_init"] = init_results
    
    # Test 4: Agent Processing
    print("\n4. Agent Processing Simulation:")
    agent_results = asyncio.run(measure_agent_processing())
    total_duration = sum(r['duration'] for r in agent_results)
    for result in agent_results:
        print(f"   {result['agent']}: {result['duration']:.4f}s")
    print(f"   Total: {total_duration:.4f}s")
    baseline["measurements"]["agent_processing"] = agent_results
    
    # Save baseline
    output_file = "performance_baseline.json"
    with open(output_file, 'w') as f:
        json.dump(baseline, f, indent=2)
    
    print(f"\n✅ Baseline saved to: {output_file}")
    print("\nSummary:")
    print(f"- Average token counting: {sum(r['duration'] for r in token_results)/len(token_results):.4f}s")
    print(f"- Total agent processing: {total_duration:.4f}s")
    print(f"- Expected overhead for 24 agents: {total_duration * 4:.2f}s")
    
    return baseline

if __name__ == "__main__":
    generate_baseline_report()