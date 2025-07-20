import Foundation
import LangGraph

enum AgentOutcome {
    case action(AgentAction)
    case finish(AgentFinish)
}

struct ToolOutputParser: BaseOutputParser {
    public init() {}
    
    public func parse(text: String) -> Parsed {
        print("\n-------\n\(text.uppercased())\n-------\n")
        let pattern = "Action\\s*:[\\s]*(.*)[\\s]*Action\\s*Input\\s*:[\\s]*(.*)"
        let regex = try! NSRegularExpression(pattern: pattern)
        
        if let match = regex.firstMatch(in: text, options: [], range: NSRange(location: 0, length: text.utf16.count)) {
            
            let firstCaptureGroup = Range(match.range(at: 1), in: text).map { String(text[$0]) }
            let secondCaptureGroup = Range(match.range(at: 2), in: text).map { String(text[$0]) }
            
            return Parsed.action(AgentAction(action: firstCaptureGroup!, input: secondCaptureGroup!, log: text))
        } else {
            if text.uppercased().contains(FINAL_ANSWER_ACTION) {
                return Parsed.finish(AgentFinish(final: text))
            }
            return Parsed.error
        }
    }
} 
