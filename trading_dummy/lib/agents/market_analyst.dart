// Market Analyst Agent - Mirrors Python market_analyst.py structure
// Performs technical analysis using market data tools

import '../models/agent_states.dart';
import '../services/langchain_service.dart';
import '../services/market_tools.dart';
import '../services/logger_service.dart';

class ToolCall {
  final String name;
  final Map<String, dynamic> args;
  final String id;
  
  ToolCall({required this.name, required this.args, required this.id});
}

class MarketAnalystMessage {
  final String content;
  final List<ToolCall> toolCalls;
  final String type;
  final String? toolCallId;
  
  MarketAnalystMessage({
    required this.content,
    this.toolCalls = const [],
    this.type = 'ai',
    this.toolCallId,
  });
  
  bool get hasToolCalls => toolCalls.isNotEmpty;
}

class MarketAnalyst {
  final LangChainService _llm;
  final MarketToolkit _toolkit;
  
  MarketAnalyst(this._llm) : _toolkit = MarketToolkit();

  // Main entry point - mirrors create_market_analyst function
  Future<AgentState> analyzeMarket(AgentState state) async {
    LoggerService.agentStart('market', 'Technical analysis for ${state.companyOfInterest}');
    
    final stopwatch = Stopwatch()..start();
    final currentDate = state.tradeDate;
    final ticker = state.companyOfInterest;
    
    // Simulate message history for tool call logic
    List<MarketAnalystMessage> messages = [];
    
    // Step 1: Make initial tool calls to gather data
    if (messages.isEmpty) {
      messages = await _makeInitialToolCalls(ticker, currentDate);
    }
    
    // Step 2: Check if we have tool results and generate final report
    final hasToolResults = messages.any((msg) => msg.type == 'tool');
    final needsMoreData = !hasToolResults && messages.length < 3;
    
    String finalReport = '';
    
    if (hasToolResults || needsMoreData) {
      // We have tool data, now generate comprehensive analysis
      finalReport = await _generateFinalReport(ticker, currentDate, messages);
    } else {
      // Fallback to simple analysis
      finalReport = await _generateSimpleAnalysis(ticker, currentDate);
    }
    
    stopwatch.stop();
    LoggerService.agentComplete('market', 'Technical analysis', stopwatch.elapsed);
    
    return state.copyWith(marketReport: finalReport);
  }

  // Step 1: Make tool calls to gather market data (mirrors Python tool calling logic)
  Future<List<MarketAnalystMessage>> _makeInitialToolCalls(String ticker, String currentDate) async {
    List<MarketAnalystMessage> messages = [];
    
    LoggerService.info('market', 'Gathering market data');
    
    // Tool Call 1: Get Yahoo Finance data first (required for indicators)
    try {
      final yfinTool = _toolkit.getTool('get_YFin_data_online');
      if (yfinTool != null) {
        final yfinResult = await yfinTool.execute({
          'ticker': ticker,
          'date': currentDate,
        });
        
        messages.add(MarketAnalystMessage(
          content: yfinResult,
          type: 'tool',
          toolCallId: 'yfin_call_1',
        ));
      } else {
        LoggerService.warning('market', 'Yahoo Finance tool not found in toolkit');
      }
    } catch (e) {
      LoggerService.error('market', 'YFin tool call failed: $e');
    }
    
    // Tool Call 2: Get technical indicators based on market conditions
    try {
      final indicatorsTool = _toolkit.getTool('get_stockstats_indicators_report_online');
      if (indicatorsTool != null) {
        // Select relevant indicators (mirrors Python system message logic)
        final selectedIndicators = _selectRelevantIndicators();
        
        final indicatorsResult = await indicatorsTool.execute({
          'ticker': ticker,
          'indicators': selectedIndicators,
        });
        
        messages.add(MarketAnalystMessage(
          content: indicatorsResult,
          type: 'tool',
          toolCallId: 'indicators_call_1',
        ));
      } else {
        LoggerService.warning('market', 'Technical indicators tool not found in toolkit');
      }
    } catch (e) {
      LoggerService.error('market', 'Indicators tool call failed: $e');
    }
    
    return messages;
  }

