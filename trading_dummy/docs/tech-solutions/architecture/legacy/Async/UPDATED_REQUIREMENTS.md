# Updated Async Analysis Requirements

## Executive Summary

This document updates the async analysis architecture to align with actual production needs: direct server submission, LangGraph Studio integration, and simplified job tracking.

## Core Principle Changes

### From: Complex Client-Side Queue → To: Direct Server API

**Previous Architecture**:
- Client-side job queue with priority management
- Local Hive persistence
- Background isolate processing
- Complex retry logic
- Client-managed job states

**New Architecture**:
- Direct server API calls
- Server-managed queue
- LangGraph Studio visibility
- Simple status polling
- Server as single source of truth

## Updated Requirements

### 1. Direct Server Submission (Critical)

**Requirement**: All analysis requests must be sent directly to the server without client-side queuing.

**Acceptance Criteria**:
- [ ] Remove client-side JobQueueManager
- [ ] API call triggered immediately on submission
- [ ] No local job persistence before server submission
- [ ] Server response includes job ID for tracking

**API Contract**:
```dart
POST /api/analyze
{
  "ticker": "AAPL",
  "tradeDate": "2025-08-02"
}

Response:
{
  "jobId": "server-generated-uuid",
  "status": "processing",
  "submittedAt": "2025-08-02T10:30:00Z"
}
```

### 2. LangGraph Studio Integration (Critical)

**Requirement**: All submitted jobs must appear immediately in LangGraph Studio trace viewer.

**Acceptance Criteria**:
- [ ] LangGraph API called directly from server
- [ ] Trace ID returned in API response
- [ ] Trace visible in Studio within 1 second
- [ ] Full execution graph available

**Integration Points**:
- Server includes LangGraph trace headers
- Trace ID returned to client for debugging
- Direct link to Studio trace from app

### 3. Simplified Job Model (Critical)

**Requirement**: Remove priority levels and complex job states.

**Acceptance Criteria**:
- [ ] Single job type (no priority)
- [ ] Simple states: submitted → processing → completed/failed
- [ ] No client-side retry logic
- [ ] Server handles all job orchestration

**Simplified Job Model**:
```dart
class AnalysisRequest {
  final String ticker;
  final String tradeDate;
}

class AnalysisStatus {
  final String jobId;
  final String status; // submitted, processing, completed, failed
  final DateTime submittedAt;
  final DateTime? completedAt;
  final String? resultId;
  final String? error;
  final String? traceId; // LangGraph Studio trace
}
```

### 4. History Tab Implementation (High)

**Requirement**: History tab shows all submitted jobs with real-time status updates.

**Acceptance Criteria**:
- [ ] List all jobs from server
- [ ] Poll for status updates (5s interval)
- [ ] Show: ticker, date, status, duration
- [ ] Link to view results when complete
- [ ] Sort by submission time (newest first)

**History API**:
```dart
GET /api/jobs?limit=50

Response:
{
  "jobs": [
    {
      "jobId": "123",
      "ticker": "AAPL",
      "tradeDate": "2025-08-02",
      "status": "completed",
      "submittedAt": "...",
      "completedAt": "...",
      "duration": 45000, // ms
      "resultId": "456",
      "traceId": "langgraph-trace-789"
    }
  ]
}
```

### 5. UI/UX Fixes (Medium)

**Requirement**: Fix overflow errors and improve layout.

**Acceptance Criteria**:
- [ ] No RenderFlex overflow errors
- [ ] Responsive layout for all screen sizes
- [ ] Clear status indicators
- [ ] Proper text truncation
- [ ] Loading states for API calls

## Non-Functional Requirements

### Performance
- API submission: < 200ms
- Status polling: 5s interval
- History load: < 500ms
- UI updates: 60 FPS

### Reliability
- Graceful API error handling
- Offline queue for submissions
- Retry failed API calls
- Clear error messages

### Observability
- Client logs for API calls
- Server trace IDs
- LangGraph Studio integration
- Error tracking

## Out of Scope

1. Client-side job queue
2. Priority management
3. Local job persistence
4. Background isolate processing
5. Client-side retry logic
6. Complex job states
7. Notification system (moved to server)

## Migration Strategy

### Phase 1: Add Server APIs
- Implement direct submission endpoint
- Add job history endpoint
- Integrate LangGraph Studio

### Phase 2: Simplify Client
- Remove JobQueueManager
- Remove Hive persistence
- Simplify to API service

### Phase 3: Update UI
- Fix overflow issues
- Add history tab
- Simplify job submission

### Phase 4: Cleanup
- Remove unused code
- Update tests
- Update documentation