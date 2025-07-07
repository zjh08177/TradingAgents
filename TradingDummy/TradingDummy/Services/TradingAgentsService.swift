import Foundation
import Combine
import OSLog

// MARK: - SSE Event Model
struct SSEEvent: Codable {
    let type: String
    let message: String?
    let agent: String?
    let status: String?
    let section: String?
    let content: String?
}

// MARK: - Enhanced Progress Models
public struct AnalysisProgress {
    public let currentAgent: String
    public let message: String
    public let reports: [String: String]
    public let agentActivities: [String: AgentActivity]
    public let isComplete: Bool
    public let error: String?
    
    public init(currentAgent: String, message: String, reports: [String: String], agentActivities: [String: AgentActivity], isComplete: Bool, error: String?) {
        self.currentAgent = currentAgent
        self.message = message
        self.reports = reports
        self.agentActivities = agentActivities
        self.isComplete = isComplete
        self.error = error
    }
}

// MARK: - TradingAgentsService
public class TradingAgentsService: ObservableObject {
    internal let logger = Logger(subsystem: "com.tradingagents.app", category: "TradingAgentsService")
    
    private var eventSource: URLSessionDataTask?
    private var streamingDelegate: SSEStreamDelegate?
    private let session: URLSession
    
    @Published var isAnalyzing = false
    @Published var progress = AnalysisProgress(
        currentAgent: "",
        message: "",
        reports: [:],
        agentActivities: [:],
        isComplete: false,
        error: nil
    )
    
    public init() {
        self.session = URLSession.shared
        logger.info("🚀 TradingAgentsService initialized with baseURL: \(AppConfig.apiBaseURL)")
        
        if AppConfig.enableVerboseLogging {
            AppConfig.printConfiguration()
        }
    }
    
