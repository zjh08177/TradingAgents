import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'services/langgraph_service.dart';
import 'pages/clean_trading_analysis_page.dart';
import 'core/logging/app_logger.dart';

void main() async {
  // Ensure Flutter binding is initialized
  WidgetsFlutterBinding.ensureInitialized();
  
  AppLogger.info('main', '🚀 Starting Trading Dummy App with LangGraph Cloud integration...');
  
  try {
    // Load environment variables
    AppLogger.info('main', '📝 Loading environment configuration...');
    await dotenv.load(fileName: '.env');
    AppLogger.info('main', '✅ Environment configuration loaded');
    
    // Get LangGraph Cloud configuration from environment
    final langGraphUrl = dotenv.env['LANGGRAPH_URL'];
    final langSmithApiKey = dotenv.env['LANGSMITH_API_KEY'];
    final assistantId = dotenv.env['LANGGRAPH_ASSISTANT_ID'];
    
    // Validate required configuration
    if (langGraphUrl == null || langGraphUrl.isEmpty) {
      throw Exception('LANGGRAPH_URL is required in .env file');
    }
    if (langSmithApiKey == null || langSmithApiKey.isEmpty) {
      throw Exception('LANGSMITH_API_KEY is required in .env file');
    }
    if (assistantId == null || assistantId.isEmpty) {
      throw Exception('LANGGRAPH_ASSISTANT_ID is required in .env file');
    }
    
    // Initialize LangGraph service
    AppLogger.info('main', '🔧 Setting up LangGraph service...');
    final langGraphService = LangGraphServiceFactory.create(
      url: langGraphUrl,
      apiKey: langSmithApiKey,
      assistantId: assistantId,
    );
    
    AppLogger.info('main', '✅ LangGraph service initialized successfully');
    AppLogger.info('main', '🌐 Endpoint: $langGraphUrl');
    AppLogger.info('main', '🤖 Assistant: $assistantId');
    
    // Perform health check
    AppLogger.info('main', '=== STARTING HEALTH CHECK ===');
    try {
      final isHealthy = await langGraphService.checkHealth();
      AppLogger.info('main', '🏥 Health check result: ${isHealthy ? "PASSED" : "FAILED"}');
    } catch (e) {
      AppLogger.error('main', 'Health check threw exception', e);
    }
    AppLogger.info('main', '=== HEALTH CHECK COMPLETE ===');
    
    // Start the app with LangGraph Cloud integration
    AppLogger.info('main', '🎯 Starting Flutter app...');
    runApp(MyApp(langGraphService: langGraphService));
    
  } catch (e, stackTrace) {
    AppLogger.error('main', '💥 Failed to initialize app', e, stackTrace);
    
    // Still try to run the app with a fallback error screen
    runApp(ErrorApp(error: e.toString()));
  }
}

class MyApp extends StatelessWidget {
  final ILangGraphService langGraphService;
  
  const MyApp({
    super.key,
    required this.langGraphService,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Analysis - LangGraph Cloud',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: CleanTradingAnalysisPage(
        langGraphService: langGraphService,
      ),
    );
  }
}

/// Error app to display when initialization fails
class ErrorApp extends StatelessWidget {
  final String error;
  
  const ErrorApp({super.key, required this.error});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Analysis - Configuration Error',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.red),
        useMaterial3: true,
      ),
      home: Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.cloud_off,
                  color: Colors.red,
                  size: 64,
                ),
                const SizedBox(height: 16),
                const Text(
                  'LangGraph Cloud Configuration Error',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.red,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                Text(
                  error,
                  style: const TextStyle(fontSize: 14),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 24),
                const Text(
                  'Please check your .env file configuration:\n'
                  '• LANGGRAPH_URL\n'
                  '• LANGSMITH_API_KEY\n'
                  '• LANGGRAPH_ASSISTANT_ID',
                  style: TextStyle(fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
