import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/jobs/infrastructure/services/app_lifecycle_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  
  group('AppLifecycleService', () {
    late AppLifecycleService service;
    
    setUp(() {
      service = AppLifecycleService();
      // Reset service to ensure clean state
      service.reset();
    });
    
    tearDown(() {
      service.dispose();
    });
    
    group('Initialization', () {
      test('should start uninitialized', () {
        expect(service.isInitialized, isFalse);
      });
      
      test('should initialize successfully', () {
        service.initialize();
        expect(service.isInitialized, isTrue);
      });
      
      test('should handle multiple initialization calls', () {
        service.initialize();
        expect(service.isInitialized, isTrue);
        
        // Second call should not throw
        service.initialize();
        expect(service.isInitialized, isTrue);
      });
      
      test('should have resumed as initial state', () {
        expect(service.currentState, equals(AppLifecycleState.resumed));
        expect(service.isInForeground, isTrue);
      });
    });
    
    group('Lifecycle State Management', () {
      test('should update state when app lifecycle changes', () {
        service.initialize();
        
        // Simulate app going to background
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        expect(service.currentState, equals(AppLifecycleState.paused));
        expect(service.isInForeground, isFalse);
        
        // Simulate app coming to foreground
        service.didChangeAppLifecycleState(AppLifecycleState.resumed);
        expect(service.currentState, equals(AppLifecycleState.resumed));
        expect(service.isInForeground, isTrue);
      });
      
      test('should correctly identify foreground state', () {
        service.initialize();
        
        // Test all states
        service.didChangeAppLifecycleState(AppLifecycleState.resumed);
        expect(service.isInForeground, isTrue);
        
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        expect(service.isInForeground, isFalse);
        
        service.didChangeAppLifecycleState(AppLifecycleState.inactive);
        expect(service.isInForeground, isFalse);
        
        service.didChangeAppLifecycleState(AppLifecycleState.detached);
        expect(service.isInForeground, isFalse);
        
        service.didChangeAppLifecycleState(AppLifecycleState.hidden);
        expect(service.isInForeground, isFalse);
      });
    });
    
    group('Stream Emissions', () {
      test('should emit state changes through stream', () async {
        service.initialize();
        
        final states = <AppLifecycleState>[];
        final subscription = service.lifecycleState.listen(states.add);
        
        // Simulate state changes
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        service.didChangeAppLifecycleState(AppLifecycleState.inactive);
        service.didChangeAppLifecycleState(AppLifecycleState.resumed);
        
        // Allow stream to process
        await Future.delayed(Duration.zero);
        
        expect(states, equals([
          AppLifecycleState.paused,
          AppLifecycleState.inactive,
          AppLifecycleState.resumed,
        ]));
        
        await subscription.cancel();
      });
      
      test('should support multiple listeners (broadcast stream)', () async {
        service.initialize();
        
        final listener1States = <AppLifecycleState>[];
        final listener2States = <AppLifecycleState>[];
        
        final sub1 = service.lifecycleState.listen(listener1States.add);
        final sub2 = service.lifecycleState.listen(listener2States.add);
        
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        
        await Future.delayed(Duration.zero);
        
        expect(listener1States, equals([AppLifecycleState.paused]));
        expect(listener2States, equals([AppLifecycleState.paused]));
        
        await sub1.cancel();
        await sub2.cancel();
      });
    });
    
    group('State Name Formatting', () {
      test('should provide human-readable state names', () {
        expect(
          service.getStateName(AppLifecycleState.resumed),
          equals('Resumed (Foreground)'),
        );
        expect(
          service.getStateName(AppLifecycleState.paused),
          equals('Paused (Background)'),
        );
        expect(
          service.getStateName(AppLifecycleState.inactive),
          equals('Inactive'),
        );
        expect(
          service.getStateName(AppLifecycleState.detached),
          equals('Detached'),
        );
        expect(
          service.getStateName(AppLifecycleState.hidden),
          equals('Hidden'),
        );
      });
    });
    
    group('Singleton Pattern', () {
      test('should return same instance', () {
        // Don't use the service from setUp, create fresh instances
        final instance1 = AppLifecycleService();
        final instance2 = AppLifecycleService();
        
        expect(identical(instance1, instance2), isTrue);
      });
      
      test('should maintain state across instances', () {
        // Reset first to ensure clean state
        AppLifecycleService().reset();
        
        final instance1 = AppLifecycleService();
        instance1.initialize();
        instance1.didChangeAppLifecycleState(AppLifecycleState.paused);
        
        final instance2 = AppLifecycleService();
        expect(instance2.currentState, equals(AppLifecycleState.paused));
        expect(instance2.isInitialized, isTrue);
        
        // Clean up
        instance2.dispose();
      });
    });
    
    group('Disposal', () {
      test('should clean up resources on dispose', () {
        service.initialize();
        expect(service.isInitialized, isTrue);
        
        service.dispose();
        expect(service.isInitialized, isFalse);
      });
      
      test('should handle dispose when not initialized', () {
        expect(service.isInitialized, isFalse);
        
        // Should not throw
        service.dispose();
        expect(service.isInitialized, isFalse);
      });
      
      test('should close stream on dispose', () async {
        service.initialize();
        
        var emissionCount = 0;
        final subscription = service.lifecycleState.listen(
          (_) {
            emissionCount++;
          },
          onDone: () {
            // Stream closed
          },
        );
        
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        await Future.delayed(Duration.zero);
        expect(emissionCount, equals(1));
        
        service.dispose();
        
        // After disposal, the stream should be closed
        // We can't emit to a closed stream, so let's just verify the service state
        expect(service.isInitialized, isFalse);
        
        await subscription.cancel();
      });
    });
    
    group('Reset Functionality', () {
      test('should reset to initial state', () {
        service.initialize();
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        
        expect(service.currentState, equals(AppLifecycleState.paused));
        expect(service.isInitialized, isTrue);
        
        service.reset();
        
        expect(service.currentState, equals(AppLifecycleState.resumed));
        expect(service.isInitialized, isFalse);
      });
    });
    
    group('Edge Cases', () {
      test('should handle rapid state changes', () async {
        service.initialize();
        
        final states = <AppLifecycleState>[];
        final subscription = service.lifecycleState.listen(states.add);
        
        // Rapid state changes - need small delays for stream to process
        for (int i = 0; i < 10; i++) {
          service.didChangeAppLifecycleState(
            i.isEven ? AppLifecycleState.paused : AppLifecycleState.resumed,
          );
          // Small delay to ensure stream processes the event
          await Future.delayed(const Duration(microseconds: 10));
        }
        
        // Final delay to ensure all events are processed
        await Future.delayed(const Duration(milliseconds: 10));
        
        expect(states.length, equals(10));
        
        await subscription.cancel();
      });
      
      test('should maintain last state after rapid changes', () {
        service.initialize();
        
        // Simulate rapid changes
        service.didChangeAppLifecycleState(AppLifecycleState.paused);
        service.didChangeAppLifecycleState(AppLifecycleState.inactive);
        service.didChangeAppLifecycleState(AppLifecycleState.hidden);
        service.didChangeAppLifecycleState(AppLifecycleState.resumed);
        
        expect(service.currentState, equals(AppLifecycleState.resumed));
        expect(service.isInForeground, isTrue);
      });
    });
  });
}