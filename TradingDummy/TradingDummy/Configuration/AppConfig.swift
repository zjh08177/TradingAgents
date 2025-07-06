import Foundation

enum AppConfig {
    // MARK: - API Configuration
    static let apiBaseURL: String = {
        // Check for environment variable first (useful for CI/CD and custom URLs)
        if let envURL = ProcessInfo.processInfo.environment["TRADINGAGENTS_API_URL"] {
            return envURL
        }
        
        // Default URLs for different environments
        #if DEBUG
            #if targetEnvironment(simulator)
            // For iOS Simulator - connect to localhost
            return "http://localhost:8000"
            #else
            // For real device - connect to Mac's IP address
            return "http://10.73.204.80:8000"
            #endif
        #else
        // For production, update this to your deployed server URL
        return "https://api.tradingagents.com"
        #endif
    }()
    
    // MARK: - Network Configuration
    static let requestTimeout: TimeInterval = 600.0  // 10 minutes for long analysis
    static let streamTimeout: TimeInterval = 600.0   // 10 minutes for streaming
    static let maxRetries = 3
    
    // MARK: - API Endpoints
    static let healthEndpoint = "/health"
    static let analyzeEndpoint = "/analyze"
    static let streamEndpoint = "/analyze/stream"
    
    // MARK: - UI Configuration
    static let defaultTicker = "AAPL"
    static let animationDuration = 0.3
    
    // MARK: - Debug Configuration
    static let enableVerboseLogging = true
    static let logNetworkRequests = true
    
    // MARK: - Helper Methods
    static func fullURL(for endpoint: String) -> String {
        return apiBaseURL + endpoint
    }
    
    static func streamURL(for ticker: String) -> String {
        return "\(apiBaseURL)\(streamEndpoint)?ticker=\(ticker)"
    }
    
    // For debugging - prints current configuration
    static func printConfiguration() {
        print("🔧 TradingAgents Configuration:")
        print("📍 API Base URL: \(apiBaseURL)")
        print("⏱️ Request Timeout: \(requestTimeout)s")
        print("📡 Stream Timeout: \(streamTimeout)s")
        #if targetEnvironment(simulator)
        print("📱 Environment: iOS Simulator")
        #else
        print("📱 Environment: Real Device")
        #endif
    }
} 