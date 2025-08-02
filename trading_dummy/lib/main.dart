import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'services/langgraph_service.dart';
import 'services/auto_test.dart';
import 'core/logging/app_logger.dart';
import 'auth/auth_module.dart';
import 'services/service_provider.dart';
import 'pages/analysis_page_wrapper.dart';
import 'history/infrastructure/models/hive_history_entry.dart';
import 'history/infrastructure/models/hive_analysis_details.dart';
import 'history/infrastructure/repositories/hive_history_repository.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  AppLogger.info('main', '🚀 Starting Simplified Trading App...');
  
  try {
    // Load environment variables
    AppLogger.info('main', '📝 Loading environment configuration...');
    await dotenv.load(fileName: '.env');
    AppLogger.info('main', '✅ Environment configuration loaded');
    
    // Initialize Hive
    AppLogger.info('main', '💾 Initializing Hive database...');
    await Hive.initFlutter();
    
    // Register Hive adapters
    Hive.registerAdapter(HiveHistoryEntryAdapter());
    Hive.registerAdapter(HiveAnalysisDetailsAdapter());
    
    // Open Hive boxes
    await HiveHistoryRepository.openBox();
    AppLogger.info('main', '✅ Hive database initialized');
    
    // Get LangGraph configuration
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
    
    // Create simple service
    AppLogger.info('main', '🔧 Setting up simplified LangGraph service...');
    final langGraphService = SimpleLangGraphService(
      url: langGraphUrl,
      apiKey: langSmithApiKey,
      assistantId: assistantId,
    );
    
    // Create auto-test controller
    final autoTest = AutoTestController();
    
    AppLogger.info('main', '✅ Services initialized - ready for final report display');
    
    // Start the app with authentication
    runApp(TradingApp(
      langGraphService: langGraphService,
      autoTest: autoTest,
    ));
    
  } catch (e, stackTrace) {
    AppLogger.error('main', '💥 Failed to initialize app', e, stackTrace);
    runApp(ErrorApp(error: e.toString()));
  }
}

class TradingApp extends StatelessWidget {
  final SimpleLangGraphService langGraphService;
  final AutoTestController autoTest;
  
  const TradingApp({
    super.key,
    required this.langGraphService,
    required this.autoTest,
  });

  @override
  Widget build(BuildContext context) {
    return ServiceProvider(
      langGraphService: langGraphService,
      autoTest: autoTest,
      child: MultiProvider(
        providers: [
          ChangeNotifierProvider(
            create: (_) => AuthViewModel(),
          ),
        ],
        child: MaterialApp(
          title: 'Trading Analysis',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
            useMaterial3: true,
          ),
          initialRoute: '/',
          routes: {
            '/': (context) => const SplashScreen(),
            '/login': (context) => const LoginScreen(),
            '/home': (context) => AuthGuard(
              child: const HomeScreen(),
            ),
            '/analysis': (context) => const AuthGuard(
              child: AnalysisPageWrapper(),
            ),
          },
        ),
      ),
    );
  }
}

/// Widget that guards routes requiring authentication
class AuthGuard extends StatelessWidget {
  final Widget child;
  
  const AuthGuard({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthViewModel>(
      builder: (context, authViewModel, _) {
        // Listen to auth state changes
        if (!authViewModel.isAuthenticated) {
          // If not authenticated, navigate to login
          WidgetsBinding.instance.addPostFrameCallback((_) {
            Navigator.of(context).pushReplacementNamed('/login');
          });
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        }
        
        // Check if token needs refresh
        if (authViewModel.willTokenExpireSoon) {
          authViewModel.refreshTokenIfNeeded();
        }
        
        return child;
      },
    );
  }
}

class ErrorApp extends StatelessWidget {
  final String error;
  
  const ErrorApp({super.key, required this.error});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Analysis - Error',
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
                const Icon(Icons.error, color: Colors.red, size: 64),
                const SizedBox(height: 16),
                const Text(
                  'Configuration Error',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.red),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                Text(error, style: const TextStyle(fontSize: 14), textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      ),
    );
  }
}