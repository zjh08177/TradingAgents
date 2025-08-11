import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/utils/result_parser.dart';
import 'dart:convert';

void main() {
  group('TradeDecision Extraction Tests', () {
    test('extracts BUY from "BUY - Strong bullish outlook"', () {
      final json = jsonEncode({
        'final_trade_decision': 'BUY - Strong bullish outlook based on technical analysis',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'BUY');
    });
    
    test('extracts SELL from "SELL - Bearish signals detected"', () {
      final json = jsonEncode({
        'final_trade_decision': 'SELL - Bearish signals detected in market',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'SELL');
    });
    
    test('extracts HOLD from "HOLD - Wait for better entry"', () {
      final json = jsonEncode({
        'final_trade_decision': 'HOLD - Wait for better entry point',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'HOLD');
    });
    
    test('extracts from simple decision values', () {
      final json = jsonEncode({
        'trade_decision': 'BUY',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'BUY');
    });
    
    test('extracts from EMERGENCY INVESTMENT RECOMMENDATION', () {
      final json = jsonEncode({
        'risk_manager_report': 'EMERGENCY INVESTMENT RECOMMENDATION: HOLD\nDue to debate termination...',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'HOLD');
    });
    
    test('extracts BUY from text containing the word', () {
      final json = jsonEncode({
        'final_trade_decision': 'STRONG BUY SIGNAL',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'BUY');
    });
    
    test('prioritizes direct fields over nested text', () {
      final json = jsonEncode({
        'final_trade_decision': 'BUY - Direct field',
        'investment_plan': 'We recommend SELL position',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'BUY');
    });
    
    test('handles mixed case decisions', () {
      final json = jsonEncode({
        'trade_decision': 'Buy',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'BUY');
    });
    
    test('returns null for invalid decision text', () {
      final json = jsonEncode({
        'final_trade_decision': 'UNKNOWN - Cannot determine',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision, isNull);
    });
    
    test('extracts from investment plan when no direct field', () {
      final json = jsonEncode({
        'trader_investment_plan': 'Based on analysis, we recommend a HOLD position',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.displayName, 'HOLD');
    });
  });
  
  group('Trade Decision Icon Tests', () {
    test('BUY decision has correct icon and color', () {
      final json = jsonEncode({
        'final_trade_decision': 'BUY - Strong growth potential',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.icon, Icons.trending_up);
      expect(decision?.color, Colors.green);
    });
    
    test('SELL decision has correct icon and color', () {
      final json = jsonEncode({
        'trade_decision': 'SELL',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.icon, Icons.trending_down);
      expect(decision?.color, Colors.red);
    });
    
    test('HOLD decision has correct icon and color', () {
      final json = jsonEncode({
        'final_decision': 'HOLD',
      });
      
      final decision = ResultParser.parseDecision(json);
      expect(decision?.icon, Icons.pause_circle_outline);
      expect(decision?.color, Colors.orange);
    });
  });
}