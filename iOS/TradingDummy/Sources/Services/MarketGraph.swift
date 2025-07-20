import Foundation
import LangGraph
import OpenAI

public func runMarketAgent(input: String, llm: LLM, tools: [BaseTool]) async throws -> Void {
    
    let agent = {
        let output_parser = ToolOutputParser()
        let llm_chain = LLMChain(llm: llm,
                                prompt: ZeroShotAgent.create_prompt(tools: tools),
                                parser: output_parser,
                                stop: ["\nObservation: ", "\n\tObservation: "])
        return ZeroShotAgent(llm_chain: llm_chain)
    }()
    
    let toolExecutor = { (action: AgentAction) in
        guard let tool = tools.filter({$0.name() == action.action}).first else {
            throw CompiledGraphError.executionError("tool \(action.action) not found!")
        }
        
        print("calling \(tool.name()) tool.")
        var observation = try await tool.run(args: action.input)
        if observation.count > 1000 {
            observation = String(observation.prefix(1000))
        }
        return observation
    }
    
    let workflow = StateGraph(channels: MarketState.schema) {
        MarketState($0)
    }
    
    try workflow.addNode("call_agent") { state in
        guard let input = state.input else {
            throw CompiledGraphError.executionError("'input' not found in state!")
        }
        guard let intermediate_steps = state.intermediate_steps else {
            throw CompiledGraphError.executionError("'intermediate_steps' not found in state!")
        }
        
        let step = await agent.plan(input: input, intermediate_steps: intermediate_steps)
        switch step {
        case .finish(let finish):
            return ["agent_outcome": AgentOutcome.finish(finish)]
        case .action(let action):
            return ["agent_outcome": AgentOutcome.action(action)]
        default:
            throw CompiledGraphError.executionError("Parsed.error")
        }
    }
    
    try workflow.addNode("call_tool") { state in
        guard let agentOutcome = state.agentOutcome else {
            throw CompiledGraphError.executionError("'agent_outcome' not found in state!")
        }
        
        guard case .action(let action) = agentOutcome else {
            throw CompiledGraphError.executionError("'agent_outcome' is not an action!")
        }
        
        let result = try await toolExecutor(action)
        return ["intermediate_steps": (action, result)]
    }
    
    try workflow.addEdge(sourceId: START, targetId: "call_agent")
    try workflow.addEdge(sourceId: "call_tool", targetId: "call_agent")
    
    try workflow.addConditionalEdge(sourceId: "call_agent", condition: { state in
        guard let agentOutcome = state.agentOutcome else {
            throw CompiledGraphError.executionError("'agent_outcome' not found in state!")
        }
        
        return switch agentOutcome {
        case .finish:
            "finish"
        case .action:
            "continue"
        }
    }, edgeMapping: [
        "continue": "call_tool",
        "finish": END
    ])
    
    let runner = try workflow.compile()
    
    for try await result in runner.stream(inputs: ["input": input]) {
        print("-------------")
        print("Agent Output of \(result.node)")
        print(result.state)
    }
    print("-------------")
} 
