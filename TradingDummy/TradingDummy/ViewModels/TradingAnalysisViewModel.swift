import Foundation
import Combine
import SwiftData

// MARK: - View Model
@MainActor
class TradingAnalysisViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var ticker: String = ""
    @Published var isAnalyzing: Bool = false
    @Published var showingResults: Bool = false
    @Published var errorMessage: String?
    
    // MARK: - Streaming Properties
    @Published var currentAgent: String = ""
    @Published var statusMessage: String = ""
    @Published var analysisProgress: Double = 0.0
    @Published var reports: [String: String] = [:]
    @Published var finalDecision: String = ""
    
    // MARK: - Services
    private let tradingService = TradingAgentsService()
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - SwiftData
    var modelContext: ModelContext?
    
    // MARK: - Constants
    private let agentSteps = [
        "Starting", "Market Analyst", "Social Media Analyst", 
        "News Analyst", "Fundamentals Analyst", "Bull Researcher", 
        "Bear Researcher", "Trading Team", "Complete"
    ]
    
    init() {
        setupSubscriptions()
    }
    
    private func setupSubscriptions() {
        // Subscribe to service progress updates
        tradingService.$progress
            .receive(on: DispatchQueue.main)
            .sink { [weak self] progress in
                self?.updateProgress(progress)
            }
            .store(in: &cancellables)
    }
    
    private func updateProgress(_ progress: AnalysisProgress) {
        currentAgent = progress.currentAgent
        statusMessage = progress.message
        reports = progress.reports
        
        // Update progress percentage based on current agent
        if let stepIndex = agentSteps.firstIndex(of: progress.currentAgent) {
            analysisProgress = Double(stepIndex) / Double(agentSteps.count - 1)
        }
        
        // Handle completion
        if progress.isComplete {
            isAnalyzing = false
            if progress.error == nil {
                showingResults = true
                finalDecision = reports["final_trade_decision"] ?? ""
                // Save to history
                saveToHistory()
            } else {
                errorMessage = progress.error
            }
        }
        
        // Handle errors
        if let error = progress.error {
            errorMessage = error
            isAnalyzing = false
        }
    }
    
    func startAnalysis() {
        guard !ticker.isEmpty else {
            errorMessage = "Please enter a ticker symbol"
            return
        }
        
        // Reset state
        isAnalyzing = true
        showingResults = false
        errorMessage = nil
        currentAgent = ""
        statusMessage = ""
        analysisProgress = 0.0
        reports = [:]
        finalDecision = ""
        
        // Start streaming analysis
        tradingService.streamAnalysis(for: ticker.uppercased())
            .receive(on: DispatchQueue.main)
            .sink { [weak self] progress in
                self?.updateProgress(progress)
            }
            .store(in: &cancellables)
    }
    
    func stopAnalysis() {
        tradingService.stopAnalysis()
        isAnalyzing = false
        currentAgent = ""
        statusMessage = "Analysis stopped"
    }
    
    func resetAnalysis() {
        stopAnalysis()
        showingResults = false
        errorMessage = nil
        ticker = ""
        currentAgent = ""
        statusMessage = ""
        analysisProgress = 0.0
        reports = [:]
        finalDecision = ""
    }
    
    // MARK: - Computed Properties
    var formattedReports: [(title: String, content: String)] {
        let reportOrder = [
            ("market_report", "Market Analysis"),
            ("sentiment_report", "Sentiment Analysis"),
            ("news_report", "News Analysis"),
            ("fundamentals_report", "Fundamentals Analysis"),
            ("investment_plan", "Investment Plan"),
            ("trader_investment_plan", "Trading Plan")
        ]
        
        return reportOrder.compactMap { key, title in
            guard let content = reports[key], !content.isEmpty else { return nil }
            return (title: title, content: content)
        }
    }
    
    var hasReports: Bool {
        !reports.isEmpty
    }
    
    var progressPercentage: Int {
        Int(analysisProgress * 100)
    }
    
    // MARK: - History Management
    private func saveToHistory() {
        guard let modelContext = modelContext else { return }
        
        // Extract signal from final decision
        let signal = extractSignal(from: finalDecision)
        
        // Create full report by combining all sections
        let fullReport = formattedReports.map { section in
            "=== \(section.title) ===\n\n\(section.content)\n"
        }.joined(separator: "\n\n")
        
        // Create history entry
        let history = AnalysisHistory(
            ticker: ticker.uppercased(),
            signal: signal,
            finalDecision: finalDecision,
            fullReport: fullReport,
            marketReport: reports["market_report"],
            sentimentReport: reports["sentiment_report"],
            newsReport: reports["news_report"],
            fundamentalsReport: reports["fundamentals_report"],
            investmentPlan: reports["investment_plan"],
            traderPlan: reports["trader_investment_plan"],
            riskAnalysis: reports["risk_analysis"]
        )
        
        // Save to SwiftData
        modelContext.insert(history)
        
        do {
            try modelContext.save()
            print("✅ Analysis saved to history")
        } catch {
            print("❌ Failed to save analysis to history: \(error)")
        }
    }
    
    private func extractSignal(from decision: String) -> String {
        let uppercased = decision.uppercased()
        
        // Check for explicit signals
        if uppercased.contains("**BUY**") || uppercased.contains("BUY SIGNAL") {
            return "BUY"
        } else if uppercased.contains("**SELL**") || uppercased.contains("SELL SIGNAL") {
            return "SELL"
        } else if uppercased.contains("**HOLD**") || uppercased.contains("HOLD SIGNAL") {
            return "HOLD"
        }
        
        // Check for context clues
        if uppercased.contains("RECOMMEND BUYING") || uppercased.contains("STRONG BUY") {
            return "BUY"
        } else if uppercased.contains("RECOMMEND SELLING") || uppercased.contains("STRONG SELL") {
            return "SELL"
        } else if uppercased.contains("MAINTAIN POSITION") || uppercased.contains("HOLD POSITION") {
            return "HOLD"
        }
        
        // Default to HOLD if unclear
        return "HOLD"
    }
} 