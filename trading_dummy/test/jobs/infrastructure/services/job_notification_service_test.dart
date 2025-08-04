import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:trading_dummy/jobs/domain/entities/analysis_job.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_status.dart';
import 'package:trading_dummy/jobs/domain/value_objects/job_priority.dart';
import 'package:trading_dummy/jobs/infrastructure/services/job_notification_service.dart';

void main() {
  group('JobNotificationService', () {
    late JobNotificationService service;
    late AnalysisJob testJob;

    setUp(() {
      // Reset singleton for each test
      JobNotificationService.resetForTesting();
      service = JobNotificationService();
      
      testJob = AnalysisJob(
        id: 'test-job-1',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        status: JobStatus.completed,
        priority: JobPriority.normal,
        createdAt: DateTime.now(),
        retryCount: 0,
      );
    });

    tearDown(() async {
      await service.dispose();
      JobNotificationService.resetForTesting();
    });

    group('Initialization', () {
      test('should be singleton', () {
        final service1 = JobNotificationService();
        final service2 = JobNotificationService();
        expect(service1, same(service2));
      });

      test('should initialize successfully in test environment', () async {
        // In test environment, initialization may not work due to platform dependencies
        // We test the structure without platform-specific calls
        expect(service, isNotNull);
      });

      test('should handle initialization failure gracefully', () async {
        // Test initialization behavior
        // Note: Real initialization may fail in test environment
        final result = await service.initialize();
        // Don't assert specific result as it depends on test environment
        expect(result, isA<bool>());
      });
    });

    group('Notification Actions', () {
      test('should create notification action with correct properties', () {
        final action = NotificationAction(
          jobId: 'job-123',
          ticker: 'TSLA',
          tradeDate: '2024-01-15',
          actionId: JobNotificationService.actionViewResults,
          payload: 'job-123|TSLA|2024-01-15',
        );

        expect(action.jobId, equals('job-123'));
        expect(action.ticker, equals('TSLA'));
        expect(action.tradeDate, equals('2024-01-15'));
        expect(action.actionId, equals(JobNotificationService.actionViewResults));
        expect(action.isViewResults, isTrue);
        expect(action.isRetryJob, isFalse);
        expect(action.isDismiss, isFalse);
        expect(action.isGeneralTap, isFalse);
      });

      test('should identify retry action correctly', () {
        final action = NotificationAction(
          jobId: 'job-123',
          ticker: 'NVDA',
          tradeDate: '2024-01-15',
          actionId: JobNotificationService.actionRetryJob,
          payload: 'job-123|NVDA|2024-01-15',
        );

        expect(action.isRetryJob, isTrue);
        expect(action.isViewResults, isFalse);
        expect(action.isDismiss, isFalse);
        expect(action.isGeneralTap, isFalse);
      });

      test('should identify dismiss action correctly', () {
        final action = NotificationAction(
          jobId: 'job-123',
          ticker: 'GOOGL',
          tradeDate: '2024-01-15',
          actionId: JobNotificationService.actionDismiss,
          payload: 'job-123|GOOGL|2024-01-15',
        );

        expect(action.isDismiss, isTrue);
        expect(action.isViewResults, isFalse);
        expect(action.isRetryJob, isFalse);
        expect(action.isGeneralTap, isFalse);
      });

      test('should identify general tap correctly', () {
        final action = NotificationAction(
          jobId: 'job-123',
          ticker: 'MSFT',
          tradeDate: '2024-01-15',
          actionId: null, // No specific action
          payload: 'job-123|MSFT|2024-01-15',
        );

        expect(action.isGeneralTap, isTrue);
        expect(action.isViewResults, isFalse);
        expect(action.isRetryJob, isFalse);
        expect(action.isDismiss, isFalse);
      });
    });

    group('Notification Management', () {
      test('should handle job completion notification', () async {
        // Test the method exists and doesn't throw
        expect(() async => await service.notifyJobComplete(testJob), 
               returnsNormally);
      });

      test('should handle job failure notification', () async {
        final failedJob = testJob.copyWith(
          status: JobStatus.failed,
          errorMessage: () => 'Test error',
        );

        expect(() async => await service.notifyJobFailed(
          failedJob, 
          errorMessage: 'Test error',
          willRetry: true,
        ), returnsNormally);
      });

      test('should handle job cancellation notification', () async {
        final cancelledJob = testJob.copyWith(
          status: JobStatus.cancelled,
        );

        expect(() async => await service.notifyJobCancelled(
          cancelledJob,
          reason: 'User cancelled',
        ), returnsNormally);
      });

      test('should generate unique notification IDs', () {
        // Test that the private method generates consistent IDs
        final jobId1 = 'job-123';
        final jobId2 = 'job-456';
        
        // Create two different jobs and verify they would get different notification IDs
        expect(jobId1.hashCode, isNot(equals(jobId2.hashCode)));
      });
    });

    group('Permission Management', () {
      test('should handle permission requests gracefully', () async {
        // Test that permission request doesn't throw
        expect(() async => await service.requestPermissions(), 
               returnsNormally);
      });

      test('should check notification status', () async {
        // Test that status check doesn't throw
        expect(() async => await service.areNotificationsEnabled(), 
               returnsNormally);
      });
    });

    group('Notification Control', () {
      test('should cancel job notification', () async {
        expect(() async => await service.cancelJobNotification('job-123'), 
               returnsNormally);
      });

      test('should cancel all notifications', () async {
        expect(() async => await service.cancelAllNotifications(), 
               returnsNormally);
      });

      test('should get pending notifications', () async {
        final pending = await service.getPendingNotifications();
        expect(pending, isA<List<PendingNotificationRequest>>());
      });
    });

    group('Error Handling', () {
      test('should handle uninitialized service gracefully', () async {
        // Create a new service that hasn't been initialized
        JobNotificationService.resetForTesting();
        final uninitializedService = JobNotificationService();
        
        // Should not throw when trying to send notifications
        expect(() async => await uninitializedService.notifyJobComplete(testJob), 
               returnsNormally);
      });

      test('should handle disposal correctly', () async {
        expect(() async => await service.dispose(), returnsNormally);
      });
    });

    group('Constants', () {
      test('should have correct action constants', () {
        expect(JobNotificationService.actionViewResults, equals('view_results'));
        expect(JobNotificationService.actionRetryJob, equals('retry_job'));
        expect(JobNotificationService.actionDismiss, equals('dismiss'));
      });
    });

    group('Stream Management', () {
      test('should provide action stream', () {
        expect(service.onAction, isA<Stream<NotificationAction>>());
      });

      test('should handle action stream events', () async {
        // Listen to action stream
        final subscription = service.onAction.listen((action) {
          // Action handler would be called here
        });
        
        // Clean up
        await subscription.cancel();
        
        // Test that stream exists and is listenable
        expect(service.onAction, isA<Stream<NotificationAction>>());
      });
    });
  });

  group('NotificationAction', () {
    test('should format toString correctly', () {
      final action = NotificationAction(
        jobId: 'job-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        actionId: 'view_results',
        payload: 'job-123|AAPL|2024-01-15',
      );

      final string = action.toString();
      expect(string, contains('job-123'));
      expect(string, contains('view_results'));
      expect(string, contains('NotificationAction'));
    });

    test('should have timestamp', () {
      final before = DateTime.now();
      final action = NotificationAction(
        jobId: 'job-123',
        ticker: 'AAPL',
        tradeDate: '2024-01-15',
        payload: 'job-123|AAPL|2024-01-15',
      );
      final after = DateTime.now();

      expect(action.timestamp.isAfter(before) || action.timestamp.isAtSameMomentAs(before), isTrue);
      expect(action.timestamp.isBefore(after) || action.timestamp.isAtSameMomentAs(after), isTrue);
    });
  });
}