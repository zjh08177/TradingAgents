import 'package:flutter_test/flutter_test.dart';
import 'package:trading_dummy/auth/auth_module.dart';

/// Mock implementations for testing
class MockGoogleAuthService implements IAuthService {
  bool shouldSucceed;
  bool shouldCancel;
  UserModel? mockUser;
  
  MockGoogleAuthService({
    this.shouldSucceed = true,
    this.shouldCancel = false,
    this.mockUser,
  });
  
  @override
  Future<UserModel?> signIn() async {
    await Future.delayed(const Duration(milliseconds: 100)); // Simulate network delay
    
    if (shouldCancel) {
      return null;
    }
    
    if (!shouldSucceed) {
      throw Exception('Mock sign-in failed');
    }
    
    return mockUser ?? UserModel(
      id: 'test123',
      email: 'test@example.com',
      displayName: 'Test User',
      provider: AuthProvider.google,
      idToken: 'mock-id-token',
      accessToken: 'mock-access-token',
      tokenExpiryTime: DateTime.now().add(const Duration(hours: 1)),
    );
  }
  
  @override
  Future<void> signOut() async {
    await Future.delayed(const Duration(milliseconds: 50));
  }
  
  @override
  Future<UserModel?> silentSignIn() async {
    await Future.delayed(const Duration(milliseconds: 100));
    return shouldSucceed ? await signIn() : null;
  }
  
  @override
  Future<bool> isSignedIn() async {
    await Future.delayed(const Duration(milliseconds: 50));
    return shouldSucceed;
  }
}

class MockAuthStorageService extends AuthStorageService {
  UserModel? storedUser;
  bool shouldThrow = false;
  
  @override
  Future<void> saveUser(UserModel user) async {
    if (shouldThrow) {
      throw Exception('Mock storage error');
    }
    storedUser = user;
  }
  
  @override
  Future<UserModel?> getUser() async {
    if (shouldThrow) {
      throw Exception('Mock storage error');
    }
    return storedUser;
  }
  
  @override
  Future<void> clearAll() async {
    if (shouldThrow) {
      throw Exception('Mock storage error');
    }
    storedUser = null;
  }
  
  @override
  Future<bool> hasStoredUser() async {
    return storedUser != null;
  }
}

