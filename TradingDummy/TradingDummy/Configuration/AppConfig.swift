import Foundation

enum AppConfig {
    // API Configuration
    static let apiBaseURL: String = {
        // Check for environment variable first (useful for CI/CD)
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
    
    // Network Configuration
    static let requestTimeout: TimeInterval = 600.0
    static let maxRetries = 3
    
    // UI Configuration
    static let defaultTicker = "AAPL"
    static let animationDuration = 0.3
} 