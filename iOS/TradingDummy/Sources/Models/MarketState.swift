import Foundation
import LangGraph

public struct MarketState: AgentState {
    
    static var schema: Channels = {
        [
            "intermediate_steps": AppenderChannel<(AgentAction, String)>(),
        ]
    }()
    
    public var data: [String: Any]
    
    public init(_ initState: [String: Any]) {
        self.data = initState
    }
    
    public init(input: String) {
        self.data = [
            "input": input,
            "market_report": ""
        ]
    }
    
    var input: String? {
        value("input")
    }
    
    var agentOutcome: AgentOutcome? {
        value("agent_outcome")
    }
    
    var intermediate_steps: [(AgentAction, String)]? {
        value("intermediate_steps")
    }
    
    var marketReport: String {
        value("market_report") ?? ""
    }
} 
