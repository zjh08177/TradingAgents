#!/usr/bin/env python3
"""
Check for field type conflicts between state schemas
"""

import sys
import os
sys.path.append('src')

from agent.utils.agent_states import AgentState as OriginalState
from agent.utils.enhanced_agent_states import EnhancedAnalystState

def check_state_conflicts():
    print('🔍 Comparing field types between state schemas...')
    print('=' * 60)
    
    # Get annotations for both states
    orig_annotations = OriginalState.__annotations__
    enhanced_annotations = EnhancedAnalystState.__annotations__
    
    print(f'📊 Original AgentState fields: {len(orig_annotations)}')
    print(f'📊 Enhanced AgentState fields: {len(enhanced_annotations)}')
    
    # Find common fields
    common_fields = set(orig_annotations.keys()) & set(enhanced_annotations.keys())
    print(f'📊 Common fields: {len(common_fields)}')
    
    # Check for type conflicts
    conflicts = []
    for field in common_fields:
        orig_type = str(orig_annotations[field])
        enhanced_type = str(enhanced_annotations[field])
        
        if orig_type != enhanced_type:
            conflicts.append((field, orig_type, enhanced_type))
    
    if conflicts:
        print(f'\n⚠️ Found {len(conflicts)} type conflicts:')
        for field, orig, enhanced in conflicts:
            print(f'   {field}:')
            print(f'     Original: {orig}')
            print(f'     Enhanced: {enhanced}')
    else:
        print('\n✅ No type conflicts found!')
    
    print(f'\n📋 Common fields: {sorted(common_fields)}')
    
    return len(conflicts) == 0

if __name__ == "__main__":
    success = check_state_conflicts()
    if not success:
        sys.exit(1)