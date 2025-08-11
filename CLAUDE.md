# Claude Code Configuration - SPARC Development Environment (Batchtools Optimized)

## Principles of Execution

### 1. KISS (Keep It Simple, Stupid)
- Encourages writing straightforward, uncomplicated solutions
- Avoids over-engineering and unnecessary complexity
- Results in more readable and maintainable code

### 2. YAGNI (You Aren't Gonna Need It)
- Prevents adding speculative features
- Focuses on implementing only what's currently needed
- Reduces code bloat and maintenance overhead

### 3. SOLID Principles
#### 3.1 Single Responsibility Principle
- Each class or module should have one, and only one, reason to change

#### 3.2 Open-Closed Principle
- Software entities should be open for extension but closed for modification

#### 3.3 Liskov Substitution Principle
- Objects should be replaceable with instances of their subtypes without altering the correctness of the program

#### 3.4 Interface Segregation Principle
- Many client-specific interfaces are better than one general-purpose interface

#### 3.5 Dependency Inversion Principle
- Depend on abstractions, not concrete implementations

### 4. DRY (Don't Repeat Yourself)
- Repeating code is an invitation to problems
- Keep logic in one place to avoid errors and facilitate maintenance
- Ensures consistency across the codebase

## Documentation Management Guidelines
- For trading-graph-server documents, store in `/Users/bytedance/Documents/TradingAgents/trading-graph-server/claude_doc` folder
- When creating docs, always check if existing docs need organizational restructuring into subfolders
- Create subfolders as needed to maintain clear and logical document organization

## Execution Guidelines
- For all bash commands, timeout set to 1200 seconds (20 minutes)
- the goal for fundermental/socail/market/news analyst is to get complete data, the reserach will be done by other agents in later steps. market analyst only need to do basic level data dedup and data quality improvement and   slight summary, the goal is to process the raw data in a way that can help later reserach agent to more effciently research.