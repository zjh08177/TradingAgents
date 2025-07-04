import SwiftUI
import SwiftData

struct TradingAnalysisView: View {
    @StateObject private var viewModel = TradingAnalysisViewModel()
    @Environment(\.modelContext) private var modelContext
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                headerSection
                
                // Input Section
                inputSection
                
                // Progress Section (shown during analysis)
                if viewModel.isAnalyzing {
                    progressSection
                }
                
                // Reports Section (shown as reports come in)
                if viewModel.hasReports && !viewModel.showingResults {
                    reportsSection
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("Trading Analysis")
            .onAppear {
                viewModel.modelContext = modelContext
            }
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") {
                    viewModel.errorMessage = nil
                }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
            .sheet(isPresented: $viewModel.showingResults) {
                AnalysisResultView(
                    ticker: viewModel.ticker,
                    reports: viewModel.formattedReports,
                    finalDecision: viewModel.finalDecision,
                    onDismiss: {
                        viewModel.resetAnalysis()
                    }
                )
            }
        }
    }
    
    // MARK: - View Components
    
    private var headerSection: some View {
        VStack(spacing: 8) {
            Text("TradingAgents")
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.primary)
            
            Text("AI-Powered Stock Analysis")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }
    
    private var inputSection: some View {
        VStack(spacing: 16) {
            HStack {
                TextField("Enter ticker symbol (e.g., AAPL)", text: $viewModel.ticker)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .autocapitalization(.allCharacters)
                    .autocorrectionDisabled(true)
                    .disabled(viewModel.isAnalyzing)
                
                if viewModel.isAnalyzing {
                    Button("Stop") {
                        viewModel.stopAnalysis()
                    }
                    .foregroundColor(.red)
                } else {
                    Button("Analyze") {
                        viewModel.startAnalysis()
                    }
                    .disabled(viewModel.ticker.isEmpty)
                }
            }
            
            if !viewModel.ticker.isEmpty && !viewModel.isAnalyzing {
                Text("Tap 'Analyze' to start real-time analysis")
                    .font(.footnote)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private var progressSection: some View {
        VStack(spacing: 16) {
            // Progress Bar
            VStack(spacing: 8) {
                HStack {
                    Text("Analysis Progress")
                        .font(.headline)
                    Spacer()
                    Text("\(viewModel.progressPercentage)%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                ProgressView(value: viewModel.analysisProgress)
                    .progressViewStyle(LinearProgressViewStyle(tint: .blue))
            }
            
            // Current Agent Status
            if !viewModel.currentAgent.isEmpty {
                HStack {
                    Image(systemName: "brain.head.profile")
                        .foregroundColor(.blue)
                    VStack(alignment: .leading) {
                        Text(viewModel.currentAgent)
                            .font(.subheadline)
                            .fontWeight(.medium)
                        if !viewModel.statusMessage.isEmpty {
                            Text(viewModel.statusMessage)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    Spacer()
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
            }
        }
    }
    
    private var reportsSection: some View {
        VStack(spacing: 12) {
            HStack {
                Text("Live Reports")
                    .font(.headline)
                Spacer()
                Text("\(viewModel.formattedReports.count) sections")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(viewModel.formattedReports, id: \.title) { report in
                        ReportCardView(title: report.title, content: report.content)
                    }
                }
            }
            .frame(maxHeight: 300)
        }
    }
}

// MARK: - Supporting Views

struct ReportCardView: View {
    let title: String
    let content: String
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Spacer()
                Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .onTapGesture {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            }
            
            if isExpanded {
                Text(content)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(nil)
                    .transition(.opacity.combined(with: .slide))
            } else {
                Text(content)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
}

#Preview {
    TradingAnalysisView()
} 