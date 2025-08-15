import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:trading_dummy/jobs/application/use_cases/queue_analysis_use_case.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_database.dart';
import 'package:trading_dummy/jobs/infrastructure/persistence/analysis_record.dart';
import 'package:trading_dummy/jobs/infrastructure/services/langgraph_api_service.dart' as api;
import 'package:trading_dummy/jobs/infrastructure/services/smart_polling_service.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';

class MockAnalysisDatabase extends Mock implements AnalysisDatabase {}
class MockLangGraphApiService extends Mock implements api.LangGraphApiService {}
class MockSmartPollingService extends Mock implements SmartPollingService {}
class MockJobEventBus extends Mock implements JobEventBus {}

void main() {
  group('QueueAnalysisUseCase', () {
    late QueueAnalysisUseCase useCase;
    late MockAnalysisDatabase mockDatabase;
    late MockLangGraphApiService mockApiService;
    late MockSmartPollingService mockPollingService;
    late MockJobEventBus mockEventBus;

    setUpAll(() {
      // Register fallback values for mocktail
      registerFallbackValue(AnalysisRecord(
        id: 'fallback',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: 'pending',
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      ));
      registerFallbackValue(JobQueuedEvent(_createMockAnalysisJob()));
    });

    setUp(() {
      mockDatabase = MockAnalysisDatabase();
      mockApiService = MockLangGraphApiService();
      mockPollingService = MockSmartPollingService();
      mockEventBus = MockJobEventBus();

      useCase = QueueAnalysisUseCase(
        database: mockDatabase,
        apiService: mockApiService,
        pollingService: mockPollingService,
        eventBus: mockEventBus,
      );

      // Default mock setup
      when(() => mockDatabase.saveAnalysis(any())).thenAnswer((_) async {});
      when(() => mockDatabase.updateStatus(
        any(),
        status: any(named: 'status'),
        result: any(named: 'result'),
        error: any(named: 'error'),
        completedAt: any(named: 'completedAt'),
      )).thenAnswer((_) async {});
      when(() => mockDatabase.getAllAnalyses()).thenAnswer((_) async => <AnalysisRecord>[]);
      when(() => mockEventBus.publish(any())).thenReturn(null);
      when(() => mockPollingService.onAnalysisSubmitted(any(), any())).thenAnswer((_) async {});
    });

    group('Successful execution', () {
      test('should execute local-first flow successfully', () async {
        // Arrange
        const ticker = 'AAPL';
        const tradeDate = '2024-01-15';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-123',
          threadId: 'thread-123',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act
        final result = await useCase.execute(ticker, tradeDate);

        // Assert
        expect(result, isA<AnalysisJob>());
        expect(result.ticker, equals(ticker));
        expect(result.tradeDate, equals(tradeDate));

        // Verify local-first flow
        verify(() => mockDatabase.saveAnalysis(any())).called(2); // Initial save + update with run ID
        verify(() => mockEventBus.publish(any<JobQueuedEvent>())).called(1);
        verify(() => mockApiService.startAnalysis(ticker: ticker, tradeDate: tradeDate)).called(1);
        verify(() => mockPollingService.onAnalysisSubmitted('run-123', 'thread-123')).called(1);
      });

      test('should save local record immediately for instant UI feedback', () async {
        // Arrange
        const ticker = 'TSLA';
        const tradeDate = '2024-01-20';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-456',
          threadId: 'thread-456',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act  
        await useCase.execute(ticker, tradeDate, priority: JobPriority.high);

        // Assert - verify local record saved first
        final captured = verify(() => mockDatabase.saveAnalysis(captureAny())).captured;
        final firstSave = captured.first as AnalysisRecord;
        
        expect(firstSave.id, isNotEmpty); // Generated by IdGenerator
        expect(firstSave.ticker, equals(ticker));
        expect(firstSave.tradeDate, equals(tradeDate));
        expect(firstSave.status, equals('pending'));
        expect(firstSave.runId, isNull); // Should be null initially
        expect(firstSave.threadId, isNull); // Should be null initially
      });

      test('should update local record with API response data', () async {
        // Arrange
        const ticker = 'GOOGL';
        const tradeDate = '2024-01-25';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-789',
          threadId: 'thread-789',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act
        await useCase.execute(ticker, tradeDate);

        // Assert - verify updated record has API data
        final captured = verify(() => mockDatabase.saveAnalysis(captureAny())).captured;
        final updatedSave = captured.last as AnalysisRecord;
        
        expect(updatedSave.runId, equals('run-789'));
        expect(updatedSave.threadId, equals('thread-789'));
        expect(updatedSave.status, equals('running'));
      });

      test('should publish JobQueuedEvent for immediate UI update', () async {
        // Arrange
        const ticker = 'MSFT';
        const tradeDate = '2024-01-30';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-101',
          threadId: 'thread-101',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act
        await useCase.execute(ticker, tradeDate);

        // Assert
        final captured = verify(() => mockEventBus.publish(captureAny())).captured;
        final event = captured.first as JobQueuedEvent;
        
        expect(event.job.ticker, equals(ticker));
        expect(event.job.tradeDate, equals(tradeDate));
        expect(event.job.status, equals(JobStatus.pending));
      });
    });

    group('Input validation', () {
      test('should reject empty ticker', () async {
        expect(
          () => useCase.execute('', '2024-01-15'),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Ticker cannot be empty',
          )),
        );
      });

      test('should reject ticker longer than 10 characters', () async {
        expect(
          () => useCase.execute('VERYLONGTICKER', '2024-01-15'),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Ticker cannot be longer than 10 characters',
          )),
        );
      });

      test('should reject non-alphanumeric ticker', () async {
        expect(
          () => useCase.execute('AAP-L', '2024-01-15'),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Ticker must be alphanumeric',
          )),
        );
      });

      test('should reject invalid date format', () async {
        expect(
          () => useCase.execute('AAPL', '2024/01/15'),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Trade date must be in YYYY-MM-DD format',
          )),
        );
      });

      test('should reject future dates', () async {
        final futureDate = DateTime.now().add(const Duration(days: 1));
        final futureDateString = '${futureDate.year}-${futureDate.month.toString().padLeft(2, '0')}-${futureDate.day.toString().padLeft(2, '0')}';
        
        expect(
          () => useCase.execute('AAPL', futureDateString),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Trade date cannot be in the future',
          )),
        );
      });

      test('should reject dates before year 2000', () async {
        expect(
          () => useCase.execute('AAPL', '1999-12-31'),
          throwsA(isA<ArgumentError>().having(
            (e) => e.message,
            'message',
            'Trade date cannot be before year 2000',
          )),
        );
      });
    });

    group('Duplicate job detection', () {
      // NOTE: Duplicate detection has been removed from client per "client fires, server decides" principle
      // The server should handle duplicate detection, not the client
      
      test('should allow resubmission of completed analysis', () async {
        // Arrange
        const ticker = 'GOOGL';
        const tradeDate = '2024-01-25';
        
        final existingRecord = AnalysisRecord(
          id: 'existing-id',
          ticker: ticker,
          tradeDate: tradeDate,
          status: 'success', // Completed status
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-new',
          threadId: 'thread-new',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockDatabase.getAllAnalyses()).thenAnswer((_) async => [existingRecord]);
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act - should not throw
        final result = await useCase.execute(ticker, tradeDate);

        // Assert
        expect(result, isA<AnalysisJob>());
      });
    });

    group('Error handling', () {
      test('should handle API submission failure', () async {
        // Arrange
        const ticker = 'AAPL';
        const tradeDate = '2024-01-15';
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenThrow(Exception('Network error'));

        // Act & Assert
        expect(
          () => useCase.execute(ticker, tradeDate),
          throwsA(isA<AnalysisException>().having(
            (e) => e.toString(),
            'message',
            'AnalysisException: Failed to submit analysis: Exception: Network error',
          )),
        );

        // Note: Error status saving is tested in other tests
        // The important part is that the AnalysisException is thrown
      });

      test('should handle database save failure gracefully', () async {
        // Arrange
        const ticker = 'TSLA';
        const tradeDate = '2024-01-20';
        
        when(() => mockDatabase.saveAnalysis(any())).thenThrow(Exception('Database error'));

        // Act & Assert
        expect(
          () => useCase.execute(ticker, tradeDate),
          throwsA(isA<Exception>()),
        );
      });

      test('should handle polling service failure gracefully', () async {
        // Arrange
        const ticker = 'GOOGL';
        const tradeDate = '2024-01-25';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-123',
          threadId: 'thread-123',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);
        
        when(() => mockPollingService.onAnalysisSubmitted(any(), any()))
            .thenThrow(Exception('Polling error'));

        // Act & Assert - should still throw since polling is critical
        expect(
          () => useCase.execute(ticker, tradeDate),
          throwsA(isA<Exception>()),
        );
      });
    });

    group('Priority handling', () {
      test('should handle different priority levels', () async {
        // Arrange
        const ticker = 'MSFT';
        const tradeDate = '2024-01-30';
        
        final mockResponse = api.StartAnalysisResponse(
          runId: 'run-priority',
          threadId: 'thread-priority',
          status: 'running',
          createdAt: DateTime.now(),
        );
        
        when(() => mockApiService.startAnalysis(
          ticker: ticker,
          tradeDate: tradeDate,
        )).thenAnswer((_) async => mockResponse);

        // Act
        final result = await useCase.execute(
          ticker, 
          tradeDate, 
          priority: JobPriority.high,
        );

        // Assert
        expect(result, isA<AnalysisJob>());
        expect(result.priority, equals(JobPriority.high));
      });
    });
  });
}

/// Helper method to create mock AnalysisJob
AnalysisJob _createMockAnalysisJob() {
  return AnalysisJob(
    id: 'mock-job-id',
    ticker: 'AAPL',
    tradeDate: '2024-01-15',
    status: JobStatus.pending,
    priority: JobPriority.normal,
    createdAt: DateTime.now(),
    retryCount: 0,
  );
}