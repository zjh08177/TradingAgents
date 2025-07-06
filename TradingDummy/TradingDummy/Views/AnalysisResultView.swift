import SwiftUI

// MARK: - Analysis Result View
struct AnalysisResultView: View {
    let reports: [(title: String, content: String)]
    let finalDecision: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            Text("Final Reports")
                .font(.title2)
                .fontWeight(.bold)
                .padding(.horizontal)
            
            if reports.isEmpty && finalDecision.isEmpty {
                // Empty state
                VStack(spacing: 16) {
                    Image(systemName: "doc.text")
                        .font(.system(size: 50))
                        .foregroundColor(.secondary)
                    
                    Text("No reports available yet")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    Text("Reports will appear here as agents complete their analysis")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
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
            
            Spacer()
        }
        .padding(.vertical)
    }
    
    private func iconForReport(_ title: String) -> String {
        switch title {
        case "Market Analysis": return "chart.line.uptrend.xyaxis"
        case "Sentiment Analysis": return "bubble.left.and.bubble.right"
        case "News Analysis": return "newspaper"
        case "Fundamentals Analysis": return "doc.text"
        case "Investment Plan": return "lightbulb"
        case "Trading Plan": return "chart.bar.fill"
        case "Risk Analysis": return "shield.checkered"
        case "Final Decision": return "checkmark.seal.fill"
        default: return "doc.text"
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