  // Select relevant indicators (mirrors Python system message logic)
  List<String> _selectRelevantIndicators() {
    // Mirror Python system message - select up to 8 complementary indicators
    return [
      'close_50_sma',    // Medium-term trend
      'close_200_sma',   // Long-term trend
      'close_10_ema',    // Short-term momentum
      'macd',            // Momentum indicator
      'macds',           // MACD signal
      'rsi',             // Overbought/oversold
      'boll_ub',         // Resistance level
      'boll_lb',         // Support level
    ];
  }

  // Step 2: Generate comprehensive final report (mirrors Python final analysis)
  Future<String> _generateFinalReport(String ticker, String currentDate, List<MarketAnalystMessage> messages) async {
    // Gather all tool results
    final toolResults = messages.where((msg) => msg.type == 'tool').map((msg) => msg.content).join('\n\n');
    
    // Create comprehensive prompt for final analysis
    final prompt = '''
You are a trading assistant tasked with analyzing financial markets. You have gathered the following market data and technical indicators for $ticker:

MARKET DATA:
$toolResults

Based on this comprehensive data, provide a detailed and nuanced technical analysis report. Your analysis should include:

1. **Price Action Analysis**: Current price trends, support/resistance levels
2. **Technical Indicators Summary**: Key insights from moving averages, MACD, RSI, Bollinger Bands
3. **Volume Analysis**: Volume patterns and confirmation
4. **Momentum Assessment**: Short-term vs long-term momentum
5. **Risk Assessment**: Volatility and risk factors
6. **Trading Opportunities**: Specific entry/exit points and strategies

Do not simply state that trends are mixed. Provide detailed, fine-grained analysis and insights that may help traders make informed decisions. Focus on actionable intelligence.

Current date: $currentDate
Company: $ticker

Write a comprehensive technical analysis report:
''';

    try {
      final analysis = await _llm.generateTradingInsight(prompt);
      return '''
MARKET ANALYST TECHNICAL REPORT

Company: $ticker
Date: $currentDate
Analysis Type: Comprehensive Technical Analysis

$analysis

---
Data Sources: Yahoo Finance, Technical Indicators (Real-time)
Generated: ${DateTime.now().toLocal()}
''';
    } catch (e) {
      LoggerService.error('market', 'Failed to generate final report: $e');
      return _generateSimpleAnalysis(ticker, currentDate);
    }
  }

  // Fallback simple analysis
  Future<String> _generateSimpleAnalysis(String ticker, String currentDate) async {
    final prompt = '''
You are a Market Analyst. Analyze the technical aspects of $ticker on $currentDate.

Provide a concise market analysis covering:
- Current stock price trends
- Technical indicators 
- Volume analysis
- Support/resistance levels
- Market sentiment

Company: $ticker
Date: $currentDate

Keep response under 200 words.
''';

    try {
      final analysis = await _llm.generateTradingInsight(prompt);
      return '''
MARKET ANALYST REPORT (Simplified)

Company: $ticker
Date: $currentDate

$analysis

---
Note: Limited data analysis due to tool unavailability
Generated: ${DateTime.now().toLocal()}
''';
    } catch (e) {
      return '''
MARKET ANALYST REPORT

Company: $ticker
Date: $currentDate

Technical analysis temporarily unavailable. Please check API configuration.

Error: $e
Generated: ${DateTime.now().toLocal()}
''';
    }
  }

  // Utility method to get analysis summary
  String getAnalysisSummary(AgentState state) {
    if (state.marketReport.isEmpty) {
      return 'Market analysis not yet completed';
    }
    
    return '''
Market Analyst Status: ✅ Completed
Ticker: ${state.companyOfInterest}
Date: ${state.tradeDate}
Report Length: ${state.marketReport.length} characters
Tools Used: Online (Real-time)
''';
  }
} 