    public func streamAnalysis(for ticker: String) -> AnyPublisher<AnalysisProgress, Never> {
        let subject = PassthroughSubject<AnalysisProgress, Never>()
        
        logger.info("📡 Starting stream analysis for ticker: \(ticker)")
        
        let urlString = AppConfig.streamURL(for: ticker)
        logger.info("🌐 Request URL: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            logger.error("❌ Invalid URL: \(urlString)")
            subject.send(AnalysisProgress(
                currentAgent: "",
                message: "",
                reports: [:],
                agentActivities: [:],
                isComplete: true,
                error: "Invalid URL: \(urlString)"
            ))
            return subject.eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        request.setValue("keep-alive", forHTTPHeaderField: "Connection")
        request.timeoutInterval = AppConfig.streamTimeout
        
        logger.info("📋 Request headers: \(request.allHTTPHeaderFields ?? [:])")
        
        // Use direct streaming approach
        self.streamWithCustomSession(request: request, subject: subject)
        
        return subject.eraseToAnyPublisher()
    }
    
    private func streamWithCustomSession(request: URLRequest, subject: PassthroughSubject<AnalysisProgress, Never>) {
        logger.info("🔄 Starting SSE streaming with delegate")
        
        // Create delegate for real-time streaming
        let delegate = SSEStreamDelegate(subject: subject, service: self)
        
        // Create session with delegate for streaming
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = AppConfig.requestTimeout
        config.timeoutIntervalForResource = AppConfig.streamTimeout
        let delegateSession = URLSession(configuration: config, delegate: delegate, delegateQueue: nil)
        
        let task = delegateSession.dataTask(with: request)
        delegate.task = task
        
        // Store delegate and task
        self.streamingDelegate = delegate
        self.eventSource = task
        
        // Send initial status update
        DispatchQueue.main.async {
            subject.send(AnalysisProgress(
                currentAgent: "Starting",
                message: "🚀 Connecting to analysis service...",
                reports: [:],
                agentActivities: delegate.getAgentActivities(),
                isComplete: false,
                error: nil
            ))
        }
        
        task.resume()
        logger.info("🚀 SSE Stream task started with delegate")
    }
    
    internal func formatAgentName(_ agent: String) -> String {
        switch agent.lowercased() {
        case "market": return "Market Analyst"
        case "social": return "Social Media Analyst"
        case "news": return "News Analyst"
        case "fundamentals": return "Fundamentals Analyst"
        case "bull_researcher": return "Bull Researcher"
        case "bear_researcher": return "Bear Researcher"
        case "research_manager": return "Research Manager"
        case "trader": return "Trading Team"
        case "risky_analyst": return "Risky Analyst"
        case "safe_analyst": return "Safe Analyst"
        case "neutral_analyst": return "Neutral Analyst"
        case "risk_manager": return "Risk Manager"
        default: return agent.capitalized
        }
    }
    
    internal func formatSectionName(_ section: String) -> String {
        switch section {
        case "market_report": return "Market Analysis"
        case "sentiment_report": return "Sentiment Analysis"
        case "news_report": return "News Analysis"
        case "fundamentals_report": return "Fundamentals Analysis"
        case "investment_plan": return "Investment Plan"
        case "trader_investment_plan": return "Trading Plan"
        case "risk_analysis": return "Risk Analysis"
        case "final_trade_decision": return "Final Decision"
        default: return section.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
    
    public func stopAnalysis() {
        eventSource?.cancel()
        eventSource = nil
        streamingDelegate = nil
        isAnalyzing = false
    }
}

// MARK: - SSE Stream Delegate for Real-time Streaming
private class SSEStreamDelegate: NSObject, URLSessionDataDelegate {
    private let subject: PassthroughSubject<AnalysisProgress, Never>
    private weak var service: TradingAgentsService?
    private var buffer = ""
    private var currentReports: [String: String] = [:]
    private var agentActivities: [String: AgentActivity] = [:]
    private var currentAgentName = ""
    var task: URLSessionDataTask?
    
    init(subject: PassthroughSubject<AnalysisProgress, Never>, service: TradingAgentsService) {
        self.subject = subject
        self.service = service
        super.init()
        
        // Initialize all known agents
        let knownAgents = [
            ("market", "Market Analyst"),
            ("social", "Social Media Analyst"),
            ("news", "News Analyst"),
            ("fundamentals", "Fundamentals Analyst"),
            ("bull_researcher", "Bull Researcher"),
            ("bear_researcher", "Bear Researcher"),
            ("research_manager", "Research Manager"),
            ("trader", "Trading Team"),
            ("risky_analyst", "Risky Analyst"),
            ("safe_analyst", "Safe Analyst"),
            ("neutral_analyst", "Neutral Analyst"),
            ("risk_manager", "Risk Manager")
        ]
        
        for (name, displayName) in knownAgents {
            agentActivities[name] = AgentActivity(name: name, displayName: displayName)
        }
    }
    
    func getAgentActivities() -> [String: AgentActivity] {
        return agentActivities
    }
    
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        guard let httpResponse = response as? HTTPURLResponse else {
            completionHandler(.cancel)
            return
        }
        
        service?.logger.info("📶 SSE HTTP Response Status: \(httpResponse.statusCode)")
        
        if httpResponse.statusCode == 200 {
            completionHandler(.allow)
        } else {
            service?.logger.error("❌ SSE HTTP Error: \(httpResponse.statusCode)")
            DispatchQueue.main.async {
                self.subject.send(AnalysisProgress(
                    currentAgent: "",
                    message: "",
                    reports: self.currentReports,
                    agentActivities: self.agentActivities,
                    isComplete: true,
                    error: "HTTP \(httpResponse.statusCode)"
                ))
            }
            completionHandler(.cancel)
        }
    }
    
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        guard let service = service else { return }
        
        let newData = String(data: data, encoding: .utf8) ?? ""
        service.logger.info("📦 Received \(data.count) bytes")
        
        // Log raw SSE data for debugging
        if !newData.isEmpty {
            service.logger.info("📡 Raw SSE Data: \(newData)")
        }
        
        // Add new data to buffer
        buffer += newData
        
        // Process complete lines
        let lines = buffer.components(separatedBy: .newlines)
        buffer = lines.last ?? "" // Keep incomplete line in buffer
        
        service.logger.info("📋 Processing \(lines.count - 1) complete lines")
        
        // Process all complete lines except the last (incomplete) one
        for (index, line) in lines.dropLast().enumerated() {
            service.logger.info("📋 Line[\(index)]: \(line)")
            
            if line.hasPrefix("data: ") {
                let jsonString = String(line.dropFirst(6))
                service.logger.info("🔍 Extracting JSON: \(jsonString)")
                
                if let jsonData = jsonString.data(using: .utf8),
                   let event = try? JSONDecoder().decode(SSEEvent.self, from: jsonData) {
                    
                    service.logger.info("✅ SSE Event Successfully Decoded:")
                    service.logger.info("   📌 Type: \(event.type)")
                    service.logger.info("   📌 Agent: \(event.agent ?? "nil")")
                    service.logger.info("   📌 Status: \(event.status ?? "nil")")
                    service.logger.info("   📌 Section: \(event.section ?? "nil")")
                    service.logger.info("   📌 Message: \(event.message ?? "nil")")
                    service.logger.info("   📌 Content length: \(event.content?.count ?? 0)")
                    if let content = event.content {
                        service.logger.info("   📌 Content preview: \(String(content.prefix(200)))...")
                    }
                    
                    DispatchQueue.main.async {
                        self.processSSEEvent(event, service: service)
                    }
                } else {
                    service.logger.error("❌ Failed to decode SSE JSON: \(jsonString)")
                }
            } else if line.hasPrefix(":") {
                service.logger.info("💬 SSE Comment: \(line)")
            } else if !line.isEmpty {
                service.logger.info("📝 SSE Other: \(line)")
            }
        }
    }
    
    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            service?.logger.error("❌ SSE Connection error: \(error.localizedDescription)")
            DispatchQueue.main.async {
                self.subject.send(AnalysisProgress(
                    currentAgent: "",
                    message: "",
                    reports: self.currentReports,
                    agentActivities: self.agentActivities,
                    isComplete: true,
                    error: "Connection error: \(error.localizedDescription)"
                ))
            }
        } else {
            service?.logger.info("✅ SSE Connection completed successfully")
        }
    }
    
    private func processSSEEvent(_ event: SSEEvent, service: TradingAgentsService) {
        switch event.type {
        case "status":
            service.logger.info("📢 Status: \(event.message ?? "")")
            subject.send(AnalysisProgress(
                currentAgent: "Starting",
                message: event.message ?? "Starting analysis...",
                reports: currentReports,
                agentActivities: agentActivities,
                isComplete: false,
                error: nil
            ))
            
        case "agent_status":
            if let agentKey = event.agent {
                let agentName = service.formatAgentName(agentKey)
                currentAgentName = agentName
                
                service.logger.info("👤 Processing Agent Status:")
                service.logger.info("   🔍 Agent Key: \(agentKey)")
                service.logger.info("   🔍 Agent Name: \(agentName)")
                service.logger.info("   🔍 Status: \(event.status ?? "nil")")
                service.logger.info("   🔍 Current Activities Count: \(self.agentActivities.count)")
                
                // Create activity if it doesn't exist
                if agentActivities[agentKey] == nil {
                    agentActivities[agentKey] = AgentActivity(name: agentKey, displayName: agentName)
                    service.logger.info("   ✅ Created new activity for: \(agentKey)")
                } else {
                    service.logger.info("   ♻️ Using existing activity for: \(agentKey)")
                }
                
                // Update agent status
                if var activity = agentActivities[agentKey] {
                    let statusMessage: String
                    let newStatus: AgentActivity.AgentStatus
                    
                    switch event.status {
                    case "in_progress":
                        newStatus = .inProgress
                        statusMessage = "🔄 Analyzing with \(agentName)..."
                        activity.addMessage(AgentMessage(content: "Started analysis", type: .status))
                        service.logger.info("   🚀 Setting \(agentKey) to IN_PROGRESS")
                    case "completed":
                        newStatus = .completed
                        statusMessage = "✅ \(agentName) completed"
                        activity.addMessage(AgentMessage(content: "Analysis completed", type: .status))
                        service.logger.info("   ✅ Setting \(agentKey) to COMPLETED")
                    default:
                        newStatus = .inProgress
                        statusMessage = "🔄 Analyzing with \(agentName)..."
                        activity.addMessage(AgentMessage(content: event.status ?? "In progress", type: .status))
                        service.logger.info("   ⚠️ Unknown status '\(event.status ?? "nil")', defaulting to IN_PROGRESS")
                    }
                    
                    activity.updateStatus(newStatus)
                    agentActivities[agentKey] = activity
                    
                    // Log final agent activities state
                    service.logger.info("   📊 Final Agent Activities State:")
                    for (key, activity) in agentActivities {
                        service.logger.info("     • \(key): \(String(describing: activity.status)) (\(activity.displayName))")
                    }
                    
                    let activeCount = agentActivities.values.filter { $0.status == .inProgress }.count
                    let completedCount = agentActivities.values.filter { $0.status == .completed }.count
                    let pendingCount = agentActivities.values.filter { $0.status == .pending }.count
                    
                    service.logger.info("   📈 Status Summary: \(activeCount) active, \(completedCount) completed, \(pendingCount) pending")
                    
                    subject.send(AnalysisProgress(
                        currentAgent: agentName,
                        message: statusMessage,
                        reports: currentReports,
                        agentActivities: agentActivities,
                        isComplete: false,
                        error: nil
                    ))
                } else {
                    service.logger.error("   ❌ Failed to update activity for agent: \(agentKey)")
                }
            } else {
                service.logger.error("   ❌ Agent status event missing agent key!")
            }
            
        case "reasoning":
            // Capture intermediate reasoning messages with agent assignment
            if let content = event.content, !content.isEmpty {
                service.logger.info("🧠 Processing Reasoning Event:")
                service.logger.info("   🔍 Content length: \(content.count)")
                service.logger.info("   🔍 Content preview: \(String(content.prefix(200)))...")
                service.logger.info("   🔍 Event agent: \(event.agent ?? "nil")")
                
                // Use agent from event if available, otherwise find active agent
                let agentKey: String
                if let eventAgent = event.agent, !eventAgent.isEmpty {
                    agentKey = eventAgent
                    service.logger.info("   ✅ Using agent from event: \(agentKey)")
                } else {
                    agentKey = findCurrentActiveAgent() ?? "market"
                    service.logger.info("   ⚠️ Using fallback agent: \(agentKey)")
                }
                
                // Create activity if it doesn't exist
                if agentActivities[agentKey] == nil {
                    let displayName = service.formatAgentName(agentKey)
                    agentActivities[agentKey] = AgentActivity(name: agentKey, displayName: displayName)
                    service.logger.info("   ✅ Created new activity for agent: \(agentKey)")
                } else {
                    service.logger.info("   ♻️ Using existing activity for agent: \(agentKey)")
                }
                
                if var activity = agentActivities[agentKey] {
                    let message = AgentMessage(content: content, type: .reasoning)
                    let previousMessageCount = activity.messages.count
                    activity.addMessage(message)
                    agentActivities[agentKey] = activity
                    
                    service.logger.info("   📝 Added reasoning message to \(agentKey)")
                    service.logger.info("   📊 Messages for \(agentKey): \(previousMessageCount) → \(activity.messages.count)")
                    service.logger.info("   🎯 Sending progress update for \(activity.displayName)")
                    
                    subject.send(AnalysisProgress(
                        currentAgent: currentAgentName.isEmpty ? activity.displayName : currentAgentName,
                        message: "💭 \(activity.displayName) thinking...",
                        reports: currentReports,
                        agentActivities: agentActivities,
                        isComplete: false,
                        error: nil
                    ))
                } else {
                    service.logger.error("   ❌ Failed to find or create activity for agent: \(agentKey)")
                }
            } else {
                service.logger.warning("🧠 Reasoning event with empty or nil content")
            }
            
        case "progress":
            if let content = event.content, let percentage = Int(content) {
                service.logger.info("📊 Progress: \(percentage)%")
                subject.send(AnalysisProgress(
                    currentAgent: currentAgentName,
                    message: "Progress: \(percentage)%",
                    reports: currentReports,
                    agentActivities: agentActivities,
                    isComplete: false,
                    error: nil
                ))
            }
            
        case "report":
            if let section = event.section, let content = event.content {
                service.logger.info("📊 Report: \(section)")
                currentReports[section] = content
                
                // Find the agent that produced this report and set as final report
                let agentKey = mapSectionToAgent(section)
                if var activity = agentActivities[agentKey] {
                    activity.setFinalReport(content)
                    activity.updateStatus(.completed)
                    agentActivities[agentKey] = activity
                }
                
                subject.send(AnalysisProgress(
                    currentAgent: currentAgentName,
                    message: "📊 Updated \(service.formatSectionName(section))",
                    reports: currentReports,
                    agentActivities: agentActivities,
                    isComplete: false,
                    error: nil
                ))
            }
            
        case "complete":
            service.logger.info("✅ Analysis completed")
            subject.send(AnalysisProgress(
                currentAgent: "Complete",
                message: "✅ Analysis completed successfully",
                reports: currentReports,
                agentActivities: agentActivities,
                isComplete: true,
                error: nil
            ))
            
        case "error":
            service.logger.error("❌ Error: \(event.message ?? "")")
            subject.send(AnalysisProgress(
                currentAgent: "",
                message: "",
                reports: currentReports,
                agentActivities: agentActivities,
                isComplete: true,
                error: event.message ?? "Unknown error"
            ))
            
        default:
            service.logger.info("ℹ️ Unknown event type: \(event.type)")
        }
    }
    
    private func findCurrentActiveAgent() -> String? {
        // Find the most recently active agent
        return agentActivities.values
            .filter { $0.status == .inProgress }
            .max(by: { $0.startTime < $1.startTime })?
            .name
    }
    
    private func mapSectionToAgent(_ section: String) -> String {
        switch section {
        case "market_report": return "market"
        case "sentiment_report": return "social"
        case "news_report": return "news"
        case "fundamentals_report": return "fundamentals"
        case "investment_plan": return "research_manager"
        case "trader_investment_plan": return "trader"
        case "risk_analysis": return "risk_manager"
        case "final_trade_decision": return "risk_manager"
        default: return "market"
        }
    }
}

// MARK: - API Errors
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case serverError(message: String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .serverError(let message):
            return "Server error: \(message)"
        }
    }
} 
