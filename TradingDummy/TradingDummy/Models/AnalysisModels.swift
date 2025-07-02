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