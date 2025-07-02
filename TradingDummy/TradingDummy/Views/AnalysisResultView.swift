import SwiftUI

// MARK: - Analysis Result View
struct AnalysisResultView: View {
    let ticker: String
    let reports: [(title: String, content: String)]
    let finalDecision: String
    let onDismiss: () -> Void
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    HeaderView(ticker: ticker)
                        .padding(.horizontal)
                    
                    // Reports
                    VStack(spacing: 16) {
                        ForEach(reports, id: \.title) { report in
                            ReportCard(
                                title: report.title,
                                icon: iconForReport(report.title),
                                content: report.content
                            )
                        }
                        
                        // Final Decision
                        if !finalDecision.isEmpty {
                            ReportCard(
                                title: "Final Decision",
                                icon: "checkmark.seal.fill",
                                content: finalDecision,
                                isHighlighted: true
                            )
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .navigationTitle("Analysis Results")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Done") {
                        onDismiss()
                    }
                }
            }
        }
    }
    
    private func iconForReport(_ title: String) -> String {
        switch title {
        case "Market Analysis": return "chart.line.uptrend.xyaxis"
        case "Sentiment Analysis": return "bubble.left.and.bubble.right"
        case "News Analysis": return "newspaper"
        case "Fundamentals Analysis": return "doc.text"
        case "Investment Plan": return "lightbulb"
        case "Trading Plan": return "chart.bar.fill"
        default: return "doc.text"
        }
    }
}

// MARK: - Header View
struct HeaderView: View {
    let ticker: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(ticker)
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Analysis Date: \(DateFormatter.shortDate.string(from: Date()))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
            }
        }
    }
}

// MARK: - Report Card
struct ReportCard: View {
    let title: String
    let icon: String
    let content: String
    var isHighlighted: Bool = false
    
    @State private var isExpanded: Bool = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button(action: { withAnimation { isExpanded.toggle() } }) {
                HStack {
                    Image(systemName: icon)
                        .font(.title3)
                        .foregroundStyle(isHighlighted ? .white : .blue)
                    
                    Text(title)
                        .font(.headline)
                        .foregroundStyle(isHighlighted ? .white : .primary)
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .rotationEffect(.degrees(isExpanded ? 90 : 0))
                        .foregroundStyle(isHighlighted ? .white : .secondary)
                }
            }
            .buttonStyle(.plain)
            
            if isExpanded {
                Text(content)
                    .font(.body)
                    .foregroundStyle(isHighlighted ? .white : .primary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding()
        .background(isHighlighted ? Color.blue : Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

// MARK: - Extensions
extension DateFormatter {
    static let shortDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        return formatter
    }()
} 