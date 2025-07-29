import 'package:flutter/material.dart';
import 'core/config/app_config.dart';
import 'data/datasources/langgraph_datasource.dart';
import 'data/repositories/trading_repository_impl.dart';
import 'domain/repositories/trading_repository.dart';
import 'presentation/pages/trading_analysis_page.dart';
import 'core/utils/logger.dart';

void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();
  
  Logger.log('🚀 Starting Trading Dummy App initialization...');
  
  try {
    // Initialize configuration with error handling
    Logger.log('📝 Loading configuration...');
    await AppConfig.initialize();
    Logger.success('Configuration loaded successfully');
    
    // Set up dependencies
    Logger.log('🔧 Setting up dependencies...');
    final dataSource = LangGraphDataSource(
      baseUrl: AppConfig.langGraphUrl,
      apiKey: AppConfig.langSmithApiKey,
      assistantId: AppConfig.assistantId,
    );
    
    final repository = TradingRepositoryImpl(
      dataSource: dataSource,
    );
    
    Logger.success('Dependencies initialized successfully');
    
    // Start the app
    Logger.log('🎯 Starting Flutter app...');
    runApp(MyApp(repository: repository));
    
  } catch (e, stackTrace) {
    Logger.error('💥 Failed to initialize app', {
      'error': e.toString(),
      'stackTrace': stackTrace.toString(),
    });
    
    // Still try to run the app with a fallback error screen
    runApp(const ErrorApp());
  }
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

/// Error app to display when initialization fails
class ErrorApp extends StatelessWidget {
  const ErrorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Analysis - Error',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.red),
        useMaterial3: true,
      ),
      home: const Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                color: Colors.red,
                size: 64,
              ),
              SizedBox(height: 16),
              Text(
                'Failed to Initialize App',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.red,
                ),
              ),
              SizedBox(height: 8),
              Text(
                'Please check the configuration and try again.',
                style: TextStyle(fontSize: 16),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
