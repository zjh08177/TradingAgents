import Foundation

// MARK: - Request Model
struct AnalysisRequest: Codable {
    let ticker: String
}

// MARK: - Response Model
struct AnalysisResponse: Codable {
    let ticker: String
    let analysisDate: String
    let marketReport: String?
    let sentimentReport: String?
    let newsReport: String?
    let fundamentalsReport: String?
    let investmentPlan: String?
    let traderInvestmentPlan: String?
    let finalTradeDecision: String?
    let processedSignal: String?
    let error: String?
    
    enum CodingKeys: String, CodingKey {
        case ticker
        case analysisDate = "analysis_date"
        case marketReport = "market_report"
        case sentimentReport = "sentiment_report"
        case newsReport = "news_report"
        case fundamentalsReport = "fundamentals_report"
        case investmentPlan = "investment_plan"
        case traderInvestmentPlan = "trader_investment_plan"
        case finalTradeDecision = "final_trade_decision"
        case processedSignal = "processed_signal"
        case error
    }
}

// MARK: - Live Activity Models
public struct AgentMessage: Identifiable, Equatable {
    public let id = UUID()
    public let timestamp: Date
    public let content: String
    public let type: MessageType
    
    public enum MessageType {
        case reasoning      // Intermediate thinking/reasoning
        case toolCall      // Tool execution
        case status        // Status updates
        case finalReport   // Complete analysis report
    }
    
    public init(content: String, type: MessageType) {
        self.content = content
        self.type = type
        self.timestamp = Date()
    }
}

public struct AgentActivity: Identifiable, Equatable {
    public let id = UUID()
    public let name: String
    public let displayName: String
    public var status: AgentStatus
    public var messages: [AgentMessage]
    public var finalReport: String?
    public let startTime: Date
    public var completionTime: Date?
    
    public enum AgentStatus: Equatable {
        case pending
        case inProgress
        case completed
        case error(String)
        
        public static func == (lhs: AgentStatus, rhs: AgentStatus) -> Bool {
            switch (lhs, rhs) {
            case (.pending, .pending),
                 (.inProgress, .inProgress),
                 (.completed, .completed):
                return true
            case (.error(let lhsMessage), .error(let rhsMessage)):
                return lhsMessage == rhsMessage
            default:
                return false
            }
        }
    }
    
    public init(name: String, displayName: String) {
        self.name = name
        self.displayName = displayName
        self.status = .pending
        self.messages = []
        self.finalReport = nil
        self.startTime = Date()
        self.completionTime = nil
    }
    
    public mutating func addMessage(_ message: AgentMessage) {
        messages.append(message)
    }
    
    public mutating func setFinalReport(_ report: String) {
        finalReport = report
        // Replace reasoning messages with final report
        messages.removeAll { $0.type == .reasoning }
        messages.append(AgentMessage(content: report, type: .finalReport))
    }
    
    public mutating func updateStatus(_ newStatus: AgentStatus) {
        status = newStatus
        if case .completed = newStatus {
            completionTime = Date()
        }
    }
    
    public static func == (lhs: AgentActivity, rhs: AgentActivity) -> Bool {
        lhs.id == rhs.id
    }
} 