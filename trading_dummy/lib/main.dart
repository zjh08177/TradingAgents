import 'package:flutter/material.dart';
import 'core/config/app_config.dart';
import 'data/datasources/langgraph_datasource.dart';
import 'data/repositories/trading_repository_impl.dart';
import 'domain/repositories/trading_repository.dart';
import 'presentation/pages/trading_analysis_page.dart';
import 'core/utils/logger.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  Logger.log('Initializing Trading Dummy App');
  
  // Initialize configuration
  await AppConfig.initialize();
  Logger.log('Configuration loaded');
  
  // Set up dependencies
  final dataSource = LangGraphDataSource(
    baseUrl: AppConfig.langGraphUrl,
    apiKey: AppConfig.langSmithApiKey,
    assistantId: AppConfig.assistantId,
  );
  
  final repository = TradingRepositoryImpl(
    dataSource: dataSource,
  );
  
  Logger.log('Dependencies initialized');
  
  runApp(MyApp(repository: repository));
}

class MyApp extends StatelessWidget {
  final TradingRepository repository;
  
  const MyApp({
    super.key,
    required this.repository,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Analysis',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: TradingAnalysisPage(repository: repository),
    );
  }
}
