# Architecture Documentation

## Purpose

This directory contains system architecture documents, design decisions, and architectural patterns for the Trading Dummy application.

## Directory Structure

### `/sqlite-async-polling/`
**CURRENT ACTIVE FEATURE** - SQLite migration and async polling architecture:
- Core polling architecture for LangGraph background runs
- Hive to SQLite migration strategy and implementation
- Unified database interface design
- Platform-specific SQLite analysis
- Visual migration roadmap and timeline

### `/legacy/`
Contains historical architecture documentation including:
- Previous async job implementations
- Historical system designs  
- Archived implementation decisions

### Future Architecture
New architecture documents for upcoming features and technical solutions.

## Document Types

### System Architecture
- High-level system design
- Component relationships
- Data flow diagrams
- Technology stack decisions

### Design Patterns
- Architectural patterns used
- Design principles followed
- Code organization strategies
- Module boundaries

### Migration Strategies
- Database migration plans
- API migration approaches
- Legacy system integration
- Rollback strategies

## Naming Convention

Use the following naming pattern:
- `ARCHITECTURE_[COMPONENT]_[VERSION].md`
- `DESIGN_[PATTERN_NAME].md`
- `MIGRATION_[FROM]_TO_[TO].md`

## Template Structure

Each architecture document should include:
1. Overview and context
2. Architecture diagrams
3. Component descriptions
4. Technology decisions
5. Trade-offs and alternatives
6. Implementation considerations