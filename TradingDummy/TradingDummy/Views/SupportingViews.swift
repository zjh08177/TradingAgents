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

// MARK: - Agent Activity Views
struct AgentActivityCard: View {
    let activity: AgentActivity
    @State private var isExpanded = true
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Agent Header
            HStack {
                statusIcon
                Text(activity.displayName)
                    .font(.headline)
                    .foregroundColor(.primary)
                
                Spacer()
                
                Text(statusText)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Button(action: { isExpanded.toggle() }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .foregroundColor(.secondary)
                }
            }
            
            if isExpanded {
                // Messages
                if !activity.messages.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(activity.messages) { message in
                            AgentMessageRow(message: message)
                        }
                    }
                } else if activity.status == .pending {
                    Text("Waiting to start...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .italic()
                }
            }
        }
        .padding()
        .background(backgroundColorForStatus)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(borderColorForStatus, lineWidth: 2)
        )
    }
    
    @ViewBuilder
    private var statusIcon: some View {
        switch activity.status {
        case .pending:
            Image(systemName: "clock")
                .foregroundColor(.orange)
        case .inProgress:
            Image(systemName: "gear")
                .foregroundColor(.blue)
                .rotationEffect(.degrees(Double(activity.messages.count) * 10))
        case .completed:
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.green)
        case .error(_):
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
        }
    }
    
    private var statusText: String {
        switch activity.status {
        case .pending:
            return "Pending"
        case .inProgress:
            return "Working..."
        case .completed:
            if let completionTime = activity.completionTime {
                let duration = completionTime.timeIntervalSince(activity.startTime)
                return "Completed (\(String(format: "%.1f", duration))s)"
            }
            return "Completed"
        case .error(let message):
            return "Error: \(message)"
        }
    }
    
    private var backgroundColorForStatus: Color {
        switch activity.status {
        case .pending:
            return Color(.systemGray6)
        case .inProgress:
            return Color.blue.opacity(0.1)
        case .completed:
            return Color.green.opacity(0.1)
        case .error(_):
            return Color.red.opacity(0.1)
        }
    }
    
    private var borderColorForStatus: Color {
        switch activity.status {
        case .pending:
            return Color.orange.opacity(0.3)
        case .inProgress:
            return Color.blue.opacity(0.5)
        case .completed:
            return Color.green.opacity(0.5)
        case .error(_):
            return Color.red.opacity(0.5)
        }
    }
}

struct AgentMessageRow: View {
    let message: AgentMessage
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            messageTypeIcon
            
            VStack(alignment: .leading, spacing: 2) {
                Text(message.content)
                    .font(.caption)
                    .foregroundColor(textColorForMessageType)
                    .lineLimit(messageTypeIsImportant ? nil : 3)
                
                Text(formatTimestamp(message.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.leading, 8)
    }
    
    @ViewBuilder
    private var messageTypeIcon: some View {
        switch message.type {
        case .reasoning:
            Image(systemName: "brain")
                .foregroundColor(.purple)
                .font(.caption)
        case .toolCall:
            Image(systemName: "wrench")
                .foregroundColor(.orange)
                .font(.caption)
        case .status:
            Image(systemName: "info.circle")
                .foregroundColor(.blue)
                .font(.caption)
        case .finalReport:
            Image(systemName: "doc.text.fill")
                .foregroundColor(.green)
                .font(.caption)
        }
    }
    
    private var textColorForMessageType: Color {
        switch message.type {
        case .reasoning:
            return .purple
        case .toolCall:
            return .orange
        case .status:
            return .blue
        case .finalReport:
            return .primary
        }
    }
    
    private var messageTypeIsImportant: Bool {
        message.type == .finalReport
    }
    
    private func formatTimestamp(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .medium
        return formatter.string(from: date)
    }
}

// MARK: - Live Activity Dashboard
struct LiveActivityDashboard: View {
    let agentActivities: [AgentActivity]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Live Agent Activity")
                .font(.title2)
                .fontWeight(.bold)
            
            if agentActivities.isEmpty {
                Text("No activity yet...")
                    .foregroundColor(.secondary)
                    .italic()
            } else {
                LazyVStack(spacing: 12) {
                    ForEach(agentActivities) { activity in
                        AgentActivityCard(activity: activity)
                    }
                }
            }
        }
        .padding()
    }
}

// MARK: - Progress Overview
struct ProgressOverview: View {
    let agentActivities: [AgentActivity]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Progress Overview")
                .font(.headline)
            
            HStack(spacing: 16) {
                ProgressIndicator(
                    title: "Completed",
                    count: completedCount,
                    color: .green
                )
                
                ProgressIndicator(
                    title: "Active",
                    count: activeCount,
                    color: .blue
                )
                
                ProgressIndicator(
                    title: "Pending",
                    count: pendingCount,
                    color: .orange
                )
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private var completedCount: Int {
        agentActivities.filter { $0.status == .completed }.count
    }
    
    private var activeCount: Int {
        agentActivities.filter { $0.status == .inProgress }.count
    }
    
    private var pendingCount: Int {
        agentActivities.filter { $0.status == .pending }.count
    }
}

struct ProgressIndicator: View {
    let title: String
    let count: Int
    let color: Color
    
    var body: some View {
        VStack {
            Text("\(count)")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(color)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
} 