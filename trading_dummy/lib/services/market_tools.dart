// Market Data Tools - Production implementations
// Uses Yahoo Finance data and technical indicators

import 'market_data_service.dart';
import 'technical_indicators_service.dart';
import 'logger_service.dart';

abstract class MarketTool {
  String get name;
  String get description;
  Future<String> execute(Map<String, dynamic> args);
}

/// Yahoo Finance data tool using yahoo_finance_data_reader package
class YFinDataOnlineTool extends MarketTool {
  @override
  String get name => 'get_YFin_data_online';

  @override
  String get description => 'Get Yahoo Finance stock data with extended metrics';

  @override
  Future<String> execute(Map<String, dynamic> args) async {
    final ticker = args['ticker'] ?? '';
    
    try {
      LoggerService.toolCall('market', 'yfin_data', details: ticker);
      
      final stopwatch = Stopwatch()..start();
      
      // Calculate date range (last 30 days for analysis)
      final endDate = DateTime.now();
      final startDate = endDate.subtract(const Duration(days: 30));
      
      // Get CSV data format matching Python yfinance
      final csvData = await MarketDataService.getYFinDataOnline(
        symbol: ticker,
        startDate: startDate.toIso8601String().split('T')[0],
        endDate: endDate.toIso8601String().split('T')[0],
      );
      
      // Get additional stock info
      final stockInfo = await MarketDataService.getStockInfo(ticker);
      
      // Format comprehensive report
      final buffer = StringBuffer();
      buffer.writeln('Yahoo Finance Data for $ticker');
      buffer.writeln('Generated: ${DateTime.now().toLocal()}');
      buffer.writeln('Data Source: yahoo_finance_data_reader');
      buffer.writeln('');
      
      if (stockInfo.containsKey('error')) {
        buffer.writeln('Error: ${stockInfo['error']}');
        stopwatch.stop();
        LoggerService.toolError('market', 'yfin_data', stockInfo['error'].toString());
        return buffer.toString();
      }
      
      // Current stock information
      buffer.writeln('Stock Information:');
      buffer.writeln('  Current Price: \$${stockInfo['currentPrice']?.toStringAsFixed(2) ?? 'N/A'}');
      buffer.writeln('  Open: \$${stockInfo['open']?.toStringAsFixed(2) ?? 'N/A'}');
      buffer.writeln('  High: \$${stockInfo['high']?.toStringAsFixed(2) ?? 'N/A'}');
      buffer.writeln('  Low: \$${stockInfo['low']?.toStringAsFixed(2) ?? 'N/A'}');
      buffer.writeln('  Volume: ${stockInfo['volume']?.toStringAsFixed(0) ?? 'N/A'} shares');
      buffer.writeln('');
      
      // Performance metrics
      final change = stockInfo['change'] ?? 0.0;
      final changePercent = stockInfo['changePercent'] ?? 0.0;
      final changeSign = change >= 0 ? '+' : '';
      buffer.writeln('Performance:');
      buffer.writeln('  Day Change: $changeSign\$${change.toStringAsFixed(2)} ($changeSign${changePercent.toStringAsFixed(2)}%)');
      buffer.writeln('');
      
      // CSV Data section
      buffer.writeln('Historical Data (Last 30 Days):');
      buffer.writeln(csvData);
      
      final result = buffer.toString();
      
      stopwatch.stop();
      LoggerService.toolComplete('market', 'yfin_data', stopwatch.elapsed, 
        result: '${result.length} chars');
      
      return result;
      
    } catch (e) {
      LoggerService.toolError('market', 'yfin_data', e.toString());
      return 'Error fetching Yahoo Finance data for $ticker: $e';
    }
  }
}

/// Technical indicators tool using custom implementations
class StockStatsIndicatorsOnlineTool extends MarketTool {
  @override
  String get name => 'get_stockstats_indicators_report_online';

  @override
  String get description => 'Generate technical indicators report with market data';

  @override
  Future<String> execute(Map<String, dynamic> args) async {
    final ticker = args['ticker'] ?? '';
    final indicators = args['indicators'] as List<String>? ?? [];
    
    if (indicators.isEmpty) {
      LoggerService.toolError('market', 'indicators', 'No indicators specified');
      return 'Error: No indicators specified for analysis';
    }
    
    try {
      LoggerService.toolCall('market', 'indicators', details: '$ticker (${indicators.join(',')})');
      
      final stopwatch = Stopwatch()..start();
      
      // Use current date for analysis
      final currDate = DateTime.now().toIso8601String().split('T')[0];
      const lookBackDays = 252; // ~1 year of trading data
      
      // Calculate multiple indicators using market data
      final result = await TechnicalIndicatorsService.calculateMultipleIndicators(
        symbol: ticker,
        indicators: indicators,
        currDate: currDate,
        lookBackDays: lookBackDays,
      );
      
      stopwatch.stop();
      LoggerService.toolComplete('market', 'indicators', stopwatch.elapsed, 
        result: '${result.length} chars');
      
      return result;
      
    } catch (e) {
      LoggerService.toolError('market', 'indicators', e.toString());
      return 'Error calculating technical indicators for $ticker: $e';
    }
  }
}

/// Market toolkit - always uses real online tools
class MarketToolkit {
  MarketToolkit();
  
  List<MarketTool> get tools {
    return [
      YFinDataOnlineTool(),
      StockStatsIndicatorsOnlineTool(),
    ];
  }
  
  MarketTool? getTool(String name) {
    try {
      return tools.firstWhere((tool) => tool.name == name);
    } catch (e) {
      return null;
    }
  }
  
  /// Test connectivity to all real market data sources
  Future<Map<String, String>> testConnectivity() async {
    final results = <String, String>{};
    
    try {
      // Test Yahoo Finance connectivity
      print('🧪 Testing Yahoo Finance connectivity...');
      final testSymbol = 'AAPL';
      final stockInfo = await MarketDataService.getStockInfo(testSymbol);
      
      if (stockInfo.containsKey('error')) {
        results['yahoo_finance'] = 'Failed: ${stockInfo['error']}';
      } else {
        results['yahoo_finance'] = 'Connected ✅ (Price: \$${stockInfo['currentPrice']?.toStringAsFixed(2)})';
      }
      
      // Test technical indicators
      print('🧪 Testing technical indicators...');
      final indicatorResult = await TechnicalIndicatorsService.getStockstatsIndicatorsReportOnline(
        symbol: testSymbol,
        indicator: 'rsi',
        currDate: DateTime.now().toIso8601String().split('T')[0],
        lookBackDays: 50,
      );
      
      if (indicatorResult.contains('Error')) {
        results['technical_indicators'] = 'Failed: Indicator calculation error';
      } else {
        results['technical_indicators'] = 'Connected ✅ (RSI calculated successfully)';
      }
      
    } catch (e) {
      results['general'] = 'Test failed with error: $e';
    }
    
    return results;
  }
  
  /// Get supported indicators list
  List<String> get supportedIndicators => [
    'close_50_sma',
    'close_200_sma', 
    'close_10_ema',
    'rsi',
    'macd',
    'macds',
    'macdh',
    'boll',
    'boll_ub',
    'boll_lb',
    'atr',
    'vwma',
    'mfi',
  ];
  
  /// Format supported indicators for display
  String get supportedIndicatorsString {
    return supportedIndicators.join(', ');
  }
} 