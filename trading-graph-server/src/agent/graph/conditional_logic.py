# TradingAgents/graph/conditional_logic.py

# Import AgentState from local module
from ..utils.agent_states import AgentState
import logging

logger = logging.getLogger(__name__)

class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_market(self, state: AgentState):
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""
        logger.info("🔄 DEBATE CONDITIONAL: Starting evaluation")
        
        debate_state = state["investment_debate_state"]
        count = debate_state["count"]
        current_response = debate_state.get("current_response", "")
        max_rounds = 2 * self.max_debate_rounds
        
        logger.info(f"🔄 DEBATE CONDITIONAL: Count={count}, Max={max_rounds}")
        logger.info(f"🔄 DEBATE CONDITIONAL: Current response starts with: '{current_response[:50]}...'")

        if count >= max_rounds:  # 3 rounds of back-and-forth between 2 agents
            logger.info("🔄 DEBATE CONDITIONAL: → Research Manager (max rounds reached)")
            return "Research Manager"
        
        if current_response.startswith("Bull"):
            logger.info("🔄 DEBATE CONDITIONAL: → Bear Researcher (Bull just spoke)")
            return "Bear Researcher"
        
        logger.info("🔄 DEBATE CONDITIONAL: → Bull Researcher (default/Bear just spoke)")
        return "Bull Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            return "Risk Judge"
        if state["risk_debate_state"]["latest_speaker"].startswith("Risky"):
            return "Safe Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("Safe"):
            return "Neutral Analyst"
        return "Risky Analyst"
