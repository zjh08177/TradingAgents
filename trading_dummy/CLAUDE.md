# Claude Code Configuration - Trading Dummy Project

## 🚨 CRITICAL: Test Verification Requirement

**MANDATORY**: Always run any test files you create or modify to ensure they pass!

### Test Workflow
1. **Create/Modify Test**: Write or update test files
2. **Run Test Immediately**: Execute `flutter test <test_file_path>` 
3. **Fix Any Failures**: Debug and fix issues before marking complete
4. **Verify Success**: Ensure all tests pass before proceeding

### 🔴 Rigid Test Validation Policy
**Claude MUST follow test plans rigidly:**
- Execute EVERY test command in documentation
- Verify ALL checklist items pass
- Fix failing tests immediately
- Continue until 100% tests pass
- NO shortcuts or exceptions allowed

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

## Phase Documentation Requirements

### 🚨 MANDATORY: Test Plans in Phase Summary Documents

**Every phase completion summary MUST include a comprehensive "Test Plans and Verification" section with:**

### 🔴 CRITICAL: Rigid Test Validation Requirement

**Claude MUST rigidly follow all test plans and perform ALL validation steps:**
- Run every test command listed in the test plan
- Verify all checklist items are passing
- Fix any failing tests before marking phase complete
- Continue working until 100% of tests pass
- No exceptions or shortcuts allowed

1. **Unit Test Verification**
   - List all test files for the phase
   - Provide exact commands to run tests
   - Specify what each test verifies
   - Include expected test counts and coverage

2. **In-App Manual Testing**
   - Provide code snippets for manual verification
   - Include debug screens or test utilities
   - Show how to verify key functionality
   - Document expected behaviors

3. **Automated Test Suite**
   - Commands to run full test suite
   - Coverage report generation
   - Performance benchmarks
   - Integration test scenarios

4. **Verification Checklist**
   - Itemized list of all verification points
   - Pass/fail criteria for each item
   - Performance targets and thresholds
   - Error handling scenarios

**Example Structure**:
```markdown
## Test Plans and Verification

### Unit Test Verification
#### 1. Component Name
**Test Files**: `test/path/to/test.dart`
**How to Run**: `flutter test test/path/to/test.dart`
**What to Verify**: [specific verification points]

### In-App Manual Testing
#### 1. Feature Testing
```dart
// Code snippet for manual testing
```

### Automated Test Suite
```bash
# Commands to run tests
flutter test test/feature/
```

### Checklist for Phase X Verification
- [ ] All unit tests pass (X tests)
- [ ] Performance targets met (<Xms)
- [ ] Error scenarios handled
```

## Important Notes
- Always verify tests pass before marking tasks complete
- Check for analyzer warnings after code generation
- Use proper error handling in repository implementations
- Maintain consistent code style across the project
- Include comprehensive test plans in all phase documentation