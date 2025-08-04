# Phase 6 Hive Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[UI Components]
        VM[ViewModels]
    end
    
    subgraph "Application Layer"
        JPS[JobPersistenceService]
        JQM[JobQueueManager]
        UC[Use Cases]
    end
    
    subgraph "Domain Layer"
        PJ[PersistentJob Entity]
        AJ[AnalysisJob Entity]
        JR[JobRepository Interface]
        IJR[IJobRepository Interface]
        JS[JobStatus Enum]
        JP[JobPriority Enum]
    end
    
    subgraph "Infrastructure Layer - Hive"
        subgraph "Models"
            HPJ[HivePersistentJob]
            HAJ[HiveAnalysisJob]
        end
        subgraph "Repositories"
            HPJR[HivePersistentJobRepository]
            HJR[HiveJobRepository]
        end
        subgraph "Hive Boxes"
            PJB[persistent_jobs Box]
            AJB[analysis_jobs Box]
        end
    end
    
    %% Relationships
    UI --> VM
    VM --> UC
    UC --> JPS
    JPS --> JR
    JPS --> JQM
    JQM --> IJR
    
    %% Domain to Infrastructure
    JR -.->|implements| HPJR
    IJR -.->|implements| HJR
    
    %% Entity mappings
    PJ -.->|maps to| HPJ
    AJ -.->|maps to| HAJ
    
    %% Repository to Storage
    HPJR --> PJB
    HJR --> AJB
    HPJ --> PJB
    HAJ --> AJB
    
    %% Bridge between systems
    JPS -->|converts| PJ
    JPS -->|converts| AJ
    
    style PJ fill:#e1f5fe
    style AJ fill:#e1f5fe
    style JR fill:#fff3e0
    style IJR fill:#fff3e0
    style HPJR fill:#c8e6c9
    style HJR fill:#c8e6c9
    style HPJ fill:#f3e5f5
    style HAJ fill:#f3e5f5
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant JPS as JobPersistenceService
    participant HPJR as HivePersistentJobRepository
    participant HPJ as HivePersistentJob
    participant HB as Hive Box
    
    Client->>JPS: persistJob(type, payload)
    JPS->>JPS: Create PersistentJob
    JPS->>HPJR: saveJob(PersistentJob)
    HPJR->>HPJ: fromDomain(PersistentJob)
    HPJ->>HB: put(id, HivePersistentJob)
    HB-->>HPJR: Success
    HPJR-->>JPS: Success
    JPS-->>Client: PersistentJob
    
    Note over JPS: Convert to AnalysisJob if needed
    JPS->>JPS: Convert for Queue
    JPS->>Client: Job Queued
```

## Component Integration

```mermaid
graph LR
    subgraph "Phase 1-2 (Existing)"
        AJ1[AnalysisJob]
        HAJ1[HiveAnalysisJob]
        HJR1[HiveJobRepository]
        AB[analysis_jobs Box]
    end
    
    subgraph "Phase 6 (Refactored)"
        PJ2[PersistentJob]
        HPJ2[HivePersistentJob]
        HPJR2[HivePersistentJobRepository]
        PB[persistent_jobs Box]
    end
    
    subgraph "Bridge Layer"
        JPS3[JobPersistenceService]
        JQM3[JobQueueManager]
    end
    
    AJ1 -.->|existing| HAJ1
    HAJ1 --> AB
    HJR1 --> AB
    
    PJ2 -.->|new| HPJ2
    HPJ2 --> PB
    HPJR2 --> PB
    
    JPS3 -->|manages| PJ2
    JPS3 -->|converts to| AJ1
    JPS3 --> HPJR2
    JQM3 --> HJR1
    
    style PJ2 fill:#bbdefb
    style HPJ2 fill:#c5cae9
    style HPJR2 fill:#b2dfdb
