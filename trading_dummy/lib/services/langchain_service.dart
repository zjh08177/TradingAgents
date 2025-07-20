import 'package:langchain/langchain.dart';
import 'package:langchain_openai/langchain_openai.dart';
import 'package:langchain_google/langchain_google.dart';
import 'package:langchain_ollama/langchain_ollama.dart';

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
        _chatModel = ChatOpenAI(
          apiKey: apiKey ?? '',
          defaultOptions: ChatOpenAIOptions(
            model: model ?? 'gpt-3.5-turbo',
            temperature: 0.7,
          ),
        );
        break;
        
      case LLMProvider.google:
        _chatModel = ChatGoogleGenerativeAI(
          apiKey: apiKey ?? '',
          defaultOptions: ChatGoogleGenerativeAIOptions(
            model: model ?? 'gemini-pro',
            temperature: 0.7,
          ),
        );
        break;
        
      case LLMProvider.ollama:
        _chatModel = ChatOllama(
          baseUrl: baseUrl ?? 'http://localhost:11434',
          defaultOptions: ChatOllamaOptions(
            model: model ?? 'llama2',
            temperature: 0.7,
          ),
        );
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

  // Dispose resources
  void dispose() {
    _chatModel = null;
    _instance = null;
  }
} 