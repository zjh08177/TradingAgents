# Aggressive Optimization Plan for TradingAgents Project

## Current Status
- **Total Size**: 2.2GB
- **Major Consumers**:
  - Root .venv: 673MB (duplicate of backend)
  - Backend .venv: 626MB (251 packages!)
  - Trading-graph-server .venv: 274MB (102 packages)
  - Trading_dummy build: 395MB (Flutter artifacts)
  - Hidden directories: 80MB+ (.langgraph_api, .swarm)

## Root Causes
1. **Triple Virtual Environments**: 3 separate .venv directories (root, backend, trading-graph-server)
2. **Package Bloat**: 251 packages in backend (includes heavy GUI libraries like chainlit)
3. **Large Binaries**: onnxruntime (120MB+), chromadb (43MB), grpc (31MB), mini_racer (38MB)
4. **Unnecessary Frameworks**: Chainlit frontend (28MB) in a backend-only project
5. **Flutter Build Artifacts**: 395MB of iOS/Android build files
6. **Hidden State**: 61MB .langgraph_api checkpoints, 12MB .swarm databases

## Aggressive Optimization Plan

### Phase 1: Remove Duplicate Virtual Environments
1. **Delete root .venv** - It's a duplicate of backend
2. **Consolidate environments** - Use single venv or Docker

### Phase 2: Clean Unnecessary Dependencies
1. **Backend Cleanup**:
   - Remove chainlit (frontend framework) - Save 28MB
   - Remove onnxruntime (unless actively used) - Save 120MB
   - Remove chromadb (if not using vector DB) - Save 43MB
   - Remove py_mini_racer (JS engine) - Save 38MB

2. **Trading-graph-server Cleanup**:
   - Audit 102 packages for actual usage
   - Remove development tools from production

### Phase 3: Clean Build Artifacts
1. **Flutter Cleanup**:
   - Remove trading_dummy/build - Save 395MB
   - Keep only source code

### Phase 4: Clean Hidden Directories
1. **LangGraph API**:
   - Backup .langgraph_api checkpoints
   - Clean old checkpoints - Save 50MB+
2. **Swarm Databases**:
   - Export important data
   - Reset databases - Save 18MB

### Phase 5: Data Management
1. **CSV Cache**:
   - Implement date-based retention (keep last 7 days)
   - Deduplicate across projects - Save 7MB+
2. **Debug Logs**:
   - Keep only last 3 days of logs
   - Compress older logs - Save 30MB+

### Phase 6: Create Minimal Requirements
1. Create lean requirements.txt with only essential packages
2. Document which packages are for development vs production

## Expected Results
- **Target Size**: <500MB (from 2.2GB)
- **Reduction**: 75%+
- **Performance**: Faster installs, CI/CD, and development

## Risk Mitigation
1. **Backup First**: Create full backup before optimization
2. **Test Thoroughly**: Verify all functionality after cleanup
3. **Document Dependencies**: Track why each package is needed
4. **Gradual Rollout**: Clean in phases with validation