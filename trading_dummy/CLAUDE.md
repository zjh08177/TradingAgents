# Claude Code Configuration - Trading Dummy Project

## 🚨 CRITICAL: Test Verification Requirement

**MANDATORY**: Always run any test files you create or modify to ensure they pass!

### Test Workflow
1. **Create/Modify Test**: Write or update test files
2. **Run Test Immediately**: Execute `flutter test <test_file_path>` 
3. **Fix Any Failures**: Debug and fix issues before marking complete
4. **Verify Success**: Ensure all tests pass before proceeding

### Common Test Issues & Solutions

#### Hive Tests
- **Issue**: `MissingPluginException` with `Hive.initFlutter()`
- **Solution**: Use `Hive.init(tempDir.path)` with `Directory.systemTemp.createTemp()` for unit tests

Example:
```dart
setUpAll(() async {
  final tempDir = await Directory.systemTemp.createTemp('hive_test_');
  Hive.init(tempDir.path);
  // Register adapters and open boxes
});
```

## Project-Specific Guidelines

### History Feature Implementation
- Use clean architecture: Domain → Application → Infrastructure → Presentation
- Maintain separation between domain entities and Hive models
- Always test repository implementations with integration tests
- Run `flutter pub run build_runner build` after modifying Hive models

### Testing Best Practices
1. **Unit Tests**: Test individual components in isolation
2. **Widget Tests**: Test UI components with proper Material app wrapper
3. **Integration Tests**: Test repositories and services with real implementations
4. **Always Clean Up**: Close Hive boxes and clean temp directories in tearDown

### Flutter Commands
- `flutter test` - Run all tests
- `flutter test <file>` - Run specific test file
- `flutter analyze` - Check for code issues
- `flutter pub run build_runner build --delete-conflicting-outputs` - Generate code

## Important Notes
- Always verify tests pass before marking tasks complete
- Check for analyzer warnings after code generation
- Use proper error handling in repository implementations
- Maintain consistent code style across the project