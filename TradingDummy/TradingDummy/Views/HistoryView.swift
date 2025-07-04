//
//  HistoryView.swift
//  TradingDummy
//
//  View for displaying analysis history
//

import SwiftUI
import SwiftData

struct HistoryView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \AnalysisHistory.analysisDate, order: .reverse) 
    private var histories: [AnalysisHistory]
    
    @State private var searchText = ""
    @State private var showFavoritesOnly = false
    @State private var selectedHistory: AnalysisHistory?
    
    // Filtered histories based on search and favorites
    private var filteredHistories: [AnalysisHistory] {
        histories.filter { history in
            let matchesSearch = searchText.isEmpty || 
                history.ticker.localizedCaseInsensitiveContains(searchText) ||
                history.finalDecision.localizedCaseInsensitiveContains(searchText)
            let matchesFavorites = !showFavoritesOnly || history.isFavorite
            return matchesSearch && matchesFavorites
        }
    }
    
    var body: some View {
        NavigationStack {
            List {
                if filteredHistories.isEmpty {
                    ContentUnavailableView(
                        "No Analysis History",
                        systemImage: "clock.arrow.circlepath",
                        description: Text(searchText.isEmpty ? "Start analyzing stocks to see history here" : "No results for '\(searchText)'")
                    )
                    .listRowSeparator(.hidden)
                } else {
                    ForEach(filteredHistories) { history in
                        HistoryRow(history: history)
                            .onTapGesture {
                                selectedHistory = history
                            }
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    deleteHistory(history)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                                
                                Button {
                                    toggleFavorite(history)
                                } label: {
                                    Label(
                                        history.isFavorite ? "Unfavorite" : "Favorite",
                                        systemImage: history.isFavorite ? "star.fill" : "star"
                                    )
                                }
                                .tint(.yellow)
                            }
                    }
                }
            }
            .navigationTitle("Analysis History")
            .searchable(text: $searchText, prompt: "Search ticker or content")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showFavoritesOnly.toggle()
                    } label: {
                        Image(systemName: showFavoritesOnly ? "star.fill" : "star")
                            .foregroundColor(showFavoritesOnly ? .yellow : .gray)
                    }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Clear All History", role: .destructive) {
                            clearAllHistory()
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(item: $selectedHistory) { history in
                HistoryDetailView(history: history)
            }
        }
    }
    
    // MARK: - Actions
    
    private func deleteHistory(_ history: AnalysisHistory) {
        withAnimation {
            modelContext.delete(history)
            try? modelContext.save()
        }
    }
    
    private func toggleFavorite(_ history: AnalysisHistory) {
        withAnimation {
            history.isFavorite.toggle()
            try? modelContext.save()
        }
    }
    
    private func clearAllHistory() {
        withAnimation {
            for history in histories {
                modelContext.delete(history)
            }
            try? modelContext.save()
        }
    }
}

// MARK: - History Row View

struct HistoryRow: View {
    let history: AnalysisHistory
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(history.ticker)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                SignalBadge(signal: history.signal)
                
                if history.isFavorite {
                    Image(systemName: "star.fill")
                        .foregroundColor(.yellow)
                        .font(.caption)
                }
            }
            
            Text(history.summary)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .lineLimit(2)
            
            HStack {
                Label(history.formattedDate, systemImage: "calendar")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - History Detail View

struct HistoryDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let history: AnalysisHistory
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationStack {
            TabView(selection: $selectedTab) {
                // Summary Tab
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        // Header
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(history.ticker)
                                    .font(.largeTitle)
                                    .bold()
                                
                                Spacer()
                                
                                SignalBadge(signal: history.signal, size: .large)
                            }
                            
                            Label(history.formattedDate, systemImage: "calendar")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        
                        // Final Decision
                        VStack(alignment: .leading, spacing: 8) {
                            Label("Final Decision", systemImage: "checkmark.seal.fill")
                                .font(.headline)
                                .foregroundColor(.blue)
                            
                            Text(history.finalDecision)
                                .font(.body)
                        }
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                    }
                    .padding()
                }
                .tag(0)
                .tabItem {
                    Label("Summary", systemImage: "doc.text")
                }
                
                // Full Report Tab
                ScrollView {
                    Text(history.fullReport)
                        .font(.body)
                        .padding()
                        .textSelection(.enabled)
                }
                .tag(1)
                .tabItem {
                    Label("Full Report", systemImage: "doc.richtext")
                }
            }
            .navigationTitle("Analysis Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .topBarLeading) {
                    ShareLink(
                        item: createShareableReport(),
                        subject: Text("\(history.ticker) Analysis"),
                        message: Text("Trading analysis from \(history.formattedDate)")
                    ) {
                        Image(systemName: "square.and.arrow.up")
                    }
                }
            }
        }
    }
    
    private func createShareableReport() -> String {
        """
        Trading Analysis Report
        
        Ticker: \(history.ticker)
        Date: \(history.formattedDate)
        Signal: \(history.signal)
        
        Final Decision:
        \(history.finalDecision)
        
        Full Report:
        \(history.fullReport)
        """
    }
}

// MARK: - Signal Badge

struct SignalBadge: View {
    let signal: String
    var size: Size = .regular
    
    enum Size {
        case regular, large
        
        var font: Font {
            switch self {
            case .regular: return .caption
            case .large: return .headline
            }
        }
        
        var padding: EdgeInsets {
            switch self {
            case .regular: return EdgeInsets(top: 4, leading: 8, bottom: 4, trailing: 8)
            case .large: return EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16)
            }
        }
    }
    
    private var backgroundColor: Color {
        switch signal.uppercased() {
        case "BUY": return .green
        case "SELL": return .red
        case "HOLD": return .orange
        default: return .gray
        }
    }
    
    var body: some View {
        Text(signal.uppercased())
            .font(size.font)
            .fontWeight(.semibold)
            .foregroundColor(.white)
            .padding(size.padding)
            .background(backgroundColor)
            .cornerRadius(8)
    }
}