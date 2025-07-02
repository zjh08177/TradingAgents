# TradingDummy iOS App - Project Structure

## Overview

The iOS app is now organized following MVVM architecture with clear separation of concerns.

## Directory Structure

```
TradingDummy/
├── Configuration/
│   └── AppConfig.swift          # App-wide configuration (API URLs, timeouts)
├── Models/
│   └── AnalysisModels.swift     # Data models (Request/Response)
├── Services/
│   └── TradingAgentsService.swift # API service layer
├── ViewModels/
│   └── TradingAnalysisViewModel.swift # Business logic
├── Views/
│   ├── TradingAnalysisView.swift # Main view
│   ├── AnalysisResultView.swift  # Result display components
│   └── SupportingViews.swift     # Loading, Error, Welcome views
├── TradingDummyApp.swift         # App entry point
└── ContentView.swift             # Original demo view (can be removed)
```

## Architecture

### Models
- `AnalysisRequest`: Request payload for API
- `AnalysisResponse`: Response data structure with all analysis reports

### Services
- `TradingAgentsService`: Singleton service for API communication
- `APIError`: Custom error types for better error handling

### ViewModels
- `TradingAnalysisViewModel`: Manages state and business logic
- Uses `@Published` properties for SwiftUI binding
- Handles async API calls with proper error handling

### Views
- `TradingAnalysisView`: Main screen with ticker input
- `AnalysisResultView`: Displays analysis results with expandable cards
- Supporting views for different states (loading, error, welcome)

## Configuration

### Development
- API URL: `http://localhost:8000`
- Timeout: 60 seconds

### Production
- Update `AppConfig.swift` with your production URL
- Build with Release configuration

## Usage

1. Open `TradingDummy.xcodeproj` in Xcode
2. Build and run (⌘+R)
3. The app uses Xcode 16's file system synchronized groups - all Swift files are automatically included

## Testing

1. Ensure backend is running: `cd backend && uv run python3 run_api.py`
2. Run the app in simulator
3. Enter a ticker symbol and tap "Analyze"

## Notes

- All files in subdirectories are automatically included by Xcode 16
- No need to manually add files to the project
- The modular structure makes it easy to add new features or modify existing ones 