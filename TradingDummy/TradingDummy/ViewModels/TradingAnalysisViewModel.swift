import Foundation
import Combine
import SwiftUI

// MARK: - View Model
@MainActor
class TradingAnalysisViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var ticker: String = ""
    @Published var isAnalyzing: Bool = false
    @Published var errorMessage: String?
    
    // MARK: - Live Activity Properties
    @Published var currentAgent: String = ""
    @Published var statusMessage: String = ""
    @Published var agentActivities: [AgentActivity] = []
    @Published var reports: [String: String] = [:]
    @Published var finalDecision: String = ""
    
    // MARK: - Services
    private let tradingService = TradingAgentsService()
    private var cancellables = Set<AnyCancellable>()
    

    
    func startAnalysis() {
        guard !ticker.isEmpty else {
            errorMessage = "Please enter a ticker symbol"
            return
        }
        
        // Reset state
        errorMessage = nil
        isAnalyzing = true
        agentActivities = []
        reports = [:]
        currentAgent = ""
        statusMessage = ""
        finalDecision = ""
        
        // Start streaming analysis
        tradingService.streamAnalysis(for: ticker.uppercased())
            .receive(on: DispatchQueue.main)
            .sink { [weak self] analysisProgress in
                self?.updateProgress(analysisProgress)
            }
            .store(in: &cancellables)
    }
    
    func stopAnalysis() {
        tradingService.stopAnalysis()
        isAnalyzing = false
        currentAgent = ""
        statusMessage = "Analysis stopped"
    }
    
    private func updateProgress(_ progress: AnalysisProgress) {
        currentAgent = progress.currentAgent
        statusMessage = progress.message
        reports = progress.reports
        
        // Update agent activities with live messages
        agentActivities = Array(progress.agentActivities.values)
            .sorted { $0.startTime < $1.startTime }
        
        // Update final decision
        finalDecision = reports["final_trade_decision"] ?? ""
        
        // Handle completion
        if progress.isComplete {
            isAnalyzing = false
            if let error = progress.error {
                errorMessage = error
            }
        }
        
        // Handle errors
        if let error = progress.error {
            errorMessage = error
            isAnalyzing = false
        }
    }
    
    func resetAnalysis() {
        stopAnalysis()
        errorMessage = nil
        ticker = ""
        currentAgent = ""
        statusMessage = ""
        agentActivities = []
        reports = [:]
        finalDecision = ""
    }
    
    // MARK: - Helper Methods for UI
    func getActiveAgents() -> [AgentActivity] {
        return agentActivities.filter { $0.status == .inProgress }
    }
    
    func getCompletedAgents() -> [AgentActivity] {
        return agentActivities.filter { $0.status == .completed }
    }
    
    func getPendingAgents() -> [AgentActivity] {
        return agentActivities.filter { $0.status == .pending }
    }
    
    func getLatestMessagesForAgent(_ agentName: String) -> [AgentMessage] {
        return agentActivities.first { $0.name == agentName }?.messages ?? []
    }
    
    func hasActivityToShow() -> Bool {
        return !agentActivities.isEmpty && agentActivities.contains { !$0.messages.isEmpty }
    }
    
    var hasReports: Bool {
        !reports.isEmpty
    }
    
    var formattedReports: [(title: String, content: String)] {
        let reportOrder = [
            ("market_report", "Market Analysis"),
            ("sentiment_report", "Sentiment Analysis"),
            ("news_report", "News Analysis"),
            ("fundamentals_report", "Fundamentals Analysis"),
            ("investment_plan", "Investment Plan"),
            ("trader_investment_plan", "Trading Plan"),
            ("risk_analysis", "Risk Analysis"),
            ("final_trade_decision", "Final Decision")
        ]
        
        return reportOrder.compactMap { key, title in
            guard let content = reports[key], !content.isEmpty else { return nil }
            return (title: title, content: content)
        }
    }
} 