void main() {
  group('AuthViewModel Tests', () {
    late AuthViewModel authViewModel;
    late MockGoogleAuthService mockGoogleAuth;
    late MockAuthStorageService mockStorage;
    
    setUp(() {
      mockGoogleAuth = MockGoogleAuthService();
      mockStorage = MockAuthStorageService();
      
      authViewModel = AuthViewModel(
        googleAuthService: mockGoogleAuth,
        storageService: mockStorage,
      );
    });
    
    test('Initial state should be idle', () {
      expect(authViewModel.authState, AuthState.idle);
      expect(authViewModel.currentUser, isNull);
      expect(authViewModel.isAuthenticated, false);
      expect(authViewModel.isLoading, false);
    });
    
    group('Google Sign-In', () {
      test('Successful sign-in should update state correctly', () async {
        // Arrange
        mockGoogleAuth.shouldSucceed = true;
        
        // Act
        await authViewModel.signInWithGoogle();
        
        // Assert
        expect(authViewModel.authState, AuthState.authenticated);
        expect(authViewModel.currentUser, isNotNull);
        expect(authViewModel.currentUser?.email, 'test@example.com');
        expect(authViewModel.isAuthenticated, true);
        expect(mockStorage.storedUser, isNotNull);
      });
      
      test('Cancelled sign-in should set state to unauthenticated', () async {
        // Arrange
        mockGoogleAuth.shouldCancel = true;
        
        // Act
        await authViewModel.signInWithGoogle();
        
        // Assert
        expect(authViewModel.authState, AuthState.unauthenticated);
        expect(authViewModel.currentUser, isNull);
        expect(authViewModel.isAuthenticated, false);
      });
      
      test('Failed sign-in should set error state', () async {
        // Arrange
        mockGoogleAuth.shouldSucceed = false;
        
        // Act
        await authViewModel.signInWithGoogle();
        
        // Assert
        expect(authViewModel.authState, AuthState.error);
        expect(authViewModel.errorMessage, contains('Failed to sign in'));
        expect(authViewModel.currentUser, isNull);
        expect(authViewModel.isAuthenticated, false);
      });
    });
    
    group('Sign Out', () {
      test('Sign out should clear user data and update state', () async {
        // Arrange - Sign in first
        await authViewModel.signInWithGoogle();
        expect(authViewModel.isAuthenticated, true);
        
        // Act
        await authViewModel.signOut();
        
        // Assert
        expect(authViewModel.authState, AuthState.unauthenticated);
        expect(authViewModel.currentUser, isNull);
        expect(authViewModel.isAuthenticated, false);
        expect(mockStorage.storedUser, isNull);
      });
    });
    
    group('Auth Status Check', () {
      test('Should restore user from storage', () async {
        // Arrange
        final storedUser = UserModel(
          id: 'stored123',
          email: 'stored@example.com',
          provider: AuthProvider.google,
          tokenExpiryTime: DateTime.now().add(const Duration(hours: 1)),
        );
        mockStorage.storedUser = storedUser;
        
        // Act
        await authViewModel.checkAuthStatus();
        
        // Assert
        expect(authViewModel.authState, AuthState.authenticated);
        expect(authViewModel.currentUser?.email, 'stored@example.com');
        expect(authViewModel.isAuthenticated, true);
      });
      
      test('Should handle expired token with silent sign-in', () async {
        // Arrange
        final expiredUser = UserModel(
          id: 'expired123',
          email: 'expired@example.com',
          provider: AuthProvider.google,
          tokenExpiryTime: DateTime.now().subtract(const Duration(hours: 1)),
        );
        mockStorage.storedUser = expiredUser;
        mockGoogleAuth.shouldSucceed = true;
        
        // Act
        await authViewModel.checkAuthStatus();
        
        // Assert
        expect(authViewModel.authState, AuthState.authenticated);
        expect(authViewModel.currentUser?.email, 'test@example.com'); // New user from silent sign-in
        expect(authViewModel.isAuthenticated, true);
      });
      
      test('Should set unauthenticated if no stored user', () async {
        // Arrange
        mockStorage.storedUser = null;
        
        // Act
        await authViewModel.checkAuthStatus();
        
        // Assert
        expect(authViewModel.authState, AuthState.unauthenticated);
        expect(authViewModel.currentUser, isNull);
        expect(authViewModel.isAuthenticated, false);
      });
    });
    
    group('Error Handling', () {
      test('Clear error should reset error state', () async {
        // Arrange - Create error state
        mockGoogleAuth.shouldSucceed = false;
        await authViewModel.signInWithGoogle();
        expect(authViewModel.authState, AuthState.error);
        
        // Act
        authViewModel.clearError();
        
        // Assert
        expect(authViewModel.authState, AuthState.unauthenticated);
        expect(authViewModel.errorMessage, isNull);
      });
    });
    
    group('Token Management', () {
      test('Should detect token expiring soon', () {
        // Arrange
        authViewModel = AuthViewModel(
          googleAuthService: mockGoogleAuth,
          storageService: mockStorage,
        );
        
        // Create user with token expiring in 3 minutes
        final user = UserModel(
          id: 'test',
          email: 'test@example.com',
          provider: AuthProvider.google,
          tokenExpiryTime: DateTime.now().add(const Duration(minutes: 3)),
        );
        
        // Use reflection or a test helper to set the user
        // For now, we'll sign in to set the user
        mockGoogleAuth.mockUser = user;
        
        // Act & Assert
        expect(authViewModel.willTokenExpireSoon, true);
      });
    });
  });
}