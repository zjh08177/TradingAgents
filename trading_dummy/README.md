# Trading Dummy - LangChain.dart Starter App

A minimal Flutter application demonstrating **LangChain.dart** integration for AI-powered trading analysis with **secure API key management**.

## 🔒 **Secure API Key Management**

This app implements app-store-compliant API key handling:

- **🔐 Secure Storage**: API keys stored securely on device using `flutter_secure_storage`
- **📱 User-Provided**: Users input their own API keys (app store friendly)
- **🚫 No Hardcoded Keys**: No API keys bundled with the app
- **🔧 Development Mode**: Uses `.env` file for development (git-ignored)
- **✅ App Store Ready**: Passes Apple/Google security requirements

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd trading_dummy
flutter pub get
```

### 2. Development Setup (Optional)

Create a `.env` file for development:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
```

**Note**: The `.env` file is automatically ignored by Git for security.

### 3. Run the App

```bash
flutter run
```

### 4. Configure API Keys

#### For Development:
- API keys from `.env` file are automatically loaded in debug mode

#### For Production/Users:
1. Tap the **Settings** icon in the app
2. Enter your API keys
3. Tap **Save & Test** to verify
4. Keys are stored securely on device

## 📦 Dependencies

```yaml
dependencies:
  # LangChain.dart packages
  langchain: ^0.7.8
  langchain_community: ^0.2.0
  langchain_openai: ^0.7.0
  langchain_google: ^0.6.0
  langchain_ollama: ^0.3.3
  
  # Security & Configuration
  flutter_secure_storage: ^9.2.2  # Secure key storage
  flutter_dotenv: ^5.1.0          # Environment files
  http: ^1.1.0
```

## 🎯 Features

### Simple UI
- **Ticker Input**: Enter any stock ticker (e.g., AAPL, GOOGL, TSLA)
- **GO Button**: Tap to analyze the stock
- **Result View**: AI analysis appears below with cute robot icon 🤖
- **Settings Page**: Secure API key configuration

### AI Analysis
- Uses **LangChain.dart** with multiple LLM providers
- Generates trading insights for any ticker
- Custom prompt engineering for financial analysis
- Responses always start with "Hi, I'm Dummy" ✨

### Security Features
- **Secure Storage**: API keys encrypted on device
- **No Network Transmission**: Keys never leave your device
- **User Control**: Users manage their own keys and billing
- **Git Ignored**: Development keys never committed

## 🏗️ Project Structure

```
lib/
├── main.dart                # Main app with secure initialization
├── models/
│   └── trading_data.dart   # Data models for trading
├── pages/
│   └── settings_page.dart  # API key configuration UI
└── services/
    ├── config_service.dart     # Secure configuration management
    └── langchain_service.dart  # LangChain integration
```

## 🔧 Key Components

### ConfigService (`lib/services/config_service.dart`)

Handles secure API key management:

```dart
// Get API key (user storage → .env fallback)
final apiKey = await ConfigService.instance.getOpenAIKey();

// Save user-provided key securely
await ConfigService.instance.saveOpenAIKey(userApiKey);

// Validate key format
bool isValid = ConfigService.instance.isValidOpenAIKey(key);
```

### Settings Page (`lib/pages/settings_page.dart`)

User-friendly API key configuration:
- Provider selection (OpenAI, Google)
- Secure text input with validation
- Save & Test functionality
- Key masking for security
- Clear all keys option

### Main App (`lib/main.dart`)

Handles initialization and user experience:
- Automatic configuration detection
- Setup guidance for new users
- Seamless LangChain integration
- Error handling and retry logic

## 💡 Usage Flow

### First Time Users:
1. **Open App** → See setup warning
2. **Tap Settings** → Configure API keys  
3. **Save & Test** → Verify connection
4. **Start Trading** → Enter tickers and analyze

### Returning Users:
1. **Open App** → Auto-loads saved keys
2. **Enter Ticker** → Immediate analysis
3. **Update Settings** → Change providers anytime

## 🎨 UI Design

