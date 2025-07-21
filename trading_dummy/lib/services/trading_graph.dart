import '../models/agent_states.dart';
import 'trading_agents.dart';
import 'langchain_service.dart';
import '../agents/market_analyst.dart';
import '../agents/news_analyst.dart';
import '../agents/fundamentals_analyst.dart';
import 'config_service.dart';
import 'logger_service.dart';

// Main Trading Graph Orchestrator
// Mirrors the Python TradingAgentsGraph structure

class TradingGraph {
  final TradingAgents _agents;
  final MarketAnalyst _marketAnalyst;
  late FundamentalsAnalyst _fundamentalsAnalyst;
  final LangChainService _llmService;
  late NewsAnalyst _newsAnalyst;
  
  TradingGraph(LangChainService llmService) 
    : _agents = TradingAgents(llmService),
      _marketAnalyst = MarketAnalyst(llmService),
      _llmService = llmService {
    // Initialize with default (no API key initially)
    _fundamentalsAnalyst = FundamentalsAnalyst(llmService);
  }

  /// Initialize news analyst with API key from config
  Future<void> _initializeNewsAnalyst() async {
    // Only initialize if not already initialized
    try {
      // Try to access _newsAnalyst to see if it's initialized
      _newsAnalyst.toString();
    } catch (e) {
      // Not initialized yet, so initialize it
      final finnhubKey = await ConfigService.instance.getFinnhubKey();
      _newsAnalyst = NewsAnalyst(_llmService, finnhubApiKey: finnhubKey);
    }
  }

  /// Initialize fundamentals analyst with API key from config
  Future<void> _initializeFundamentalsAnalyst() async {
    final finnhubKey = await ConfigService.instance.getFinnhubKey();
    _fundamentalsAnalyst = FundamentalsAnalyst(_llmService, finnhubApiKey: finnhubKey);
  }

  // Main execution method - runs the entire trading workflow
  Future<AgentState> execute(String ticker, String date) async {
    // Initialize analysts with API keys
    await _initializeNewsAnalyst();
    await _initializeFundamentalsAnalyst();
    
    // Initialize state
    AgentState state = AgentState(
      companyOfInterest: ticker,
      tradeDate: date,
    );

    // Log model information for this analysis
    final modelStatus = _llmService.getModelStatus();
    LoggerService.info('trading_graph', 'Starting analysis for $ticker using $modelStatus');
    
    print('🚀 Starting Trading Analysis for $ticker on $date');
    print('   🤖 LLM Model: $modelStatus');

    // 1. DISPATCHER - Initialize the workflow
    state = await _dispatcher(state);

    // 2. PARALLEL ANALYST EXECUTION (Market Analyst is now sophisticated)
    state = await _runAnalystsInParallel(state);

    // 3. AGGREGATOR - Combine analyst reports
    state = await _aggregator(state);

    // 4. RESEARCH DEBATE (Bull vs Bear)
    state = await _runResearchDebate(state);

    // 5. TRADER - Create trading plan
    state = await _trader(state);

    // 6. PARALLEL RISK MANAGEMENT EXECUTION
    state = await _runRiskAnalystsInParallel(state);

    // 7. FINAL MANAGER - Make final decision
    state = await _riskManager(state);

    print('✅ Trading Analysis Complete');
    return state;
  }

  // ==================== WORKFLOW STAGES ====================

  // 1. DISPATCHER
  Future<AgentState> _dispatcher(AgentState state) async {
    print('📋 Dispatcher: Initializing analysis workflow...');
    // In simplified version, dispatcher just logs the start
    // In full version, this would set up data fetching and validation
    return state;
  }

  // 2. PARALLEL ANALYST EXECUTION (Enhanced with real Market Analyst)
  Future<AgentState> _runAnalystsInParallel(AgentState state) async {
    print('🔄 Running 4 Analysts in Parallel...');
    print('   📈 Market Analyst: Enhanced with tool calls');
    print('   📱 Social Media Analyst: Simple analysis');
    print('   📰 News Analyst: Finnhub API enabled');  
    print('   💼 Fundamentals Analyst: Finnhub API enabled');
    
    // Run all 4 analysts in parallel (Market, News & Fundamentals Analysts with real APIs)
    final results = await Future.wait([
      _marketAnalyst.analyzeMarket(state),       // Real analyst with tools
      _agents.socialMediaAnalyst(state),         // Simple analysts
      _newsAnalyst.analyzeNews(state),           // Real news analyst with Finnhub
      _fundamentalsAnalyst.analyzeFundamentals(state), // Real fundamentals analyst
    ]);

    // Combine results - each analyst updates a different field
    return state.copyWith(
      marketReport: results[0].marketReport,
      sentimentReport: results[1].sentimentReport,
      newsReport: results[2].newsReport,
      fundamentalsReport: results[3].fundamentalsReport,
    );
  }

  // 3. AGGREGATOR
  Future<AgentState> _aggregator(AgentState state) async {
    print('📊 Aggregator: Combining analyst reports...');
    
    // Validate all reports are complete
    final reports = [
      state.marketReport,
      state.sentimentReport,
      state.newsReport,
      state.fundamentalsReport,
    ];
    
    final completedReports = reports.where((r) => r.isNotEmpty).length;
    print('   ✅ Completed $completedReports/4 analyst reports');
    
    // Show enhanced market analysis info
    if (state.marketReport.isNotEmpty) {
      print('   📈 Market Analysis: Enhanced technical analysis with tool calls');
      print('   📊 Data Sources: Yahoo Finance + Technical Indicators');
    }
    
    return state;
  }

