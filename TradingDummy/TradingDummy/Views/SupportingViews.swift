import SwiftUI

// MARK: - Loading View
struct LoadingView: View {
    let ticker: String
    
    var body: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(1.5)
            
            Text("Analyzing \(ticker)...")
                .font(.headline)
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}

// MARK: - Welcome View
struct WelcomeView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: 60))
                .foregroundStyle(.blue)
            
            Text("Trading Agents Analysis")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Enter a stock ticker to get AI-powered trading analysis")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }
}

// MARK: - Error View
struct ErrorView: View {
    let error: String
    
    var body: some View {
        VStack(spacing: 15) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 50))
                .foregroundStyle(.red)
            
            Text("Error")
                .font(.title2)
                .fontWeight(.bold)
            
            Text(error)
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }
} 