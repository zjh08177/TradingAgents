from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"  # Use OpenAI provider
config["backend_url"] = "https://api.openai.com/v1"  # Use OpenAI backend
config["deep_think_llm"] = "gpt-4o-mini"  # Use valid OpenAI model
config["quick_think_llm"] = "gpt-4o-mini"  # Use valid OpenAI model
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = True  # Increase debate rounds

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
