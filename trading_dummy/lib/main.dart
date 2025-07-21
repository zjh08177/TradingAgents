import 'package:flutter/material.dart';
import 'services/langchain_service.dart';
import 'services/config_service.dart';
import 'services/langgraph_client.dart';
import 'pages/settings_page.dart';
import 'services/logger_service.dart';
import 'models/langgraph_models.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize configuration service
  await ConfigService.instance.initialize();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trading Dummy',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const TradingAnalysisPage(),
    );
  }
}

class TradingAnalysisPage extends StatefulWidget {
  const TradingAnalysisPage({super.key});

  @override
  State<TradingAnalysisPage> createState() => _TradingAnalysisPageState();
}

class _TradingAnalysisPageState extends State<TradingAnalysisPage> {
  final TextEditingController _tickerController = TextEditingController();
  late LangGraphClient _langGraphClient;
  
  bool _isLoading = false;
  bool _isInitialized = false;
  String _result = '';
  String _error = '';
  String _statusMessage = '';
  bool _hasRunAutomatedTest = false;

  @override
  void initState() {
    super.initState();
    _initializeLangGraphClient();
  }

  @override
  void dispose() {
    _tickerController.dispose();
    _langGraphClient.dispose();
    super.dispose();
  }

  Future<void> _initializeLangGraphClient() async {
    try {
      LoggerService.info('app', '==================== LANGGRAPH CLIENT INITIALIZATION ====================');
      LoggerService.info('app', 'Initializing LangGraph client...');
      
      // Configure LangGraph client with localhost for testing
      // In production, this should be your deployed server URL
      const serverUrl = 'http://localhost:8000';
      
      _langGraphClient = LangGraphClient(
        baseUrl: serverUrl,
        timeout: const Duration(seconds: 120),
      );
      
      // Check server health
      LoggerService.info('app', 'Checking LangGraph server health...');
      final isHealthy = await _langGraphClient.checkHealth();
      
      if (isHealthy) {
        LoggerService.info('app', '✅ LangGraph server is healthy and ready');
        setState(() {
          _isInitialized = true;
        });
        
        // Start automated test after 2 seconds
        _scheduleAutomatedTest();
      } else {
        LoggerService.error('app', '❌ LangGraph server health check failed');
        setState(() {
          _error = 'LangGraph server is not responding. Please ensure the server is running on $serverUrl';
        });
      }
    } catch (e) {
      LoggerService.error('app', 'Failed to initialize LangGraph client: $e');
      setState(() {
        _error = 'Failed to initialize LangGraph client: $e';
      });
    }
  }

