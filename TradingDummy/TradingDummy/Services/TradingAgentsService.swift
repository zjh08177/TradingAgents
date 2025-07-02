import Foundation
import Combine
import os.log

// MARK: - SSE Event Models
public struct SSEEvent: Codable {
    let type: String
    let message: String?
    let agent: String?
    let section: String?
    let content: String?
    let status: String?
}

// MARK: - Progress Models
public struct AnalysisProgress {
    public let currentAgent: String
    public let message: String
    public let reports: [String: String]
    public let isComplete: Bool
    public let error: String?
    
    public init(currentAgent: String, message: String, reports: [String: String], isComplete: Bool, error: String?) {
        self.currentAgent = currentAgent
        self.message = message
        self.reports = reports
        self.isComplete = isComplete
        self.error = error
    }
}

// MARK: - TradingAgentsService
public class TradingAgentsService: ObservableObject {
    internal let logger = Logger(subsystem: "com.tradingagents.app", category: "TradingAgentsService")
    
    private let baseURL: String = {
        // Check for environment variable first
        if let envURL = ProcessInfo.processInfo.environment["TRADINGAGENTS_API_URL"] {
            return envURL
        }
        
        // Default URLs for different environments
        #if DEBUG
            #if targetEnvironment(simulator)
            // For iOS Simulator
            return "http://localhost:8000"
            #else
            // For real device - UPDATE THIS WITH YOUR MAC'S IP
            return "http://192.168.4.223:8000"
            #endif
        #else
        // For production, update this to your deployed server URL
        return "https://api.tradingagents.com"
        #endif
    }()
    
    private var eventSource: URLSessionDataTask?
    private var streamingDelegate: SSEStreamDelegate?
    private let session: URLSession
    
    @Published var isAnalyzing = false
    @Published var progress = AnalysisProgress(
        currentAgent: "",
        message: "",
        reports: [:],
        isComplete: false,
        error: nil
    )
    
    public init() {
        self.session = URLSession.shared
        logger.info("🚀 TradingAgentsService initialized with baseURL: \(self.baseURL)")
    }
    
    public func streamAnalysis(for ticker: String) -> AnyPublisher<AnalysisProgress, Never> {
        let subject = PassthroughSubject<AnalysisProgress, Never>()
        
        logger.info("📡 Starting stream analysis for ticker: \(ticker)")
        
        let urlString = "\(baseURL)/analyze/stream?ticker=\(ticker)"
        logger.info("🌐 Request URL: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            logger.error("❌ Invalid URL: \(urlString)")
            subject.send(AnalysisProgress(
                currentAgent: "",
                message: "",
                reports: [:],
                isComplete: true,
                error: "Invalid URL: \(urlString)"
            ))
            return subject.eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        request.setValue("keep-alive", forHTTPHeaderField: "Connection")
        request.timeoutInterval = 600.0 // 10 minutes
        
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
        config.timeoutIntervalForRequest = 600.0
        config.timeoutIntervalForResource = 600.0
        let delegateSession = URLSession(configuration: config, delegate: delegate, delegateQueue: nil)
        
        let task = delegateSession.dataTask(with: request)
        delegate.task = task
        
        // Store delegate and task
        self.streamingDelegate = delegate
        self.eventSource = task
        
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
        case "trader": return "Trading Team"
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
    var task: URLSessionDataTask?
    
    init(subject: PassthroughSubject<AnalysisProgress, Never>, service: TradingAgentsService) {
        self.subject = subject
        self.service = service
        super.init()
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
        service.logger.info("📦 Received \(data.count) bytes: \(String(newData.prefix(100)))...")
        
        // Add new data to buffer
        buffer += newData
        
        // Process complete lines
        let lines = buffer.components(separatedBy: .newlines)
        buffer = lines.last ?? "" // Keep incomplete line in buffer
        
        // Process all complete lines except the last (incomplete) one
        for line in lines.dropLast() {
            if line.hasPrefix("data: ") {
                let jsonString = String(line.dropFirst(6))
                service.logger.info("🔍 Processing JSON: \(String(jsonString.prefix(50)))...")
                
                if let jsonData = jsonString.data(using: .utf8),
                   let event = try? JSONDecoder().decode(SSEEvent.self, from: jsonData) {
                    
                    service.logger.info("✅ Decoded event - Type: \(event.type)")
                    
                    DispatchQueue.main.async {
                        self.processSSEEvent(event, service: service)
                    }
                } else {
                    service.logger.warning("⚠️ Failed to decode JSON: \(jsonString)")
                }
            }
        }
    }
    
    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didCompleteWithError error: Error?) {
        if let error = error {
            service?.logger.error("❌ SSE Connection error: \(error.localizedDescription)")
            DispatchQueue.main.async {
                self.subject.send(AnalysisProgress(
                    currentAgent: "",
                    message: "",
                    reports: self.currentReports,
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
                isComplete: false,
                error: nil
            ))
            
        case "agent_status":
            let agentName = service.formatAgentName(event.agent ?? "")
            let statusMessage = event.status == "completed" ? 
                "✅ \(agentName) completed" : 
                "🔄 Analyzing with \(agentName)..."
            
            service.logger.info("👤 Agent: \(agentName), Status: \(event.status ?? "")")
            subject.send(AnalysisProgress(
                currentAgent: agentName,
                message: statusMessage,
                reports: currentReports,
                isComplete: false,
                error: nil
            ))
            
        case "progress":
            if let content = event.content, let percentage = Int(content) {
                service.logger.info("📊 Progress: \(percentage)%")
                subject.send(AnalysisProgress(
                    currentAgent: service.progress.currentAgent,
                    message: "Progress: \(percentage)%",
                    reports: currentReports,
                    isComplete: false,
                    error: nil
                ))
            }
            
        case "report":
            if let section = event.section, let content = event.content {
                service.logger.info("📊 Report: \(section)")
                currentReports[section] = content
                subject.send(AnalysisProgress(
                    currentAgent: service.progress.currentAgent,
                    message: "📊 Updated \(service.formatSectionName(section))",
                    reports: currentReports,
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
                isComplete: true,
                error: nil
            ))
            
        case "error":
            service.logger.error("❌ Error: \(event.message ?? "")")
            subject.send(AnalysisProgress(
                currentAgent: "",
                message: "",
                reports: currentReports,
                isComplete: true,
                error: event.message ?? "Unknown error"
            ))
            
        default:
            service.logger.info("ℹ️ Unknown event type: \(event.type)")
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
