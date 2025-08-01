#!/usr/bin/env python3
"""
Apply Token Optimization to All Agents
Updates all agent files to use the token optimization system
"""

import os
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def update_agent_file(filepath: str, agent_type: str):
    """Update an agent file to use token optimization"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if already optimized
    if "enhance_agent_prompt" in content and "compress_prompt" in content:
        print(f"✅ {filepath} already optimized")
        return False
    
    # Find the imports section
    import_pattern = r'(from langchain_core\.prompts.*\n)(import.*\n)*'
    
    # Add new imports after existing ones
    new_imports = """from agent.utils.token_limiter import get_token_limiter
from agent.utils.connection_retry import safe_llm_invoke
from agent.utils.parallel_tools import log_parallel_execution
from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt
from agent.utils.agent_prompt_enhancer import enhance_agent_prompt
"""
    
    # Check if imports already exist
    has_limiter = "from agent.utils.token_limiter" in content
    has_compressor = "from agent.utils.prompt_compressor" in content
    has_enhancer = "from agent.utils.agent_prompt_enhancer" in content
    
    if not (has_limiter and has_compressor and has_enhancer):
        # Find last import and add new ones
        import_lines = content.split('\n')
        last_import_idx = 0
        for i, line in enumerate(import_lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
        
        # Insert new imports
        if not has_limiter:
            import_lines.insert(last_import_idx + 1, "from agent.utils.token_limiter import get_token_limiter")
        if not has_compressor:
            import_lines.insert(last_import_idx + 1, "from agent.utils.prompt_compressor import get_prompt_compressor, compress_prompt")
        if not has_enhancer:
            import_lines.insert(last_import_idx + 1, "from agent.utils.agent_prompt_enhancer import enhance_agent_prompt")
        
        content = '\n'.join(import_lines)
    
    # Find system message definition
    system_msg_pattern = r'(system_message\s*=\s*)("""[\s\S]*?""")'
    
    def replace_system_message(match):
        prefix = match.group(1)
        original_msg = match.group(2)
        
        # Add compression logic
        replacement = f'''"""[Original system message - will be compressed]"""

        # Compress the system message
        base_system_message = {original_msg}
        compressor = get_prompt_compressor()
        compressed_result = compressor.compress_prompt(base_system_message)
        system_message = compressed_result.compressed
        
        # Add word limit enforcement
        system_message = enhance_agent_prompt(system_message, "{agent_type}")
        
        logger.info(f"📊 {agent_type.replace('_', ' ').title()} prompt compression: {{compressed_result.original_tokens}} → {{compressed_result.compressed_tokens}} tokens ({{compressed_result.reduction_percentage:.1f}}% reduction)")'''
        
        return replacement
    
    # Apply system message update
    if 'system_message =' in content and 'compress_prompt' not in content:
        content = re.sub(system_msg_pattern, replace_system_message, content, flags=re.DOTALL)
    
    # Enable token limiting (uncomment if commented)
    content = re.sub(
        r'#\s*messages\s*=\s*get_token_limiter\(\)\.check_and_enforce_limit\(messages,\s*"[^"]+"\)',
        r'messages = get_token_limiter().check_and_enforce_limit(messages, "{}")'.format(
            agent_type.replace('_', ' ').title()
        ),
        content
    )
    
    # Write updated content
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✨ Updated {filepath}")
    return True

def main():
    """Apply optimization to all agent files"""
    
    base_dir = Path(__file__).parent.parent / "src" / "agent"
    
    # Agent files to update
    agent_files = [
        ("analysts/news_analyst.py", "news_analyst"),
        ("analysts/social_media_analyst.py", "social_media_analyst"),
        ("analysts/fundamentals_analyst.py", "fundamentals_analyst"),
        ("managers/research_manager.py", "research_manager"),
        ("managers/risk_manager.py", "risk_manager"),
        ("researchers/bull_researcher.py", "bull_researcher"),
        ("researchers/bear_researcher.py", "bear_researcher"),
        ("trader/trader.py", "trader"),
        ("risk_mgmt/aggresive_debator.py", "aggressive_debator"),
        ("risk_mgmt/conservative_debator.py", "conservative_debator"),
        ("risk_mgmt/neutral_debator.py", "neutral_debator")
    ]
    
    updated_count = 0
    
    print("🚀 Applying token optimization to all agents...")
    print("-" * 50)
    
    for relative_path, agent_type in agent_files:
        filepath = base_dir / relative_path
        if filepath.exists():
            if update_agent_file(str(filepath), agent_type):
                updated_count += 1
        else:
            print(f"❌ File not found: {filepath}")
    
    print("-" * 50)
    print(f"✅ Updated {updated_count} files")
    print("\n📝 Next steps:")
    print("1. Review the updated files")
    print("2. Test with debug_local.sh")
    print("3. Monitor token usage reduction")

if __name__ == "__main__":
    main()