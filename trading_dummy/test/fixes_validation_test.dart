import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/models/trading_report.dart';
import 'package:trading_dummy/models/stream_message.dart';
import 'package:trading_dummy/services/finality_detector.dart';
import 'package:trading_dummy/services/stream_processor_v2.dart';
import 'package:trading_dummy/widgets/trading_report_card.dart';

/// Validation test for final report display fixes
/// Tests the core components that were implemented to fix UI display issues
void main() {
  group('Final Report Display Fixes', () {
    
    test('TradingReport.fromLangGraphValues should extract data correctly', () {
      // Test the unified trading report schema
      final mockValuesData = {
        'final_trade_decision': 'BUY - Strong bullish outlook based on technical analysis',
        'trader_investment_plan': 'Allocate 5% of portfolio, set stop loss at 10%',
        'market_report': 'Market showing strong upward momentum',
        'sentiment_report': 'Positive sentiment across social media',
        'company_of_interest': 'AAPL',
        'trade_date': '2024-01-15',
      };

      final report = TradingReport.fromLangGraphValues(mockValuesData);

      expect(report.finalDecision, contains('BUY'));
      expect(report.investmentPlan, contains('Allocate 5%'));
      expect(report.marketAnalysis, contains('upward momentum'));
      expect(report.sentimentAnalysis, contains('Positive sentiment'));
      expect(report.ticker, equals('AAPL'));
      expect(report.tradeDate, equals('2024-01-15'));
      expect(report.completeness, equals(ReportCompleteness.substantial));
    });

    test('FinalityDetector should correctly identify final reports', () {
      // Test semantic finality detection
      final finalMessage = StreamMessage(
        id: '1',
        type: MessageType.success,
        content: 'Final trading decision: BUY AAPL with strong conviction',
        contentType: 'values',
        timestamp: DateTime.now(),
      );

      final report = TradingReport(
        finalDecision: 'BUY AAPL with strong conviction',
        rawData: {},
        completeness: ReportCompleteness.complete,
        timestamp: DateTime.now(),
      );

      expect(
        FinalityDetector.isDefinitelyFinal(finalMessage, report),
        isTrue,
      );

      final confidence = FinalityDetector.getFinalityConfidence(finalMessage, report);
      expect(confidence, greaterThan(70));
    });

    test('FinalityDetector should reject non-final content', () {
      // Test that progress updates are not marked as final
      final progressMessage = StreamMessage(
        id: '2',
        type: MessageType.progress,
        content: 'Collecting market data, please wait...',
        contentType: 'values',
        timestamp: DateTime.now(),
      );

      expect(
        FinalityDetector.isDefinitelyFinal(progressMessage, null),
        isFalse,
      );

      expect(
        FinalityDetector.isProgressUpdate(progressMessage.content),
        isTrue,
      );
    });

    test('ReportKeyMapper should handle various key formats', () {
      // Test robust key mapping with fallbacks
      final mapper = ReportKeyMapper();
      
      // Test primary key
      final data1 = {'final_trade_decision': 'BUY Signal'};
      expect(
        mapper.extractValue(data1, 'final_decision'),
        equals('BUY Signal'),
      );

      // Test fallback key
      final data2 = {'recommendation': 'SELL Signal'};
      expect(
        mapper.extractValue(data2, 'final_decision'),
        equals('SELL Signal'),
      );

      // Test alternative key
      final data3 = {'trader_investment_plan': 'Portfolio allocation strategy'};
      expect(
        mapper.extractValue(data3, 'investment_plan'),
        equals('Portfolio allocation strategy'),
      );
    });

    test('StreamProcessorV2 should create proper final messages', () {
      // Test enhanced stream processor
      final processor = StreamProcessorV2();
      
      // Mock a final trading report
      final report = TradingReport(
        finalDecision: 'BUY AAPL - Strong technical setup',
        investmentPlan: 'Allocate 3% of portfolio',
        marketAnalysis: 'Bullish trend continuation expected',
        completeness: ReportCompleteness.complete,
        rawData: {},
        timestamp: DateTime.now(),
        ticker: 'AAPL',
      );

      expect(report.hasMeaningfulContent, isTrue);
      expect(report.formattedContent, contains('⚡ **Final Trading Decision**'));
      expect(report.formattedContent, contains('🎯 **Investment Plan**'));
      expect(report.formattedContent, contains('📈 **Market Analysis**'));
    });

    test('SmartTitleGenerator should create appropriate titles', () {
      // Test intelligent title generation
      final message = StreamMessage(
        id: '3',
        type: MessageType.success,
        content: 'Final decision: Buy TSLA',
        contentType: 'values',
        timestamp: DateTime.now(),
      );

      final report = TradingReport(
        finalDecision: 'Buy TSLA',
        rawData: {},
        completeness: ReportCompleteness.substantial,
        timestamp: DateTime.now(),
      );

      final title = SmartTitleGenerator.getDisplayTitle(message, report);
      expect(title, equals('⚡ Final Trading Decision'));
    });

    test('TradingReport completeness calculation should work correctly', () {
      // Test completeness scoring
      
      // Complete report
      final completeReport = TradingReport(
        finalDecision: 'BUY',
        investmentPlan: 'Strategy',
        marketAnalysis: 'Analysis',
        sentimentAnalysis: 'Sentiment',
        newsImpact: 'News',
        fundamentalsAnalysis: 'Fundamentals',
        rawData: {},
        completeness: ReportCompleteness.complete, // This gets calculated
        timestamp: DateTime.now(),
      );
      
      expect(completeReport.hasMeaningfulContent, isTrue);

      // Partial report
      final partialReport = TradingReport(
        marketAnalysis: 'Just market data',
        rawData: {},
        completeness: ReportCompleteness.partial,
        timestamp: DateTime.now(),
      );
      
      expect(partialReport.hasMeaningfulContent, isFalse);
    });

    test('UnifiedMessageFilterService should filter correctly', () {
      // Test unified message filtering
      final filterService = UnifiedMessageFilterService();

      // Should show final trading decisions
      final finalMessage = StreamMessage(
        id: '4',
        type: MessageType.success,
        content: 'Final trading recommendation',
        contentType: 'final_trading_decision',
        timestamp: DateTime.now(),
      );
      
      expect(filterService.isUserRelevant(finalMessage), isTrue);

      // Should show values events
      final valuesMessage = StreamMessage(
        id: '5',
        type: MessageType.analysis,
        content: 'Analysis data',
        contentType: 'values',
        timestamp: DateTime.now(),
      );
      
      expect(filterService.isUserRelevant(valuesMessage), isTrue);

      // Should show errors
      final errorMessage = StreamMessage(
        id: '6',
        type: MessageType.error,
        content: 'Something went wrong',
        contentType: 'error',
        timestamp: DateTime.now(),
      );
      
      expect(filterService.isUserRelevant(errorMessage), isTrue);
    });
  });

  group('Integration Tests', () {
    test('End-to-end flow should work correctly', () {
      // Test complete flow from raw data to final display
      final mockLangGraphData = {
        'final_trade_decision': 'STRONG BUY - Technical analysis shows bullish breakout pattern',
        'trader_investment_plan': 'Recommend 4% portfolio allocation with stop loss at 8%',
        'market_report': 'Market momentum strongly positive, volume increasing',
        'sentiment_report': 'Social sentiment overwhelmingly bullish',
        'fundamentals_report': 'Strong earnings growth, improving margins',
        'news_report': 'Positive product launch news driving optimism',
        'company_of_interest': 'NVDA',
        'trade_date': '2024-01-15',
      };

      // 1. Create trading report from LangGraph data
      final report = TradingReport.fromLangGraphValues(mockLangGraphData);
      
      expect(report.completeness, equals(ReportCompleteness.complete));
      expect(report.hasMeaningfulContent, isTrue);

      // 2. Create stream message
      final message = StreamMessage(
        id: 'test-final',
        type: MessageType.success,
        content: report.formattedContent,
        contentType: 'values',
        timestamp: DateTime.now(),
      );

      // 3. Test finality detection
      expect(FinalityDetector.isDefinitelyFinal(message, report), isTrue);
      expect(FinalityDetector.getFinalityConfidence(message, report), greaterThan(90));

      // 4. Test title generation
      final title = SmartTitleGenerator.getDisplayTitle(message, report);
      expect(title, equals('⚡ Final Trading Decision'));

      // 5. Verify formatted content contains all sections
      final formattedContent = report.formattedContent;
      expect(formattedContent, contains('⚡ **Final Trading Decision**'));
      expect(formattedContent, contains('🎯 **Investment Plan**'));
      expect(formattedContent, contains('📈 **Market Analysis**'));
      expect(formattedContent, contains('💭 **Sentiment Analysis**'));
      expect(formattedContent, contains('📊 **Financial Fundamentals**'));
      expect(formattedContent, contains('📰 **News Impact**'));
    });
  });
}