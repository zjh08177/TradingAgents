import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:trading_dummy/jobs/application/use_cases/queue_analysis_use_case.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/smart_polling_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/infrastructure/services/app_lifecycle_service.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';

@GenerateMocks([
  AnalysisDatabase,
  LangGraphApiService,
  SmartPollingService,
  JobEventBus,
  AppLifecycleService,
])
import 'immediate_history_test.mocks.dart';

void main() {
  group('Immediate History Visibility Test', () {
    late QueueAnalysisUseCase useCase;
    late MockAnalysisDatabase mockDatabase;
    late MockLangGraphApiService mockApiService;
    late MockSmartPollingService mockPollingService;
    late MockJobEventBus mockEventBus;
    
    setUp(() {
      // Clear GetIt instance
      GetIt.instance.reset();
      
      // Create mocks
      mockDatabase = MockAnalysisDatabase();
      mockApiService = MockLangGraphApiService();
      mockPollingService = MockSmartPollingService();
      mockEventBus = MockJobEventBus();
      
      // Create use case with mocks
      useCase = QueueAnalysisUseCase(
        database: mockDatabase,
        apiService: mockApiService,
        pollingService: mockPollingService,
        eventBus: mockEventBus,
      );
    });
    
    test('Should save to database immediately before API call', () async {
      // Arrange
      const ticker = 'AAPL';
      const tradeDate = '2025-08-06';
      
      // Mock database operations
      when(mockDatabase.getAllAnalyses()).thenAnswer((_) async => []);
      when(mockDatabase.saveAnalysis(argThat(isA<AnalysisRecord>()))).thenAnswer((_) async => {});
      
      // Mock API response
      when(mockApiService.startAnalysis(
        ticker: ticker,
        tradeDate: tradeDate,
      )).thenAnswer((_) async => StartAnalysisResponse(
        runId: 'test-run-123',
        threadId: 'test-thread-456',
        status: 'running',
        createdAt: DateTime.now(),
      ));
      
      // Mock polling service
      when(mockPollingService.onAnalysisSubmitted(any(), any()))
          .thenAnswer((_) async => {});
      
      // Mock event bus
      when(mockEventBus.publish(argThat(isA<JobEvent>()))).thenReturn(null);
      
      // Act
      final result = await useCase.execute(ticker, tradeDate);
      
      // Assert - Verify immediate database save happened
      verify(mockDatabase.saveAnalysis(argThat(isA<AnalysisRecord>()))).called(2); // Once for initial save, once for update
      
      // Verify event was published for UI update
      verify(mockEventBus.publish(argThat(isA<JobEvent>()))).called(1);
      
      // Verify API was called after database save
      verify(mockApiService.startAnalysis(
        ticker: ticker,
        tradeDate: tradeDate,
      )).called(1);
      
      // Verify polling started
      verify(mockPollingService.onAnalysisSubmitted(any(), any())).called(1);
      
      // Verify result
      expect(result.ticker, equals(ticker));
      expect(result.tradeDate, equals(tradeDate));
      expect(result.status, isNotNull);
    });
    
    test('Should handle API failure gracefully while keeping local record', () async {
      // Arrange
      const ticker = 'FAIL';
      const tradeDate = '2025-08-06';
      
      // Mock database operations
      when(mockDatabase.getAllAnalyses()).thenAnswer((_) async => []);
      when(mockDatabase.saveAnalysis(argThat(isA<AnalysisRecord>()))).thenAnswer((_) async => {});
      when(mockDatabase.updateStatus(any(), 
        status: anyNamed('status'),
        error: anyNamed('error'),
      )).thenAnswer((_) async => {});
      
      // Mock API failure
      when(mockApiService.startAnalysis(
        ticker: ticker,
        tradeDate: tradeDate,
      )).thenThrow(Exception('API Error'));
      
      // Mock event bus
      when(mockEventBus.publish(argThat(isA<JobEvent>()))).thenReturn(null);
      
      // Act & Assert
      expect(
        () => useCase.execute(ticker, tradeDate),
        throwsA(isA<AnalysisException>()),
      );
      
      // Wait for async operations
      await Future.delayed(Duration(milliseconds: 100));
      
      // Verify database was updated with error status
      verify(mockDatabase.saveAnalysis(argThat(isA<AnalysisRecord>()))).called(1); // Initial save
      verify(mockDatabase.updateStatus(any(), 
        status: 'error',
        error: anyNamed('error'),
      )).called(1);
      
      // Verify event was still published for initial UI update
      verify(mockEventBus.publish(argThat(isA<JobEvent>()))).called(1);
    });
    
    test('Should prevent duplicate pending requests', () async {
      // Arrange
      const ticker = 'DUPL';
      const tradeDate = '2025-08-06';
      
      // Mock existing pending record
      final existingRecord = AnalysisRecord(
        id: 'existing-123',
        ticker: ticker,
        tradeDate: tradeDate,
        status: 'pending',
        createdAt: DateTime.now().subtract(Duration(minutes: 1)),
        updatedAt: DateTime.now().subtract(Duration(minutes: 1)),
      );
      
      when(mockDatabase.getAllAnalyses())
          .thenAnswer((_) async => [existingRecord]);
      
      // Act & Assert
      expect(
        () => useCase.execute(ticker, tradeDate),
        throwsA(isA<DuplicateJobException>()),
      );
      
      // Verify no new database saves were attempted
      verifyNever(mockDatabase.saveAnalysis(argThat(isA<AnalysisRecord>())));
      verifyNever(mockApiService.startAnalysis(ticker: ticker, tradeDate: tradeDate));
    });
  });
}

// Note: StartAnalysisResponse is imported from langgraph_api_service.dart