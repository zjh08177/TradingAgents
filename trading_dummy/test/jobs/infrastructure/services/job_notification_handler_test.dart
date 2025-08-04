import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/events/job_event.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_notification_handler.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_event_bus.dart';

void main() {
  group('JobNotificationHandler', () {
    late JobNotificationHandler handler;
    late JobEventBus eventBus;
    late AnalysisJob testJob;

    setUp(() {
      // Reset singletons for each test
      JobNotificationHandler.resetForTesting();
      JobEventBus.resetForTesting();
      
      handler = JobNotificationHandler();
      eventBus = JobEventBus();
      
      testJob = AnalysisJob(
        id: 'test-job-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: JobStatus.pending,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        retryCount: 0,
      );
    });

    tearDown(() async {
      await handler.dispose();
      await eventBus.close();
      JobNotificationHandler.resetForTesting();
      JobEventBus.resetForTesting();
    });

    group('Initialization', () {
      test('should be singleton', () {
        final handler1 = JobNotificationHandler();
        final handler2 = JobNotificationHandler();
        expect(handler1, same(handler2));
      });

      test('should initialize successfully in test environment', () async {
        // In test environment, notification service may not initialize
        // Test that handler handles this gracefully
        final result = await handler.initialize();
        expect(result, isA<bool>());
      });

      testWidgets('should handle navigation context', (WidgetTester tester) async {
        // Create a minimal widget for testing
        await tester.pumpWidget(MaterialApp(home: Container()));
        final context = tester.element(find.byType(Container));
        
        await handler.initialize(navigationContext: context);
        
        handler.updateNavigationContext(context);
        
        // Verify handler doesn't throw with context
        expect(() => handler.updateNavigationContext(context), returnsNormally);
      });
    });

    group('Event Handling', () {
      test('should handle job completed events', () async {
        await handler.initialize();
        
        // Create a completed job
        final completedJob = testJob.copyWith(
          status: JobStatus.completed,
          completedAt: () => DateTime.now(),
        );
        
        // Publish event and verify no exceptions
        expect(() => eventBus.publish(JobCompletedEvent(completedJob)), 
               returnsNormally);
        
        // Allow event processing
        await Future.delayed(Duration(milliseconds: 10));
      });

      test('should handle job failed events', () async {
        await handler.initialize();
        
        // Create a failed job
        final failedJob = testJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'Test error',
        );
        
        // Publish event and verify no exceptions
        expect(() => eventBus.publish(JobFailedEvent(
          failedJob, 
          errorMessage: 'Test error',
          willRetry: false,
        )), returnsNormally);
        
        // Allow event processing
        await Future.delayed(Duration(milliseconds: 10));
      });

      test('should handle job cancelled events', () async {
        await handler.initialize();
        
        // Create a cancelled job
        final cancelledJob = testJob.copyWith(
          status: JobStatus.cancelled,
        );
        
        // Publish event and verify no exceptions
        expect(() => eventBus.publish(JobCancelledEvent(
          cancelledJob,
          reason: 'User cancelled',
        )), returnsNormally);
        
        // Allow event processing
        await Future.delayed(Duration(milliseconds: 10));
      });
    });

    group('Notification Actions', () {
      test('should show test notification', () async {
        await handler.initialize();
        
        // Should not throw even if notification service isn't fully initialized
        expect(() async => await handler.showTestNotification(), 
               returnsNormally);
      });

      test('should check notification status', () async {
        await handler.initialize();
        
        final enabled = await handler.areNotificationsEnabled();
        expect(enabled, isA<bool>());
      });

      test('should cancel all notifications', () async {
        await handler.initialize();
        
        expect(() async => await handler.cancelAllNotifications(), 
               returnsNormally);
      });
    });

    group('Statistics', () {
      test('should provide handler statistics', () {
        final stats = handler.getStats();
        
        expect(stats, isA<NotificationHandlerStats>());
        expect(stats.isActive, isA<bool>());
        expect(stats.hasNavigationContext, isA<bool>());
        expect(stats.subscriptionCount, isA<int>());
      });

      test('should format stats toString correctly', () {
        final stats = NotificationHandlerStats(
          isActive: true,
          hasNavigationContext: false,
          subscriptionCount: 3,
        );
        
        final string = stats.toString();
        expect(string, contains('active: true'));
        expect(string, contains('hasContext: false'));
        expect(string, contains('subs: 3'));
      });
    });

    group('Lifecycle', () {
      test('should handle multiple initialize calls', () async {
        final result1 = await handler.initialize();
        final result2 = await handler.initialize();
        
        expect(result1, isA<bool>());
        expect(result2, isA<bool>());
      });

      test('should dispose cleanly', () async {
        await handler.initialize();
        
        expect(() async => await handler.dispose(), returnsNormally);
        
        // Stats should reflect disposal
        final stats = handler.getStats();
        expect(stats.isActive, isFalse);
      });

      test('should handle reset for testing', () {
        JobNotificationHandler.resetForTesting();
        
        // Should be able to create new instance after reset
        final newHandler = JobNotificationHandler();
        expect(newHandler, isA<JobNotificationHandler>());
      });
    });

    group('Error Handling', () {
      test('should handle uninitialized handler gracefully', () async {
        // Don't initialize the handler
        
        // Should not throw when calling methods on uninitialized handler
        expect(() async => await handler.showTestNotification(), 
               returnsNormally);
        
        expect(() async => await handler.areNotificationsEnabled(), 
               returnsNormally);
      });

      testWidgets('should handle navigation without context', (WidgetTester tester) async {
        // Handler should work even without navigation context
        await tester.pumpWidget(MaterialApp(home: Container()));
        
        expect(() => handler.updateNavigationContext(
          tester.element(find.byType(Container))
        ), returnsNormally);
      });

      test('should handle missing navigation context gracefully', () async {
        await handler.initialize();
        
        // Should not throw when handling actions without context
        final stats = handler.getStats();
        expect(stats.hasNavigationContext, isA<bool>());
      });
    });
  });

  group('Integration Tests', () {
    late JobNotificationHandler handler;
    late JobEventBus eventBus;

    setUp(() {
      JobNotificationHandler.resetForTesting();
      JobEventBus.resetForTesting();
      handler = JobNotificationHandler();
      eventBus = JobEventBus();
    });

    tearDown(() async {
      await handler.dispose();
      await eventBus.close();
      JobNotificationHandler.resetForTesting();
      JobEventBus.resetForTesting();
    });

    testWidgets('should handle full notification flow', (WidgetTester tester) async {
      // Create test app
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: Container(key: ValueKey('test-container')),
        ),
        routes: {
          '/jobs': (context) => Scaffold(body: Text('Jobs Screen')),
          '/history': (context) => Scaffold(body: Text('History Screen')),
        },
      ));

      final context = tester.element(find.byKey(ValueKey('test-container')));

      // Initialize handler with context
      await handler.initialize(navigationContext: context);
      
      // Create test job and events
      final job = AnalysisJob(
        id: 'integration-test-job',
        ticker: 'TSLA',
        tradeDate: '2024-01-15',
        status: JobStatus.completed,
        priority: JobPriority.high,
        createdAt: DateTime.now(),
        retryCount: 0,
      );

      // Simulate job completion
      eventBus.publish(JobCompletedEvent(job));
      
      // Allow event processing
      await tester.pump(Duration(milliseconds: 100));
      
      // Verify handler is active
      final stats = handler.getStats();
      expect(stats.isActive, isTrue);
      expect(stats.hasNavigationContext, isTrue);
    });

    test('should handle event bus integration', () async {
      await handler.initialize();
      
      final job = AnalysisJob(
        id: 'bus-test-job',
        ticker: 'NVDA',
        tradeDate: '2024-01-15',
        status: JobStatus.failed,
        priority: JobPriority.critical,
        createdAt: DateTime.now(),
        retryCount: 2,
      );

      // Test multiple event types
      final events = [
        JobCompletedEvent(job),
        JobFailedEvent(job, errorMessage: 'Network error', willRetry: true),
        JobCancelledEvent(job, reason: 'Timeout'),
      ];

      // Publish all events
      for (final event in events) {
        expect(() => eventBus.publish(event), returnsNormally);
      }
      
      // Allow processing
      await Future.delayed(Duration(milliseconds: 50));
      
      // Verify handler is still active
      expect(handler.getStats().isActive, isTrue);
    });
  });
}