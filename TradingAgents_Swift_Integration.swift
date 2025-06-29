import Foundation
import Combine
import ReSwift

// MARK: - Redux State
struct TradingAnalysisState: StateType {
    var ticker: String = ""
    var isLoading: Bool = false
    var analysisResult: AnalysisResponse?
    var error: String?
}

// MARK: - Redux Actions
struct RequestAnalysisAction: Action {
    let ticker: String
}

struct AnalysisLoadingAction: Action {}

struct AnalysisSuccessAction: Action {
    let result: AnalysisResponse
}

struct AnalysisErrorAction: Action {
    let error: String
}

// MARK: - Models
struct AnalysisRequest: Codable {
    let ticker: String
}

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

// MARK: - Reducer
func tradingAnalysisReducer(action: Action, state: TradingAnalysisState?) -> TradingAnalysisState {
    var state = state ?? TradingAnalysisState()
    
    switch action {
    case let requestAction as RequestAnalysisAction:
        state.ticker = requestAction.ticker
        return state
        
    case _ as AnalysisLoadingAction:
        state.isLoading = true
        state.error = nil
        return state
        
    case let successAction as AnalysisSuccessAction:
        state.isLoading = false
        state.analysisResult = successAction.result
        state.error = nil
        return state
        
    case let errorAction as AnalysisErrorAction:
        state.isLoading = false
        state.error = errorAction.error
        return state
        
    default:
        return state
    }
}

// MARK: - API Service
class TradingAgentsAPIService {
    static let shared = TradingAgentsAPIService()
    private let baseURL = "http://localhost:8000" // Configure this based on your server
    
    private init() {}
    
    func analyzeTickerAsync(ticker: String) async throws -> AnalysisResponse {
        guard let url = URL(string: "\(baseURL)/analyze") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = AnalysisRequest(ticker: ticker)
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw APIError.httpError(statusCode: httpResponse.statusCode)
        }
        
        let analysisResponse = try JSONDecoder().decode(AnalysisResponse.self, from: data)
        
        if let error = analysisResponse.error {
            throw APIError.serverError(message: error)
        }
        
        return analysisResponse
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

// MARK: - Middleware for async operations
func createTradingAgentsMiddleware() -> Middleware<TradingAnalysisState> {
    return { dispatch, getState in
        return { next in
            return { action in
                next(action)
                
                if let requestAction = action as? RequestAnalysisAction {
                    dispatch(AnalysisLoadingAction())
                    
                    Task {
                        do {
                            let result = try await TradingAgentsAPIService.shared.analyzeTickerAsync(
                                ticker: requestAction.ticker
                            )
                            await MainActor.run {
                                dispatch(AnalysisSuccessAction(result: result))
                            }
                        } catch {
                            await MainActor.run {
                                dispatch(AnalysisErrorAction(error: error.localizedDescription))
                            }
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Store Configuration
func createTradingAnalysisStore() -> Store<TradingAnalysisState> {
    return Store<TradingAnalysisState>(
        reducer: tradingAnalysisReducer,
        state: nil,
        middleware: [createTradingAgentsMiddleware()]
    )
}