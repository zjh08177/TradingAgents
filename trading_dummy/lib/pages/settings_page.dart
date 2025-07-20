import 'package:flutter/material.dart';
import '../services/config_service.dart';
import '../services/langchain_service.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final ConfigService _configService = ConfigService.instance;
  final LangChainService _langChainService = LangChainService.instance;
  
  final TextEditingController _openaiController = TextEditingController();
  final TextEditingController _googleController = TextEditingController();
  
  bool _isLoading = false;
  String _message = '';
  LLMProvider _selectedProvider = LLMProvider.openai;

  @override
  void initState() {
    super.initState();
    _loadExistingKeys();
  }

  @override
  void dispose() {
    _openaiController.dispose();
    _googleController.dispose();
    super.dispose();
  }

  Future<void> _loadExistingKeys() async {
    try {
      final openaiKey = await _configService.getOpenAIKey();
      final googleKey = await _configService.getGoogleKey();
      
      if (openaiKey != null) {
        _openaiController.text = '${openaiKey.substring(0, 7)}...${openaiKey.substring(openaiKey.length - 4)}';
      }
      if (googleKey != null) {
        _googleController.text = '${googleKey.substring(0, 7)}...${googleKey.substring(googleKey.length - 4)}';
      }
    } catch (e) {
      // Error loading keys - this is fine, user can enter new ones
    }
  }

  Future<void> _saveAndTestKeys() async {
    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      String? keyToTest;
      
      // Save OpenAI key if provided
      if (_openaiController.text.isNotEmpty && !_openaiController.text.contains('...')) {
        if (!_configService.isValidOpenAIKey(_openaiController.text)) {
          throw Exception('Invalid OpenAI API key format. Should start with "sk-"');
        }
        await _configService.saveOpenAIKey(_openaiController.text);
        if (_selectedProvider == LLMProvider.openai) {
          keyToTest = _openaiController.text;
        }
      }

      // Save Google key if provided
      if (_googleController.text.isNotEmpty && !_googleController.text.contains('...')) {
        if (!_configService.isValidGoogleKey(_googleController.text)) {
          throw Exception('Invalid Google API key format');
        }
        await _configService.saveGoogleKey(_googleController.text);
        if (_selectedProvider == LLMProvider.google) {
          keyToTest = _googleController.text;
        }
      }

      // Test the key with LangChain
      if (keyToTest != null) {
        await _langChainService.initialize(
          provider: _selectedProvider,
          apiKey: keyToTest,
        );
        
        // Test with a simple query
        final testResult = await _langChainService.generateTradingInsight(
          'Test data: AAPL, Price: \$150.00'
        );
        
        if (testResult.isNotEmpty) {
          setState(() {
            _message = '✅ API key saved and tested successfully!';
          });
        }
      } else {
        setState(() {
          _message = '✅ Settings saved successfully!';
        });
      }

      // Reload masked keys
      await _loadExistingKeys();
      
    } catch (e) {
      setState(() {
        _message = '❌ Error: ${e.toString()}';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _clearAllKeys() async {
    await _configService.clearAllKeys();
    _openaiController.clear();
    _googleController.clear();
    setState(() {
      _message = '🗑️ All API keys cleared';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('API Settings'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
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
              // Information Card
              Card(
                color: Colors.blue.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.info, color: Colors.blue),
                          const SizedBox(width: 8),
                          Text(
                            'About API Keys',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              color: Colors.blue,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '• API keys are stored securely on your device\n'
                        '• Keys are never shared or transmitted to third parties\n'
                        '• You maintain full control of your API usage and billing\n'
                        '• Keys can be deleted at any time',
                        style: TextStyle(fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Provider Selection
              Text(
                'Select AI Provider',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<LLMProvider>(
                value: _selectedProvider,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.psychology),
                ),
                onChanged: (value) {
                  setState(() {
                    _selectedProvider = value!;
                  });
                },
                items: LLMProvider.values.map((provider) {
                  return DropdownMenuItem(
                    value: provider,
                    child: Text(provider.name.toUpperCase()),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),

              // OpenAI API Key
              Text(
                'OpenAI API Key',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _openaiController,
                decoration: const InputDecoration(
                  hintText: 'sk-your-openai-api-key-here',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.key),
                  helperText: 'Get your key from platform.openai.com',
                ),
                obscureText: true,
                textInputAction: TextInputAction.next,
                onEditingComplete: () {
                  // Move focus to next field or dismiss keyboard
                  FocusScope.of(context).nextFocus();
                },
              ),
              const SizedBox(height: 16),

              // Google API Key
              Text(
                'Google AI API Key',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _googleController,
                decoration: const InputDecoration(
                  hintText: 'your-google-ai-api-key-here',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.key),
                  helperText: 'Get your key from aistudio.google.com',
                ),
                obscureText: true,
                textInputAction: TextInputAction.done,
                onEditingComplete: () {
                  // Dismiss keyboard when Done button is pressed
                  FocusScope.of(context).unfocus();
                },
                onSubmitted: (_) {
                  // Dismiss keyboard and trigger save
                  FocusScope.of(context).unfocus();
                  _saveAndTestKeys();
                },
              ),
              const SizedBox(height: 24),

              // Action Buttons
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : () {
                        // Dismiss keyboard before saving
                        FocusScope.of(context).unfocus();
                        _saveAndTestKeys();
                      },
                      icon: _isLoading 
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save),
                      label: Text(_isLoading ? 'Testing...' : 'Save & Test'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Theme.of(context).colorScheme.primary,
                        foregroundColor: Theme.of(context).colorScheme.onPrimary,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: () {
                      // Dismiss keyboard before clearing
                      FocusScope.of(context).unfocus();
                      _clearAllKeys();
                    },
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Clear'),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Message Display
              if (_message.isNotEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12.0),
                  decoration: BoxDecoration(
                    color: _message.startsWith('✅') 
                        ? Colors.green.shade50 
                        : _message.startsWith('❌')
                            ? Colors.red.shade50
                            : Colors.grey.shade50,
                    border: Border.all(
                      color: _message.startsWith('✅') 
                          ? Colors.green.shade200 
                          : _message.startsWith('❌')
                              ? Colors.red.shade200
                              : Colors.grey.shade200,
                    ),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _message,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
} 