  // 4. RESEARCH DEBATE (Bull vs Bear with Judge)
  Future<AgentState> _runResearchDebate(AgentState state) async {
    print('⚖️ Research Debate: Bull vs Bear...');
    
    // Start with Bull researcher
    state = await _agents.bullResearcher(state);
    print('   🐂 Bull case presented');

    // Bear responds
    state = await _agents.bearResearcher(state);
    print('   🐻 Bear case presented');

    // Judge makes decision
    state = await _agents.researchManager(state);
    print('   ⚖️ Research Manager decision made');

    return state;
  }

  // 5. TRADER
  Future<AgentState> _trader(AgentState state) async {
    print('💼 Trader: Creating trading plan...');
    
    state = await _agents.trader(state);
    print('   ✅ Trading plan created');
    
    return state;
  }

  // 6. PARALLEL RISK MANAGEMENT EXECUTION
  Future<AgentState> _runRiskAnalystsInParallel(AgentState state) async {
    print('🛡️ Running 3 Risk Analysts in Parallel...');
    
    // Run all 3 risk analysts in parallel
    final results = await Future.wait([
      _agents.aggressiveRiskAnalyst(state),
      _agents.conservativeRiskAnalyst(state),
      _agents.neutralRiskAnalyst(state),
    ]);

    // Combine risk analysis results
    final combinedRiskState = state.riskDebateState.copyWith(
      riskyHistory: results[0].riskDebateState.riskyHistory,
      safeHistory: results[1].riskDebateState.safeHistory,
      neutralHistory: results[2].riskDebateState.neutralHistory,
      currentRiskyResponse: results[0].riskDebateState.currentRiskyResponse,
      currentSafeResponse: results[1].riskDebateState.currentSafeResponse,
      currentNeutralResponse: results[2].riskDebateState.currentNeutralResponse,
      count: results[0].riskDebateState.count,
    );

    return state.copyWith(riskDebateState: combinedRiskState);
  }

  // 7. FINAL MANAGER (Risk Manager)
  Future<AgentState> _riskManager(AgentState state) async {
    print('🎯 Risk Manager: Making final decision...');
    
    state = await _agents.riskManager(state);
    print('   ✅ Final trading decision made');
    
    return state;
  }

  // ==================== UTILITY METHODS ====================

  // Get a summary of the current state (Enhanced with market analyst info)
  String getStateSummary(AgentState state) {
    final buffer = StringBuffer();
    
    buffer.writeln('=== TRADING ANALYSIS SUMMARY ===');
    buffer.writeln('Company: ${state.companyOfInterest}');
    buffer.writeln('Date: ${state.tradeDate}');
    buffer.writeln('');
    
    // Analyst Reports Status (Enhanced)
    buffer.writeln('📊 ANALYST REPORTS:');
    buffer.writeln('Market: ${state.marketReport.isNotEmpty ? "✅ (Enhanced with tools)" : "❌"}');
    buffer.writeln('Social: ${state.sentimentReport.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('News: ${state.newsReport.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Fundamentals: ${state.fundamentalsReport.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('');
    
    // Market Analyst Summary
    if (state.marketReport.isNotEmpty) {
      buffer.writeln('📈 MARKET ANALYSIS DETAILS:');
      buffer.writeln(_marketAnalyst.getAnalysisSummary(state));
      buffer.writeln('');
    }
    
    // Research Debate Status
    buffer.writeln('⚖️ RESEARCH DEBATE:');
    buffer.writeln('Bull Case: ${state.investmentDebateState.bullHistory.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Bear Case: ${state.investmentDebateState.bearHistory.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Judge Decision: ${state.investmentPlan.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('');
    
    // Trading Plan Status
    buffer.writeln('💼 TRADING:');
    buffer.writeln('Trading Plan: ${state.traderInvestmentPlan.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('');
    
    // Risk Management Status
    buffer.writeln('🛡️ RISK MANAGEMENT:');
    buffer.writeln('Aggressive: ${state.riskDebateState.riskyHistory.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Conservative: ${state.riskDebateState.safeHistory.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Neutral: ${state.riskDebateState.neutralHistory.isNotEmpty ? "✅" : "❌"}');
    buffer.writeln('Final Decision: ${state.finalTradeDecision.isNotEmpty ? "✅" : "❌"}');
    
    return buffer.toString();
  }

  // Get the final trading recommendation (Enhanced with market data insights)
  String getFinalRecommendation(AgentState state) {
    if (state.finalTradeDecision.isEmpty) {
      return 'Analysis incomplete - no final decision available';
    }
    
    return '''
=== FINAL TRADING RECOMMENDATION ===

${state.finalTradeDecision}

--- SUPPORTING ANALYSIS ---

Enhanced Market Analysis:
${state.marketReport.isNotEmpty ? state.marketReport : 'Market analysis unavailable'}

Investment Research Decision:
${state.investmentPlan}

Trading Plan:
${state.traderInvestmentPlan}

Risk Analysis Summary:
• Aggressive Perspective: ${state.riskDebateState.currentRiskyResponse}
• Conservative Perspective: ${state.riskDebateState.currentSafeResponse}
• Neutral Perspective: ${state.riskDebateState.currentNeutralResponse}

--- ANALYSIS QUALITY ---
Market Data: ✅ Enhanced technical analysis with tool calls
Research Depth: ✅ Multi-agent debate and validation
Risk Assessment: ✅ Multiple risk perspectives analyzed
''';
  }
} 