- **Setup Guidance**: Clear instructions for new users
- **Progressive Disclosure**: Advanced settings hidden until needed  
- **Security Indicators**: Visual feedback for key status
- **Adaptive Layout**: Responds to content and configuration state
- **Error Recovery**: Helpful error messages with action buttons

## 🔒 Security Implementation

### Development vs Production

| Environment | Key Source | Security Level |
|-------------|------------|----------------|
| **Development** | `.env` file | File-based (Git ignored) |
| **Production** | User input | Device keychain/keystore |
| **App Store** | User-provided | ✅ Compliant |

### Key Protection

```dart
// ✅ GOOD: Secure storage
await FlutterSecureStorage().write(key: 'api_key', value: userKey);

// ❌ BAD: Hardcoded in app
const apiKey = 'sk-hardcoded-key'; // Never do this!

// ✅ GOOD: Environment for development only
if (kDebugMode) {
  final devKey = dotenv.env['OPENAI_API_KEY'];
}
```

### App Store Compliance

- **✅ No bundled API keys**: Keys provided by users
- **✅ Secure storage**: Platform keychain/keystore
- **✅ User control**: Users manage their own billing
- **✅ Transparency**: Clear explanation of key usage
- **✅ Deletable**: Users can remove keys anytime

## 🚀 Deployment Guide

### For App Stores:

1. **Remove .env from assets** (production builds)
2. **Test without .env** to ensure user flow works
3. **Include privacy policy** explaining API key usage
4. **Test key validation** and error scenarios
5. **Document user setup** in app store description

### Production Build:

```bash
# Build release APK/IPA without .env dependencies
flutter build apk --release
flutter build ios --release
```

## 🔧 Customization

### Add New LLM Providers

1. **Add dependency** in `pubspec.yaml`
2. **Extend LLMProvider enum** in `langchain_service.dart`
3. **Add validation** in `config_service.dart`
4. **Update settings UI** in `settings_page.dart`

### Custom Key Validation

```dart
bool isValidCustomKey(String key) {
  return key.startsWith('custom-') && 
         key.length > 20 && 
         RegExp(r'^[a-zA-Z0-9-]+$').hasMatch(key);
}
```

## 📚 API Key Sources

### OpenAI
- **Get Key**: [platform.openai.com](https://platform.openai.com/)
- **Format**: `sk-...` (starts with "sk-")
- **Models**: GPT-3.5, GPT-4, GPT-4 Turbo

### Google AI (Gemini)
- **Get Key**: [aistudio.google.com](https://aistudio.google.com/)
- **Format**: Alphanumeric string
- **Models**: Gemini Pro, Gemini Pro Vision

### Local Ollama
- **Setup**: Install Ollama locally
- **URL**: `http://localhost:11434`
- **Models**: Llama 2, Mistral, CodeLlama, etc.

## 🧪 Testing

### Test Scenarios:

1. **First Launch**: No keys configured
2. **Valid Keys**: Successful analysis
3. **Invalid Keys**: Proper error handling
4. **Network Issues**: Graceful degradation
5. **Key Rotation**: Update existing keys

### Security Tests:

1. **Key Storage**: Verify secure storage usage
2. **Key Masking**: Ensure keys are hidden in UI
3. **Memory Safety**: Keys not logged or cached
4. **Git Safety**: `.env` properly ignored

## 🐛 Troubleshooting

### Common Issues:

#### "No API key found"
- **Solution**: Configure keys in Settings page
- **Check**: Settings icon in app bar

#### "Invalid API key format"
- **OpenAI**: Must start with `sk-`
- **Google**: Check for extra spaces or characters

#### ".env file not found" (Development)
- **Solution**: Copy `.env.example` to `.env`
- **Check**: File is in project root

#### "Failed to save API key"
- **Solution**: Check device storage permissions
- **iOS**: Keychain access enabled
- **Android**: Device encryption enabled

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. **Never commit real API keys**
4. Test with both development and production flows
5. Update documentation
6. Submit pull request

## 📝 License

This project is licensed under the MIT License.

---

**🔒 Built with security first using Flutter and LangChain.dart**
