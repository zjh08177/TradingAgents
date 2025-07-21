import 'package:langchain/langchain.dart';
import 'package:langchain_openai/langchain_openai.dart';
import 'package:langchain_google/langchain_google.dart';
import 'package:langchain_ollama/langchain_ollama.dart';
import 'logger_service.dart';

enum LLMProvider {
  openai,
  google,
  ollama,
}

class LangChainService {
  static LangChainService? _instance;
  static LangChainService get instance => _instance ??= LangChainService._();
  
  LangChainService._();

  BaseChatModel? _chatModel;
  LLMProvider _currentProvider = LLMProvider.openai;
  String _currentModel = '';
  String _currentProviderName = '';

  // Initialize the service with provider and API key
  Future<void> initialize({
    required LLMProvider provider,
    String? apiKey,
    String? baseUrl,
    String? model,
  }) async {
    _currentProvider = provider;
    
    switch (provider) {
      case LLMProvider.openai:
        final openaiModel = model ?? 'gpt-4o';
        _chatModel = ChatOpenAI(
          apiKey: apiKey ?? '',
          defaultOptions: ChatOpenAIOptions(
            model: openaiModel,
            temperature: 0.7,
          ),
        );
        _currentModel = openaiModel;
        _currentProviderName = 'OpenAI';
        LoggerService.info('llm', 'Initialized OpenAI model: $openaiModel');
        break;
        
      case LLMProvider.google:
        final googleModel = model ?? 'gemini-pro';
        _chatModel = ChatGoogleGenerativeAI(
          apiKey: apiKey ?? '',
          defaultOptions: ChatGoogleGenerativeAIOptions(
            model: googleModel,
            temperature: 0.7,
          ),
        );
        _currentModel = googleModel;
        _currentProviderName = 'Google';
        LoggerService.info('llm', 'Initialized Google model: $googleModel');
        break;
        
      case LLMProvider.ollama:
        final ollamaModel = model ?? 'llama2';
        _chatModel = ChatOllama(
          baseUrl: baseUrl ?? 'http://localhost:11434',
          defaultOptions: ChatOllamaOptions(
            model: ollamaModel,
            temperature: 0.7,
          ),
        );
        _currentModel = ollamaModel;
        _currentProviderName = 'Ollama';
        LoggerService.info('llm', 'Initialized Ollama model: $ollamaModel');
        break;
    }
  }

  // Generate trading insights
  Future<String> generateTradingInsight(String marketData) async {
    if (_chatModel == null) {
      throw Exception('LangChain service not initialized');
    }

    final prompt = '''
    As a financial advisor AI, analyze the following market data and provide trading insights:
    
    Market Data: $marketData
    
    Please provide:
    1. Market trend analysis
    2. Key support/resistance levels
    3. Trading recommendation (buy/sell/hold)
    4. Risk assessment
    Your reply always start with "Hi, I'm Dummy"
    Keep the response concise and actionable.
    ''';

    try {
      final response = await _chatModel!.invoke(
        PromptValue.string(prompt),
      );
      return response.output.content;
    } catch (e) {
      throw Exception('Failed to generate trading insight: $e');
    }
  }

  // Generate market analysis
  Future<String> analyzeMarketSentiment(String newsData) async {
    if (_chatModel == null) {
      throw Exception('LangChain service not initialized');
    }

    final prompt = '''
    Analyze the market sentiment from the following news data:
    
    News: $newsData
    
    Provide:
    1. Overall sentiment (bullish/bearish/neutral)
    2. Key factors influencing sentiment
    3. Potential market impact
    4. Trading implications
    ''';

    try {
      final response = await _chatModel!.invoke(
        PromptValue.string(prompt),
      );
      return response.output.content;
    } catch (e) {
      throw Exception('Failed to analyze market sentiment: $e');
    }
  }

  // Get risk assessment
  Future<String> assessTradingRisk(String portfolioData) async {
    if (_chatModel == null) {
      throw Exception('LangChain service not initialized');
    }

    final prompt = '''
    Perform a risk assessment for the following portfolio:
    
    Portfolio: $portfolioData
    
    Analyze:
    1. Portfolio diversification
    2. Risk concentration
    3. Volatility assessment
    4. Risk mitigation recommendations
    ''';

    try {
      final response = await _chatModel!.invoke(
        PromptValue.string(prompt),
      );
      return response.output.content;
    } catch (e) {
      throw Exception('Failed to assess trading risk: $e');
    }
  }

  // Get current model information
  String get currentModel => _currentModel;
  String get currentProvider => _currentProviderName;
  LLMProvider get currentProviderEnum => _currentProvider;
  
  // Get model status for logging
  String getModelStatus() {
    if (_chatModel == null) {
      return 'No model initialized';
    }
    return '$_currentProviderName: $_currentModel';
  }
  
  // Dispose resources
  void dispose() {
    _chatModel = null;
    _instance = null;
  }
} 