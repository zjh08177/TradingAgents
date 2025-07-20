import 'package:flutter/material.dart';
import 'services/langchain_service.dart';
import 'services/config_service.dart';
import 'services/trading_graph.dart';
import 'pages/settings_page.dart';

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
  final LangChainService _langChainService = LangChainService.instance;
  final ConfigService _configService = ConfigService.instance;
  late final TradingGraph _tradingGraph;
  
  bool _isLoading = false;
  bool _isInitialized = false;
  String _result = '';
  String _error = '';
  String _statusMessage = '';

  @override
  void initState() {
    super.initState();
    _initializeLangChain();
  }

  @override
  void dispose() {
    _tickerController.dispose();
    super.dispose();
  }

  Future<void> _initializeLangChain() async {
    try {
      // Try to get API keys from secure storage or .env
      final openaiKey = await _configService.getOpenAIKey();
      final googleKey = await _configService.getGoogleKey();
      
      if (openaiKey != null && openaiKey.isNotEmpty) {
        await _langChainService.initialize(
          provider: LLMProvider.openai,
          apiKey: openaiKey,
        );
        _tradingGraph = TradingGraph(_langChainService, useOnlineTools: true);
        setState(() {
          _isInitialized = true;
        });
      } else if (googleKey != null && googleKey.isNotEmpty) {
        await _langChainService.initialize(
          provider: LLMProvider.google,
          apiKey: googleKey,
        );
        _tradingGraph = TradingGraph(_langChainService, useOnlineTools: true);
        setState(() {
          _isInitialized = true;
        });
      } else {
        setState(() {
          _error = 'No API key found. Please configure your API keys in Settings.';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Failed to initialize: $e';
      });
    }
  }

  Future<void> _analyzeStock() async {
    if (!_isInitialized) {
      setState(() {
        _error = 'Please configure your API keys in Settings first.';
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
      _statusMessage = 'Initializing trading analysis...';
    });

    try {
      final today = DateTime.now().toIso8601String().split('T')[0];
      
      // Run the full trading graph
      final finalState = await _tradingGraph.execute(ticker, today);
      
      // Get the final recommendation
      final recommendation = _tradingGraph.getFinalRecommendation(finalState);
      
      setState(() {
        _result = recommendation;
        _statusMessage = '';
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to analyze: $e';
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
    
    // Reinitialize if user configured keys
    if (result == true || mounted) {
      setState(() {
        _isInitialized = false;
        _error = '';
        _result = '';
      });
      await _initializeLangChain();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Analysis'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            onPressed: _navigateToSettings,
            icon: const Icon(Icons.settings),
            tooltip: 'API Settings',
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
              // Setup Warning (if not initialized)
              if (!_isInitialized && _error.contains('No API key'))
                Card(
                  color: Colors.orange.shade50,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.warning, color: Colors.orange),
                            const SizedBox(width: 8),
                            Text(
                              'Setup Required',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                color: Colors.orange,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'To use AI analysis, you need to configure your API keys. '
                          'Tap the settings icon above to get started.',
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton.icon(
                          onPressed: _navigateToSettings,
                          icon: const Icon(Icons.settings),
                          label: const Text('Configure API Keys'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.orange,
                            foregroundColor: Colors.white,
                          ),
                        ),
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
                if (_error.isNotEmpty && !_error.contains('No API key'))
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
                            const Icon(Icons.smart_toy, color: Colors.green, size: 20),
                            const SizedBox(width: 8),
                            Text(
                              'Multi-Agent Trading Analysis',
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
            ],
          ),
        ),
      ),
    );
  }
}
