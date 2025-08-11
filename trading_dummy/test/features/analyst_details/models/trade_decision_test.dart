import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/features/analyst_details/models/trade_decision.dart';

void main() {
  group('TradeDecision', () {
    group('fromString', () {
      test('parses BUY correctly', () {
        expect(TradeDecision.fromString('BUY'), TradeDecision.buy);
        expect(TradeDecision.fromString('buy'), TradeDecision.buy);
        expect(TradeDecision.fromString('Buy'), TradeDecision.buy);
        expect(TradeDecision.fromString(' BUY '), TradeDecision.buy);
      });

      test('parses SELL correctly', () {
        expect(TradeDecision.fromString('SELL'), TradeDecision.sell);
        expect(TradeDecision.fromString('sell'), TradeDecision.sell);
        expect(TradeDecision.fromString('Sell'), TradeDecision.sell);
        expect(TradeDecision.fromString(' SELL '), TradeDecision.sell);
      });

      test('parses HOLD correctly', () {
        expect(TradeDecision.fromString('HOLD'), TradeDecision.hold);
        expect(TradeDecision.fromString('hold'), TradeDecision.hold);
        expect(TradeDecision.fromString('Hold'), TradeDecision.hold);
        expect(TradeDecision.fromString(' HOLD '), TradeDecision.hold);
      });

      test('returns null for invalid strings', () {
        expect(TradeDecision.fromString('invalid'), null);
        expect(TradeDecision.fromString(''), null);
        expect(TradeDecision.fromString('BUYY'), null);
        expect(TradeDecision.fromString('HODL'), null);
      });

      test('returns null for null input', () {
        expect(TradeDecision.fromString(null), null);
      });
    });

    group('display properties', () {
      test('BUY has correct display properties', () {
        expect(TradeDecision.buy.displayName, 'BUY');
        expect(TradeDecision.buy.color, Colors.green);
        expect(TradeDecision.buy.icon, Icons.trending_up);
      });

      test('SELL has correct display properties', () {
        expect(TradeDecision.sell.displayName, 'SELL');
        expect(TradeDecision.sell.color, Colors.red);
        expect(TradeDecision.sell.icon, Icons.trending_down);
      });

      test('HOLD has correct display properties', () {
        expect(TradeDecision.hold.displayName, 'HOLD');
        expect(TradeDecision.hold.color, Colors.orange);
        expect(TradeDecision.hold.icon, Icons.pause_circle_outline);
      });
    });

    group('enum values', () {
      test('has exactly 3 values', () {
        expect(TradeDecision.values.length, 3);
      });

      test('contains all expected values', () {
        expect(TradeDecision.values, contains(TradeDecision.buy));
        expect(TradeDecision.values, contains(TradeDecision.sell));
        expect(TradeDecision.values, contains(TradeDecision.hold));
      });

      test('values are in expected order', () {
        expect(TradeDecision.values[0], TradeDecision.buy);
        expect(TradeDecision.values[1], TradeDecision.sell);
        expect(TradeDecision.values[2], TradeDecision.hold);
      });
    });
  });
}