import SwiftUI

struct TradingAnalysisView: View {
    @StateObject private var viewModel = TradingAnalysisViewModel()
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Header Section
                VStack(spacing: 16) {
                    Text("Trading Agents Analysis")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    // Ticker Input
                    HStack {
                        TextField("Enter ticker (e.g., AAPL)", text: $viewModel.ticker)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.allCharacters)
                            .disabled(viewModel.isAnalyzing)
                        
                        Button(action: {
                            if viewModel.isAnalyzing {
                                viewModel.stopAnalysis()
                            } else {
                                viewModel.startAnalysis()
                            }
                        }) {
                            Text(viewModel.isAnalyzing ? "Stop" : "Analyze")
                                .fontWeight(.semibold)
                                .foregroundColor(.white)
                                .padding(.horizontal, 20)
                                .padding(.vertical, 10)
                                .background(viewModel.isAnalyzing ? Color.red : Color.blue)
                                .cornerRadius(8)
                        }
                        .disabled(viewModel.ticker.isEmpty && !viewModel.isAnalyzing)
                    }
                    
                    // Progress Overview
                    if viewModel.hasActivityToShow() {
                        ProgressOverview(agentActivities: viewModel.agentActivities)
                    }
                    
                    // Current Status
                    if viewModel.isAnalyzing && !viewModel.statusMessage.isEmpty {
                        HStack {
                            ProgressView()
                                .scaleEffect(0.8)
                            Text(viewModel.statusMessage)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        .padding(.vertical, 8)
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                
                // Content Tabs
                if viewModel.hasActivityToShow() || viewModel.hasReports {
                    VStack(spacing: 0) {
                        // Tab Selector
                        Picker("View", selection: $selectedTab) {
                            Text("Live Activity").tag(0)
                            Text("Final Reports").tag(1)
                        }
                        .pickerStyle(SegmentedPickerStyle())
                        .padding()
                        
                        // Tab Content
                        TabView(selection: $selectedTab) {
                            // Live Activity Tab
                            ScrollView {
                                LiveActivityDashboard(agentActivities: viewModel.agentActivities)
                            }
                            .tag(0)
                            
                            // Final Reports Tab
                            ScrollView {
                                AnalysisResultView(
                                    reports: viewModel.formattedReports,
                                    finalDecision: viewModel.finalDecision
                                )
                            }
                            .tag(1)
                        }
                        .tabViewStyle(PageTabViewStyle(indexDisplayMode: .never))
                    }
                } else if !viewModel.isAnalyzing {
                    // Placeholder when no activity
                    Spacer()
                    VStack(spacing: 16) {
                        Image(systemName: "chart.line.uptrend.xyaxis")
                            .font(.system(size: 60))
                            .foregroundColor(.secondary)
                        
                        Text("Enter a ticker symbol and tap Analyze to start")
                            .font(.headline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                    Spacer()
                }
                
                Spacer()
            }
            .navigationBarHidden(true)
        }
        .alert("Analysis Error", isPresented: .constant(viewModel.errorMessage != nil)) {
            Button("OK") {
                viewModel.errorMessage = nil
            }
            Button("Try Again") {
                viewModel.startAnalysis()
            }
        } message: {
            Text(viewModel.errorMessage ?? "")
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