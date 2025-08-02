#!/bin/bash

echo "🧪 Wave 2 Verification Script"
echo "============================"
echo ""

echo "📊 Checking file structure..."
if [ -d "lib/history/infrastructure" ]; then
  echo "✅ Infrastructure layer created"
  ls -la lib/history/infrastructure/
else
  echo "❌ Infrastructure layer missing"
fi

echo ""
echo "🔍 Checking for key files..."
files=(
  "lib/history/infrastructure/mappers/report_mapper.dart"
  "lib/history/infrastructure/repositories/mock_history_repository.dart"
  "lib/screens/test_history_screen.dart"
  "test/test_wave2_integration.dart"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file exists"
  else
    echo "❌ $file missing"
  fi
done

echo ""
echo "🧪 Running unit tests..."
flutter test test/test_wave2_integration.dart

echo ""
echo "📱 Instructions to test in app:"
echo "1. Run: flutter run"
echo "2. Login to the app"
echo "3. Look for 'Development Testing' section at the bottom"
echo "4. Tap 'Test History (Wave 2)' button"
echo "5. Test the following:"
echo "   - View 3 mock entries (AAPL, GOOGL, MSFT)"
echo "   - Tap 'Test Mapper' to add a TSLA entry"
echo "   - Tap 'Test Error' to test error handling"
echo "   - Tap any entry to see details"
echo ""
echo "✅ Wave 2 verification complete!"