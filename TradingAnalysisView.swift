import SwiftUI
import ReSwift

struct TradingAnalysisView: View {
    @StateObject private var viewModel = TradingAnalysisViewModel()
    @State private var tickerInput: String = ""
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Ticker Input
                HStack {
                    TextField("Enter ticker (e.g., AAPL)", text: $tickerInput)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .autocapitalization(.allCharacters)
                        .disableAutocorrection(true)
                    
                    Button(action: analyzeTicker) {
                        Text("Analyze")
                            .foregroundColor(.white)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 10)
                            .background(Color.blue)
                            .cornerRadius(8)
                    }
                    .disabled(tickerInput.isEmpty || viewModel.isLoading)
                }
                .padding(.horizontal)
                
                // Content
                if viewModel.isLoading {
                    ProgressView("Analyzing \(viewModel.ticker)...")
                        .scaleEffect(1.5)
                        .padding()
                    Spacer()
                } else if let error = viewModel.error {
                    ErrorView(error: error)
                    Spacer()
                } else if let result = viewModel.analysisResult {
                    AnalysisResultView(result: result)
                } else {
                    WelcomeView()
                    Spacer()
                }
            }
            .navigationTitle("Trading Analysis")
            .navigationBarTitleDisplayMode(.large)
        }
        .onAppear {
            viewModel.subscribe()
        }
        .onDisappear {
            viewModel.unsubscribe()
        }
    }
    
    private func analyzeTicker() {
        let ticker = tickerInput.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !ticker.isEmpty else { return }
        viewModel.analyzeTicker(ticker)
    }
}

// MARK: - ViewModel
class TradingAnalysisViewModel: ObservableObject, StoreSubscriber {
    @Published var ticker: String = ""
    @Published var isLoading: Bool = false
    @Published var analysisResult: AnalysisResponse?
    @Published var error: String?
    
    private let store: Store<TradingAnalysisState>
    
    init() {
        self.store = createTradingAnalysisStore()
    }
    
    func subscribe() {
        store.subscribe(self)
    }
    
    func unsubscribe() {
        store.unsubscribe(self)
    }
    
    func newState(state: TradingAnalysisState) {
        DispatchQueue.main.async {
            self.ticker = state.ticker
            self.isLoading = state.isLoading
            self.analysisResult = state.analysisResult
            self.error = state.error
        }
    }
    
    func analyzeTicker(_ ticker: String) {
        store.dispatch(RequestAnalysisAction(ticker: ticker))
    }
}

// MARK: - Welcome View
struct WelcomeView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            Text("Trading Agents Analysis")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Enter a stock ticker to get AI-powered trading analysis")
                .font(.subheadline)
                .foregroundColor(.secondary)
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
                .foregroundColor(.red)
            
            Text("Error")
                .font(.title2)
                .fontWeight(.bold)
            
            Text(error)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }
}

// MARK: - Analysis Result View
struct AnalysisResultView: View {
    let result: AnalysisResponse
    @State private var selectedTab = 0
    
    var body: some View {
        VStack(alignment: .leading, spacing: 15) {
            // Header
            VStack(alignment: .leading, spacing: 5) {
                Text(result.ticker)
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Analysis Date: \(result.analysisDate)")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                if let signal = result.processedSignal {
                    SignalBadge(signal: signal)
                }
            }
            .padding(.horizontal)
            
            // Tab View
            TabView(selection: $selectedTab) {
                // Market Analysis
                if let report = result.marketReport {
                    ReportSection(title: "Market Analysis", content: report)
                        .tabItem {
                            Label("Market", systemImage: "chart.line.uptrend.xyaxis")
                        }
                        .tag(0)
                }
                
                // Sentiment Analysis
                if let report = result.sentimentReport {
                    ReportSection(title: "Sentiment Analysis", content: report)
                        .tabItem {
                            Label("Sentiment", systemImage: "bubble.left.and.bubble.right")
                        }
                        .tag(1)
                }
                
                // News Analysis
                if let report = result.newsReport {
                    ReportSection(title: "News Analysis", content: report)
                        .tabItem {
                            Label("News", systemImage: "newspaper")
                        }
                        .tag(2)
                }
                
                // Final Decision
                if let decision = result.finalTradeDecision {
                    ReportSection(title: "Final Decision", content: decision)
                        .tabItem {
                            Label("Decision", systemImage: "checkmark.seal.fill")
                        }
                        .tag(3)
                }
            }
        }
    }
}

// MARK: - Signal Badge
struct SignalBadge: View {
    let signal: String
    
    var signalColor: Color {
        switch signal.lowercased() {
        case "buy", "strong buy":
            return .green
        case "sell", "strong sell":
            return .red
        case "hold":
            return .orange
        default:
            return .gray
        }
    }
    
    var body: some View {
        Text(signal.uppercased())
            .font(.caption)
            .fontWeight(.bold)
            .foregroundColor(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(signalColor)
            .cornerRadius(15)
    }
}

// MARK: - Report Section
struct ReportSection: View {
    let title: String
    let content: String
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 15) {
                Text(title)
                    .font(.title2)
                    .fontWeight(.bold)
                    .padding(.horizontal)
                
                Text(content)
                    .font(.body)
                    .padding(.horizontal)
            }
            .padding(.vertical)
        }
    }
}