```

## Class Relationships (SOLID Compliance)

```mermaid
classDiagram
    class JobRepository {
        <<interface>>
        +saveJob(PersistentJob) Future
        +updateJob(PersistentJob) Future
        +getJob(String) Future~PersistentJob~
        +getJobsByStatus(JobStatus) Future~List~
        +getStatistics() Future~JobStatistics~
    }
    
    class IJobRepository {
        <<interface>>
        +save(AnalysisJob) Future
        +update(AnalysisJob) Future
        +getById(String) Future~AnalysisJob~
        +getByStatus(JobStatus) Future~List~
    }
    
    class HivePersistentJobRepository {
        -Box~HivePersistentJob~ _box
        +init() Future
        +saveJob(PersistentJob) Future
        +updateJob(PersistentJob) Future
    }
    
    class HiveJobRepository {
        -Box~HiveAnalysisJob~ _box
        +init() Future
        +save(AnalysisJob) Future
        +update(AnalysisJob) Future
    }
    
    class PersistentJob {
        +String id
        +String type
        +Map payload
        +JobStatus status
        +int priority
    }
    
    class AnalysisJob {
        +String id
        +String ticker
        +String tradeDate
        +JobStatus status
        +JobPriority priority
    }
    
    class HivePersistentJob {
        <<HiveType: 21>>
        +String id
        +String type
        +String payloadJson
        +fromDomain(PersistentJob)
        +toDomain() PersistentJob
    }
    
    class HiveAnalysisJob {
        <<HiveType: 20>>
        +String id
        +String ticker
        +String tradeDate
        +fromDomain(AnalysisJob)
        +toDomain() AnalysisJob
    }
    
    JobRepository <|.. HivePersistentJobRepository : implements
    IJobRepository <|.. HiveJobRepository : implements
    PersistentJob ..> HivePersistentJob : maps to
    AnalysisJob ..> HiveAnalysisJob : maps to
    HivePersistentJobRepository --> HivePersistentJob : uses
    HiveJobRepository --> HiveAnalysisJob : uses
```

## Hive Type ID Allocation

```mermaid
graph TD
    subgraph "Reserved Type IDs"
        T0["0-9: System Reserved"]
        T10["10-19: User/Auth Domain"]
        T20["20-29: Job Domain"]
        T30["30-39: Trading Domain"]
        T40["40-49: History Domain"]
    end
    
    subgraph "Job Domain Allocations"
        T20A["20: HiveAnalysisJob"]
        T21A["21: HivePersistentJob"]
        T22A["22-29: Future Job Types"]
    end
    
    T20 --> T20A
    T20 --> T21A
    T20 --> T22A
    
    style T20A fill:#90caf9
    style T21A fill:#81c784
```

## Migration Path

```mermaid
graph LR
    subgraph "Current State"
        SQL[SqliteJobRepository]
        SQLD[SQLite Database]
    end
    
    subgraph "Migration"
        M1[Create Hive Models]
        M2[Implement Repository]
        M3[Update Service]
        M4[Test & Verify]
        M5[Remove SQLite]
    end
    
    subgraph "Target State"
        HIVE[HivePersistentJobRepository]
        HIVEB[Hive Boxes]
    end
    
    SQL --> M1
    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> M5
    M5 --> HIVE
    HIVE --> HIVEB
    
    style SQL fill:#ffcdd2
    style HIVE fill:#c8e6c9
```

## Key Design Decisions

1. **Separate Hive Boxes**: `persistent_jobs` vs `analysis_jobs` for clear separation
2. **Type ID 21**: Next available ID after HiveAnalysisJob (20)
3. **JSON Serialization**: Complex fields (payload, result, metadata) stored as JSON strings
4. **Bridge Pattern**: JobPersistenceService bridges PersistentJob and AnalysisJob systems
5. **SOLID Compliance**: Clean interfaces, single responsibilities, dependency inversion

## Benefits of Hive Architecture

- **Consistency**: Single persistence technology across all phases
- **Performance**: Fast NoSQL operations, no SQL query overhead
- **Offline Support**: Works without network connectivity
- **Type Safety**: Generated adapters ensure type safety
- **Simplicity**: No SQL schema migrations needed
- **Flutter Integration**: Native Flutter support via hive_flutter