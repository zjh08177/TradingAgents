//
//  HistoryModels.swift
//  TradingDummy
//
//  SwiftData models for storing analysis history locally
//

import Foundation
import SwiftData

/// Model for storing historical analysis results
@Model
final class AnalysisHistory {
    /// Unique identifier
    var id: UUID
    
    /// Stock ticker symbol
    var ticker: String
    
    /// Date of analysis
    var analysisDate: Date
    
    /// Trading signal (BUY, SELL, HOLD)
    var signal: String
    
    /// Final trade decision summary
    var finalDecision: String
    
    /// Full analysis report (combined from all sections)
    var fullReport: String
    
    /// Individual report sections for quick access
    var marketReport: String?
    var sentimentReport: String?
    var newsReport: String?
    var fundamentalsReport: String?
    var investmentPlan: String?
    var traderPlan: String?
    var riskAnalysis: String?
    
    /// Metadata
    var createdAt: Date
    var isFavorite: Bool
    
    /// Initialize a new analysis history entry
    init(
        ticker: String,
        analysisDate: Date = Date(),
        signal: String,
        finalDecision: String,
        fullReport: String,
        marketReport: String? = nil,
        sentimentReport: String? = nil,
        newsReport: String? = nil,
        fundamentalsReport: String? = nil,
        investmentPlan: String? = nil,
        traderPlan: String? = nil,
        riskAnalysis: String? = nil
    ) {
        self.id = UUID()
        self.ticker = ticker
        self.analysisDate = analysisDate
        self.signal = signal
        self.finalDecision = finalDecision
        self.fullReport = fullReport
        self.marketReport = marketReport
        self.sentimentReport = sentimentReport
        self.newsReport = newsReport
        self.fundamentalsReport = fundamentalsReport
        self.investmentPlan = investmentPlan
        self.traderPlan = traderPlan
        self.riskAnalysis = riskAnalysis
        self.createdAt = Date()
        self.isFavorite = false
    }
}

// MARK: - Helper Extensions

extension AnalysisHistory {
    /// Get a formatted date string
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: analysisDate)
    }
    
    /// Get signal color
    var signalColor: String {
        switch signal.uppercased() {
        case "BUY":
            return "green"
        case "SELL":
            return "red"
        case "HOLD":
            return "orange"
        default:
            return "gray"
        }
    }
    
    /// Get a brief summary for list view
    var summary: String {
        let words = finalDecision.split(separator: " ").prefix(20)
        return words.joined(separator: " ") + (words.count >= 20 ? "..." : "")
    }
}

// MARK: - Query Helpers

extension AnalysisHistory {
    /// Predicate for filtering by ticker
    static func byTicker(_ ticker: String) -> Predicate<AnalysisHistory> {
        #Predicate<AnalysisHistory> { history in
            history.ticker == ticker
        }
    }
    
    /// Predicate for filtering favorites
    static var favorites: Predicate<AnalysisHistory> {
        #Predicate<AnalysisHistory> { history in
            history.isFavorite == true
        }
    }
    
    /// Predicate for recent analyses (last 7 days)
    static var recent: Predicate<AnalysisHistory> {
        let sevenDaysAgo = Date().addingTimeInterval(-7 * 24 * 60 * 60)
        return #Predicate<AnalysisHistory> { history in
            history.analysisDate > sevenDaysAgo
        }
    }
}