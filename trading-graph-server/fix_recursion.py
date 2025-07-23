#!/usr/bin/env python3
"""
Fix the recursion issue in graph routing
"""

with open('src/agent/graph/setup.py', 'r') as f:
    content = f.read()

# Replace the routing function
old_routing = '''    def _create_analyst_routing(self, analyst_type: str):
        """Create routing logic for analyst nodes"""
        def route(state: AgentState) -> str:
            messages = state.get(f"{analyst_type}_messages", [])
            if not messages:
                return "aggregator"
            
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return f"{analyst_type}_tools"
            return "aggregator"
        
        return route'''

new_routing = '''    def _create_analyst_routing(self, analyst_type: str):
        """Create routing logic for analyst nodes with loop prevention"""
        def route(state: AgentState) -> str:
            messages = state.get(f"{analyst_type}_messages", [])
            if not messages:
                return "aggregator"
            
            # Count tool calls to prevent infinite loops
            tool_call_count = sum(1 for msg in messages if hasattr(msg, 'tool_calls') and msg.tool_calls)
            
            # Limit to max 3 tool call cycles per analyst to prevent recursion
            if tool_call_count >= 3:
                return "aggregator"
            
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return f"{analyst_type}_tools"
            return "aggregator"
        
        return route'''

content = content.replace(old_routing, new_routing)

with open('src/agent/graph/setup.py', 'w') as f:
    f.write(content)

print("✅ Fixed recursion logic in setup.py")
