# LangGraph Direct Integration

This Flutter app directly integrates with the deployed LangGraph instance for trading analysis.

## Architecture

The implementation follows SOLID principles with clean architecture:

```
lib/
├── domain/               # Core business logic
│   ├── entities/        # Business models
│   └── repositories/    # Repository interfaces
├── data/                # Data layer
│   ├── datasources/     # External data sources
│   └── repositories/    # Repository implementations
├── presentation/        # UI layer
│   ├── pages/          # Screen widgets
│   └── widgets/        # Reusable widgets
└── core/               # Shared utilities
    ├── config/         # Configuration
    └── utils/          # Utilities (logging, etc.)
```

## Configuration

1. Copy `.env.example` to `.env`
2. Update the API key in `.env`:
   ```
   LANGSMITH_API_KEY=your-actual-api-key
   ```

## Running the App

```bash
flutter pub get
flutter run
```

## Key Features

- **Direct LangGraph Integration**: Uses `langgraph_client` package
- **Real-time Streaming**: Displays analysis updates as they stream
- **Auto-search**: Automatically searches for "ETH" after 2 seconds
- **Comprehensive Logging**: All API interactions are logged
- **Clean Architecture**: Follows SOLID principles

## API Configuration

- **LangGraph URL**: https://tradingdummy2-1b191fa821f85a9e81e0f1d2255177ac.us.langgraph.app
- **Assistant ID**: agent
- **Stream Mode**: updates

## Development

The app includes comprehensive logging for debugging:
- All API calls are logged with timestamps
- Response data is formatted for readability
- Errors are clearly marked and logged

To view logs, run the app in debug mode and check the console output.