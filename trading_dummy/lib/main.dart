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
import 'history/presentation/screens/history_screen.dart';
import 'history/presentation/screens/history_detail_screen.dart';
// Job system imports for Phase 7 UI testing
import 'jobs/infrastructure/models/hive_analysis_job.dart';
import 'jobs/infrastructure/repositories/hive_job_repository.dart';
import 'jobs/application/use_cases/queue_analysis_use_case.dart';
import 'jobs/application/use_cases/get_job_status_use_case.dart';
import 'jobs/application/use_cases/cancel_job_use_case.dart';
import 'jobs/presentation/view_models/job_queue_view_model.dart';
import 'jobs/presentation/view_models/job_list_view_model.dart';
import 'jobs/presentation/screens/job_test_screen.dart';
// Phase 8: Notification system imports
import 'jobs/infrastructure/services/job_notification_handler.dart';
import 'jobs/infrastructure/services/job_queue_manager.dart';
// Phase 9: Retry system imports
import 'jobs/infrastructure/services/retry_scheduler.dart';

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
    Hive.registerAdapter(HiveAnalysisJobAdapter());
    
    // Open Hive boxes
    await HiveHistoryRepository.openBox();
    
    // Initialize job repository
    final jobRepository = HiveJobRepository();
    await jobRepository.init();
    
    // Initialize job queue manager for Phase 8
    final jobQueueManager = JobQueueManager(repository: jobRepository);
    await jobQueueManager.initialize();
    
    // Initialize retry scheduler for Phase 9 with queue manager
    final retryScheduler = RetryScheduler(
      repository: jobRepository,
      queueManager: jobQueueManager,
    );
    await retryScheduler.initialize();
    
    // Initialize notification handler for Phase 8
    final notificationHandler = JobNotificationHandler();
    await notificationHandler.initialize();
    
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
      jobRepository: jobRepository,
      jobQueueManager: jobQueueManager,
      notificationHandler: notificationHandler,
      retryScheduler: retryScheduler,
    ));
    
  } catch (e, stackTrace) {
    AppLogger.error('main', '💥 Failed to initialize app', e, stackTrace);
    runApp(ErrorApp(error: e.toString()));
  }
}

class TradingApp extends StatelessWidget {
  final SimpleLangGraphService langGraphService;
  final AutoTestController autoTest;
  final HiveJobRepository jobRepository;
  final JobQueueManager jobQueueManager;
  final JobNotificationHandler notificationHandler;
  final RetryScheduler retryScheduler;
  
  const TradingApp({
    super.key,
    required this.langGraphService,
    required this.autoTest,
    required this.jobRepository,
    required this.jobQueueManager,
    required this.notificationHandler,
    required this.retryScheduler,
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
          // Job system providers for Phase 8 UI testing with notifications
          ChangeNotifierProvider(
            create: (_) => JobQueueViewModel(
              queueAnalysis: QueueAnalysisUseCase(
                repository: jobRepository,
                queueManager: jobQueueManager,
              ),
              getJobStatus: GetJobStatusUseCase(repository: jobRepository),
              cancelJob: CancelJobUseCase(
                repository: jobRepository,
                queueManager: jobQueueManager,
              ),
            ),
          ),
          ChangeNotifierProvider(
            create: (_) => JobListViewModel(
              getJobStatus: GetJobStatusUseCase(repository: jobRepository),
            ),
          ),
        ],
        child: Builder(
          builder: (context) {
            // Initialize notification handler with navigation context
            WidgetsBinding.instance.addPostFrameCallback((_) {
              notificationHandler.updateNavigationContext(context);
            });
            
            return MaterialApp(
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
                '/history': (context) => const AuthGuard(
                  child: HistoryScreen(),
                ),
                '/jobs': (context) => const AuthGuard(
                  child: JobTestScreen(),
                ),
              },
            );
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