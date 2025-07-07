//
//  TradingDummyApp.swift
//  TradingDummy
//
//  Created by ByteDance on 6/28/25.
//

import SwiftUI
import SwiftData

@main
struct TradingDummyApp: App {
    // SwiftData model container
    let modelContainer: ModelContainer
    
    init() {
        do {
            modelContainer = try ModelContainer(for: AnalysisHistory.self)
        } catch {
            fatalError("Failed to create ModelContainer: \(error)")
        }
    }
    
    var body: some Scene {
        WindowGroup {
            TabView {
                TradingAnalysisView()
                    .tabItem {
                        Label("Analysis", systemImage: "chart.line.uptrend.xyaxis")
                    }
                
                HistoryView()
                    .tabItem {
                        Label("History", systemImage: "clock.arrow.circlepath")
                    }
            }
            .modelContainer(modelContainer)
        }
    }
}