  void _scheduleAutomatedTest() {
    LoggerService.info('app', '⏰ Scheduling automated test with TSLA in 2 seconds...');
    
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted && !_hasRunAutomatedTest) {
        LoggerService.info('app', '🤖 AUTOMATED TEST: Starting analysis for TSLA');
        _hasRunAutomatedTest = true;
        _tickerController.text = 'TSLA';
        _analyzeStock();
      }
    });
  }

  Future<void> _analyzeStock() async {
    if (!_isInitialized) {
      setState(() {
        _error = 'LangGraph client is not initialized. Please check server connection.';
        _result = '';
      });
      return;
    }

    final ticker = _tickerController.text.trim().toUpperCase();
    
    if (ticker.isEmpty) {
      setState(() {
        _error = 'Please enter a ticker symbol';
        _result = '';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = '';
      _result = '';
      _statusMessage = 'Connecting to LangGraph server...';
    });

    try {
      LoggerService.info('app', '==================== STARTING LANGGRAPH ANALYSIS ====================');
      LoggerService.info('app', 'Ticker: $ticker');
      LoggerService.info('app', 'Timestamp: ${DateTime.now().toIso8601String()}');
      
      // Update status
      setState(() {
        _statusMessage = 'Analyzing $ticker with LangGraph agents...';
      });
      
      // Call LangGraph server
      final analysisResult = await _langGraphClient.analyzeTicker(ticker);
      
      LoggerService.info('app', 'LangGraph analysis completed successfully');
      LoggerService.info('app', 'Processing signal: ${analysisResult.processedSignal ?? "N/A"}');
      
      // Format and display results
      final formattedResult = analysisResult.getFormattedSummary();
      
      setState(() {
        _result = formattedResult;
        _statusMessage = '';
        _isLoading = false;
      });
      
      // Log analysis completion
      LoggerService.info('app', '==================== LANGGRAPH ANALYSIS COMPLETE ====================');
      LoggerService.info('app', 'Result displayed to user');
      
    } catch (e) {
      LoggerService.error('app', 'LangGraph analysis failed: $e');
      setState(() {
        _error = 'Analysis failed: $e';
        _statusMessage = '';
        _isLoading = false;
      });
    }
  }

  Future<void> _navigateToSettings() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const SettingsPage()),
    );
    
    // Note: Settings are not used for LangGraph client
    // API keys should be configured on the server side
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Analysis - LangGraph'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            onPressed: _navigateToSettings,
            icon: const Icon(Icons.settings),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: GestureDetector(
        onTap: () {
          // Dismiss keyboard when tapping anywhere on screen
          FocusScope.of(context).unfocus();
        },
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // LangGraph Status Card
              Card(
                color: _isInitialized ? Colors.green.shade50 : Colors.orange.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            _isInitialized ? Icons.check_circle : Icons.warning,
                            color: _isInitialized ? Colors.green : Colors.orange,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'LangGraph Server Status',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: _isInitialized ? Colors.green : Colors.orange,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _isInitialized 
                          ? 'Connected to LangGraph server at http://localhost:8000'
                          : 'Not connected to LangGraph server',
                      ),
                      if (_hasRunAutomatedTest) ...[
                        const SizedBox(height: 8),
                        const Text(
                          '🤖 Automated test has been triggered with TSLA',
                          style: TextStyle(fontStyle: FontStyle.italic),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              if (_isInitialized) ...[
                const SizedBox(height: 16),
                
                // Input bar with GO button
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _tickerController,
                        decoration: const InputDecoration(
                          hintText: 'Enter ticker symbol (e.g., AAPL)',
                          border: OutlineInputBorder(),
                          helperText: 'Analysis powered by remote LangGraph server',
                        ),
                        textCapitalization: TextCapitalization.characters,
                        textInputAction: TextInputAction.go,
                        onSubmitted: (_) {
                          // Dismiss keyboard and trigger analysis
                          FocusScope.of(context).unfocus();
                          _analyzeStock();
                        },
                        onEditingComplete: () {
                          // Dismiss keyboard when Done button is pressed
                          FocusScope.of(context).unfocus();
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    ElevatedButton(
                      onPressed: _isLoading ? null : () {
                        // Dismiss keyboard before analysis
                        FocusScope.of(context).unfocus();
                        _analyzeStock();
                      },
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                      ),
                      child: _isLoading 
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('GO'),
                    ),
                  ],
                ),
              ],
              
              const SizedBox(height: 24),

              // Status Message (when loading)
              if (_statusMessage.isNotEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16.0),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    border: Border.all(color: Colors.blue.shade200),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _statusMessage,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.blue.shade700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              // Result view - only show if there's content
              if (_error.isNotEmpty || _result.isNotEmpty) ...[
                // Error display
                if (_error.isNotEmpty)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16.0),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      border: Border.all(color: Colors.red.shade200),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.error, color: Colors.red, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              'Error',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(_error),
                      ],
                    ),
                  ),

                // Result display
                if (_result.isNotEmpty)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16.0),
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      border: Border.all(color: Colors.green.shade200),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.cloud_sync, color: Colors.green, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              'LangGraph Analysis Results',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Colors.green,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _result,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
              ],
              
              // Debug Information Card (for E2E testing verification)
              if (_isInitialized) ...[
                const SizedBox(height: 24),
                Card(
                  color: Colors.grey.shade100,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'E2E Testing Information',
                          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text('• LangGraph Client: Initialized ✅'),
                        Text('• Server URL: http://localhost:8000'),
                        Text('• Automated Test: ${_hasRunAutomatedTest ? "Executed ✅" : "Pending ⏳"}'),
                        Text('• Check logs for detailed trace'),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
