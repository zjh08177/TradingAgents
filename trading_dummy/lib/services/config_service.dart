import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ConfigService {
  static ConfigService? _instance;
  static ConfigService get instance => _instance ??= ConfigService._();
  
  ConfigService._();

  static const _storage = FlutterSecureStorage();
  
  // Storage keys
  static const String _openaiKeyStorage = 'openai_api_key';
  static const String _googleKeyStorage = 'google_api_key';
  static const String _anthropicKeyStorage = 'anthropic_api_key';

  // Initialize the service
  Future<void> initialize() async {
    try {
      // Only load .env in development/debug mode
      if (kDebugMode) {
        await dotenv.load(fileName: ".env");
      }
    } catch (e) {
      // .env file not found or couldn't be loaded - this is fine for production
      debugPrint('Could not load .env file: $e');
    }
  }

  // Get OpenAI API Key
  Future<String?> getOpenAIKey() async {
    try {
      // First try to get from secure storage (user-provided)
      String? userKey = await _storage.read(key: _openaiKeyStorage);
      if (userKey != null && userKey.isNotEmpty) {
        return userKey;
      }

      // In debug mode, fallback to .env file
      if (kDebugMode) {
        try {
          String? envKey = dotenv.env['OPENAI_API_KEY'];
          if (envKey != null && envKey != 'your-openai-api-key-here') {
            return envKey;
          }
        } catch (e) {
          // .env not loaded or key not found - this is fine
        }
      }

      return null;
    } catch (e) {
      debugPrint('Error getting OpenAI key: $e');
      return null;
    }
  }

  // Save OpenAI API Key (user-provided)
  Future<void> saveOpenAIKey(String key) async {
    try {
      await _storage.write(key: _openaiKeyStorage, value: key);
    } catch (e) {
      debugPrint('Error saving OpenAI key: $e');
      throw Exception('Failed to save API key securely');
    }
  }

  // Get Google API Key
  Future<String?> getGoogleKey() async {
    try {
      String? userKey = await _storage.read(key: _googleKeyStorage);
      if (userKey != null && userKey.isNotEmpty) {
        return userKey;
      }

      if (kDebugMode) {
        try {
          String? envKey = dotenv.env['GOOGLE_API_KEY'];
          if (envKey != null && envKey != 'your-google-api-key-here') {
            return envKey;
          }
        } catch (e) {
          // .env not loaded or key not found - this is fine
        }
      }

      return null;
    } catch (e) {
      debugPrint('Error getting Google key: $e');
      return null;
    }
  }

  // Save Google API Key
  Future<void> saveGoogleKey(String key) async {
    try {
      await _storage.write(key: _googleKeyStorage, value: key);
    } catch (e) {
      debugPrint('Error saving Google key: $e');
      throw Exception('Failed to save API key securely');
    }
  }

  // Check if any API key is available
  Future<bool> hasValidApiKey() async {
    final openaiKey = await getOpenAIKey();
    final googleKey = await getGoogleKey();
    return (openaiKey != null && openaiKey.isNotEmpty) || 
           (googleKey != null && googleKey.isNotEmpty);
  }

  // Clear all stored keys (for logout/reset)
  Future<void> clearAllKeys() async {
    try {
      await _storage.delete(key: _openaiKeyStorage);
      await _storage.delete(key: _googleKeyStorage);
      await _storage.delete(key: _anthropicKeyStorage);
    } catch (e) {
      debugPrint('Error clearing keys: $e');
    }
  }

  // Validate API key format
  bool isValidOpenAIKey(String key) {
    return key.startsWith('sk-') && key.length > 20;
  }

  bool isValidGoogleKey(String key) {
    return key.length > 10 && !key.contains(' ');
  }
} 