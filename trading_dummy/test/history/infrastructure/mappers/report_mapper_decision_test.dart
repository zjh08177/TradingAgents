import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/models/final_report.dart';
import 'package:trading_dummy/history/infrastructure/mappers/report_mapper.dart';

void main() {
  group('ReportMapper Decision Extraction', () {
    late ReportMapper mapper;

    setUp(() {
      mapper = ReportMapper();
    });

    test('should correctly extract HOLD from Investment Recommendation format', () {
      // This test replicates the exact issue from the screenshot
      final report = FinalReport(
        ticker: 'TSLA',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
# Risk Manager Report

Investment Recommendation: HOLD (Confidence Level: Medium)

The analysis presents both bullish and bearish perspectives, ultimately leading to a recommendation to hold shares of Tesla (TSLA). The innovative potential and growth vectors suggested by bullish analysts are balanced by valuation concerns and mixed sentiment, suggesting a more cautious stance.

Position Sizing: Given the HOLD recommendation, retain existing positions. For new investors looking for exposure, allocate no more than 5% of their portfolio to TSLA, allowing room for potential changes in the investment thesis.

Entry Strategy:
• Current Price: \$335.58
• Consider entering or increasing positions if the stock retraces to its 20-day simple moving average (SMA-20) around \$323.28 or if there are clear technical signals indicating a reversal after a pullback.

Some analysts might say BUY based on innovation potential, while others suggest SELL due to valuation concerns.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      // The decision should be HOLD, not BUY
      expect(entry.finalDecision, equals('HOLD'));
      expect(entry.confidence, equals(0.60)); // Medium confidence
    });

    test('should extract BUY when it is the actual recommendation', () {
      final report = FinalReport(
        ticker: 'AAPL',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
# Risk Manager Report

Investment Recommendation: BUY (Confidence Level: High)

Strong fundamentals and positive market sentiment support a buy recommendation.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      expect(entry.finalDecision, equals('BUY'));
      expect(entry.confidence, equals(0.85)); // High confidence
    });

    test('should extract SELL when it is the actual recommendation', () {
      final report = FinalReport(
        ticker: 'XYZ',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
Investment Recommendation: SELL (Confidence Level: Low)

Deteriorating fundamentals suggest exiting positions.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      expect(entry.finalDecision, equals('SELL'));
      expect(entry.confidence, equals(0.35)); // Low confidence
    });

    test('should not be confused by other mentions of BUY/SELL/HOLD', () {
      final report = FinalReport(
        ticker: 'MSFT',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
Some analysts recommend BUY due to strong earnings.
Others suggest SELL because of high valuation.
Many prefer to HOLD and wait for clarity.

# Final Analysis

Investment Recommendation: HOLD (Confidence Level: Medium)

After considering all factors, we recommend holding current positions.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      // Should extract HOLD from the explicit recommendation, not BUY from earlier text
      expect(entry.finalDecision, equals('HOLD'));
    });

    test('should handle Final Decision format', () {
      final report = FinalReport(
        ticker: 'GOOGL',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
After thorough analysis...

Final Decision: BUY

Strong growth prospects ahead.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      expect(entry.finalDecision, equals('BUY'));
    });

    test('should handle Trading Decision format', () {
      final report = FinalReport(
        ticker: 'AMZN',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
Based on our analysis...

Trading Decision: SELL

Concerns about margin compression.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      expect(entry.finalDecision, equals('SELL'));
    });

    test('should fallback to sentiment analysis when no explicit decision', () {
      final report = FinalReport(
        ticker: 'NVDA',
        tradeDate: '2025-08-14',
        timestamp: DateTime.now(),
        content: '''
The stock shows strong bullish momentum with buy signals across multiple indicators.
Technical analysis is bullish with positive trends.
Fundamentals remain bullish with strong earnings growth.
''',
        isError: false,
      );

      final entry = mapper.map(report);

      // With no explicit recommendation, should analyze sentiment
      expect(entry.finalDecision, equals('BUY'));
    });

    test('should handle various confidence level formats', () {
      final testCases = [
        ('Confidence Level: High', 0.85),
        ('Confidence Level: Medium', 0.60),
        ('Confidence Level: Low', 0.35),
        ('confidence: 75%', 0.75),
        ('80% confidence', 0.80),
        ('certainty: 0.9', 0.9),
      ];

      for (final (text, expectedConfidence) in testCases) {
        final report = FinalReport(
          ticker: 'TEST',
          tradeDate: '2025-08-14',
          timestamp: DateTime.now(),
          content: 'Investment Recommendation: HOLD\n$text',
          isError: false,
        );

        final entry = mapper.map(report);
        expect(
          entry.confidence,
          equals(expectedConfidence),
          reason: 'Failed to extract confidence from "$text"',
        );
      }
    });
  });
}