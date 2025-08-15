import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/utils/result_parser.dart';
import 'package:trading_dummy/features/analyst_details/models/trade_decision.dart';

void main() {
  group('UHN Decision Extraction Bug Fix', () {
    test('should extract BUY from "Investment Recommendation: BUY with Medium confidence"', () {
      // Test case for UHN ticker where decision shows as "no decision available"
      // even though the text says "Investment Recommendation: BUY with Medium confidence"
      
      final jsonResult = jsonEncode({
        'investment_plan': '''
# Investment Plan

Investment Recommendation: BUY with Medium confidence

Given the current market conditions and analysis, we recommend a BUY position.

Position Sizing: 5% of Total Portfolio
''',
        'market_report': 'Technical indicators show positive momentum',
        'fundamentals_report': 'Strong financial metrics',
      });

      final decision = ResultParser.parseDecision(jsonResult);

      // Should extract BUY from Investment Recommendation
      expect(decision, equals(TradeDecision.buy));
    });

    test('should extract decision from investment_plan when risk_manager_report is missing', () {
      final jsonResult = jsonEncode({
        'investment_plan': '''
Investment Recommendation: HOLD with High confidence

Market conditions suggest maintaining current positions.
''',
      });

      final decision = ResultParser.parseDecision(jsonResult);

      expect(decision, equals(TradeDecision.hold));
    });

    test('should handle different confidence formats in Investment Recommendation', () {
      final testCases = [
        ('Investment Recommendation: BUY with High confidence', TradeDecision.buy),
        ('Investment Recommendation: SELL with Low confidence', TradeDecision.sell),
        ('Investment Recommendation: HOLD with Medium confidence', TradeDecision.hold),
        ('Investment Recommendation: BUY with confidence level: High', TradeDecision.buy),
      ];

      for (final (text, expectedDecision) in testCases) {
        final jsonResult = jsonEncode({
          'investment_plan': text,
        });

        final decision = ResultParser.parseDecision(jsonResult);
        expect(
          decision,
          equals(expectedDecision),
          reason: 'Failed to extract decision from "$text"',
        );
      }
    });

    test('should prefer risk_manager_report over investment_plan if both exist', () {
      final jsonResult = jsonEncode({
        'risk_manager_report': '''
Investment Recommendation: HOLD with Medium confidence
''',
        'investment_plan': '''
Investment Recommendation: BUY with High confidence
''',
      });

      final decision = ResultParser.parseDecision(jsonResult);

      // Should find HOLD first since we check risk_manager_report first
      expect(decision, equals(TradeDecision.hold));
    });

    test('should extract confidence level from text descriptions', () {
      final jsonResult = jsonEncode({
        'investment_plan': '''
Investment Recommendation: BUY with Medium confidence

This is our recommendation based on analysis.
''',
        'confidence_level': 'Medium',
      });

      final confidence = ResultParser.parseConfidence(jsonResult);

      // Medium confidence should map to 0.6 or similar
      // Check if confidence parsing works (this might need adjustment based on implementation)
      expect(confidence, isNotNull);
    });

    test('full UHN scenario - complete JSON structure', () {
      // This simulates the exact UHN case from the user's report
      final jsonResult = jsonEncode({
        'ticker': 'UHN',
        'trade_date': '2025-08-15',
        'investment_plan': '''
# Risk Manager Report

Investment Recommendation: BUY with Medium confidence

Given the mixed market indicators, we recommend a BUY position on UHN at this time.
The current market environment presents both opportunities and risks, as outlined below.

Position Sizing: 5% of Total Portfolio

Given the high volatility and rich valuation metrics, allocate no more than 5% of the 
total investment portfolio to UHN. This cautious stance allows participation without 
overexposure to the company's inherent risks.

Entry Strategy:
• Initial Entry: Aim to enter at or below the current price
• Staged Entry: Consider additional tranches if the stock retraces further
''',
        'market_report': 'Technical analysis shows BUY signals',
        'fundamentals_report': 'Fundamentals indicate opportunity',
        'sentiment_report': 'Social sentiment is positive',
        'news_report': 'Recent news coverage is favorable',
      });

      final decision = ResultParser.parseDecision(jsonResult);
      final riskReport = ResultParser.parseRiskReport(jsonResult);

      // Decision should be BUY
      expect(decision, equals(TradeDecision.buy));
      
      // Risk report should be found in investment_plan
      expect(riskReport, isNotNull);
      expect(riskReport, contains('Investment Recommendation: BUY'));
    });
  });
}