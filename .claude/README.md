# MediSupply Multi-Agent Orchestration System

Complete guide to implementing features using coordinated AI agents in Claude Code.

## Quick Start

### For New Features

```bash
# 1. Invoke master orchestrator
/master-orchestrator "Implement [feature description]"

# 2. Answer clarification questions

# 3. Review generated spec file
# (Located in .claude/requests/{request_id}/SPEC.md)

# 4. Approve spec
Reply: "approved"

# 5. Review implementation plan
# (Located in .claude/requests/{request_id}/PLAN.md)

# 6. Approve plan
Reply: "approved"

# 7. Monitor progress
# Orchestrator will provide updates at key milestones

# 8. Done!
# All code implemented, tested, and documented
```

---

## System Architecture

### Agent Hierarchy

```
┌─────────────────────────┐
│   Master Orchestrator   │ ← Entry point
│  (Feature coordination) │
└───────────┬─────────────┘
            │
            ├─→ Context Manager (Knowledge base)
            │   └─→ Code Archeologist (Codebase expert)
            │
            ├─→ Backend Architect (Design decisions)
            │   └─→ Consults Context Manager
            │
            └─→ Task Coordinator (Implementation coordination)
                ├─→ Python Pro (Use cases, domain logic)
                ├─→ FastAPI Pro (Controllers, APIs)
                ├─→ Test Automator (Unit tests)
                ├─→ QA Tester (API testing)
                └─→ Debugger (Fix issues)
```

### Chain of Command for Questions

```
Implementation Agent (Python Pro, FastAPI Pro)
  ↓ (has question)
Task Coordinator
  ↓ (checks design, if unclear)
Backend Architect
  ↓ (if needs context)
Context Manager
  ↓ (checks docs & codebase via Code Archeologist)
  ├─→ Answer found → returns answer
  └─→ No answer → escalates
        ↓
Master Orchestrator
  ↓ (if user decision needed)
User
```

### ⚠️ CRITICAL ORCHESTRATION RULES ⚠️

**When coordinating agents, you MUST:**

1. **ALWAYS FORWARD AGENT QUESTIONS**
   - If an agent asks a question, forward it IMMEDIATELY to the right agent or user
   - DO NOT hold questions, interpret them, or answer them yourself
   - DO NOT make assumptions about what the agent needs
   - Follow the chain of command above

2. **NEVER LIE ABOUT TASK STATUS**
   - If a task FAILED → Report "FAILED" with the exact error
   - If a task is BLOCKED → Report "BLOCKED" with what it's waiting for
   - If a task is INCOMPLETE → Report "INCOMPLETE" with what's missing
   - DO NOT report success when the task did not complete fully

3. **AGENT QUESTIONS = BLOCKING STATE**
   - When an agent asks a question, it is PAUSED/BLOCKED
   - The workflow is STOPPED until the question is answered
   - You MUST forward the question immediately
   - DO NOT continue as if the task completed

4. **HONEST STATUS REPORTING**
   - Report exactly what happened: success, failure, error, blocked, incomplete
   - Include error messages verbatim
   - Include what the agent is waiting for
   - Include which step failed or where it stopped

**Example - WRONG:**
```
Agent asked: "Should I use pattern A or B?"
You: "The agent completed the analysis successfully!"
```

**Example - CORRECT:**
```
Agent Status: BLOCKED - Waiting for user decision
Agent Question: "Should I use pattern A or B?"

Forwarding to user...
```

---

## Agent Roles & Responsibilities

### 1. Master Orchestrator (`/master-orchestrator`)

**Purpose**: Entry point for all feature development

**Responsibilities**:
- Gather requirements through Q&A
- Create comprehensive spec files
- Coordinate with Backend Architect for design
- Delegate to Task Coordinator for implementation
- Ensure quality through testing
- Document decisions via Context Manager
- Clean up artifacts after completion

**When to use**: Start of every feature implementation

**Invocation**:
```
/master-orchestrator "Implement seller visit creation with GPS tracking and offline support"
```

---

### 2. Context Manager (`/context-manager`)

**Purpose**: Central knowledge base and decision tracker

**Responsibilities**:
- Maintain `.claude/context/architecture.md`
- Route implementation questions to Code Archeologist
- Answer architectural questions
- Track architecture decisions
- Escalate unknowns to user
- Document decisions after feature completion

**When consulted**: 
- Backend Architect needs existing decisions
- Agents have architectural questions
- Need to verify patterns/approaches

**Maintains**:
- `.claude/context/architecture.md` - System architecture and decisions
- `.claude/context/testing-guidelines.md` - Testing practices
- `.claude/context/er-diagram.md` - Database schema

---

### 3. Code Archeologist (`/code-archeologist`)

**Purpose**: Codebase expert - analyzes and documents patterns

**Responsibilities**:
- Analyze existing code for patterns
- Document patterns in `.claude/context/code-patterns.md`
- Answer "how do we do X in this codebase?"
- Provide code examples from existing implementation
- Keep pattern documentation current

**When consulted**: 
- Via Context Manager for implementation questions
- When documenting new patterns
- When analyzing similar features

**Maintains**:
- `.claude/context/code-patterns.md` - Coding standards and patterns

**Example questions**:
- "How do we handle database transactions?"
- "What's the error handling pattern for use cases?"
- "Show me an example of a similar API endpoint"

---

### 3. Backend Architect (`/backend-architect`)

**Purpose**: Makes technical design decisions

**From**: `backend-development` plugin (wshobson/agents)

**Responsibilities**:
- Review specs and create design documents
- Make architecture decisions
- Define component structure
- Design integration points
- Consult Context Manager for existing patterns
- Document design rationale

**Creates**: `.claude/requests/{request_id}/DESIGN.md`

**Consults**:
- Context Manager for existing decisions
- Code Archeologist (via Context Manager) for patterns

---

### 4. Task Coordinator (`/task-coordinator`)

**Purpose**: Splits work and coordinates implementation team

**Responsibilities**:
- Break down design into discrete tasks
- Create task files with acceptance criteria
- Delegate to Python Pro and FastAPI Pro
- Coordinate agent collaboration
- Track progress in status files
- Handle test failures via Debugger
- Report progress to Master Orchestrator

**Creates**:
- `.claude/requests/{request_id}/task-{num}-{name}.md` - Individual tasks
- `.claude/requests/{request_id}/status.md` - Progress tracking

**Coordinates**:
- Python Pro (domain, use cases, repositories)
- FastAPI Pro (controllers, APIs, schemas)
- Test Automator (unit tests)
- QA Tester (API tests)
- Debugger (issue fixes)

---

### 5. Python Pro (`/python-pro`)

**Purpose**: Implements Python code (use cases, repositories, domain logic)

**From**: `python-development` plugin (wshobson/agents)

**Responsibilities**:
- Implement use cases following Clean Architecture
- Create repositories with async operations
- Implement domain models and business logic
- Follow patterns from Code Archeologist
- Consult Task Coordinator if questions arise
- Update task files with progress

**Works on**:
- Domain models
- Use cases (application layer)
- Repositories (data access)
- Business logic

---

### 6. FastAPI Pro (`/fastapi-pro`)

**Purpose**: Implements FastAPI controllers and schemas

**From**: `python-development` plugin (wshobson/agents)

**Responsibilities**:
- Create Pydantic schemas (request/response)
- Implement controllers (thin, delegate to use cases)
- Define API routes and endpoints
- Integrate with Python Pro's use cases
- Follow API design patterns
- NO exception handling in controllers (let global handler catch)

**Works on**:
- Controllers
- Pydantic schemas
- API routes
- Request/response models

---

### 7. Test Automator (`/test-automator`)

**Purpose**: Creates comprehensive unit tests

**From**: `unit-testing` plugin (wshobson/agents)

**Responsibilities**:
- Generate unit tests for all components
- Target 95%+ coverage
- Follow AAA pattern (Arrange-Act-Assert)
- Use pytest-asyncio for async code
- Mock dependencies appropriately
- Run tests and report coverage

**Tests**:
- Use cases (unit tests)
- Repositories (unit tests with DB mocks)
- Controllers (integration tests)
- Domain logic

---

### 8. QA Tester (`/qa-tester`)

**Purpose**: Tests API endpoints using curl

**Responsibilities**:
- Test all endpoints from spec
- Verify request/response formats
- Test error scenarios (400, 404, 409, etc.)
- Test edge cases (empty data, boundaries, special chars)
- Test business rules
- Document results with pass/fail
- Create detailed failure reports for Debugger

**Tests**:
- Happy path scenarios
- Validation errors
- Not found cases
- Conflict scenarios
- Authorization
- Edge cases
- Business rules

**Uses**: curl, httpie, jq

---

### 9. Debugger (`/debugger`)

**Purpose**: Fixes bugs and test failures

**From**: Multiple plugins - `debugging-toolkit`, `error-debugging`, `unit-testing`

**Responsibilities**:
- Analyze test failures
- Fix implementation bugs
- Debug error scenarios
- Ensure tests pass after fixes

**Invoked when**:
- Unit tests fail
- QA tests fail
- Implementation errors discovered

**Receives**:
- Detailed issue report
- Expected vs actual behavior
- Components involved
- Test output / error messages

---

## Complete Workflow

### Phase 1: Requirements Gathering

**Master Orchestrator** leads:

1. **User request**: "/master-orchestrator 'Implement seller visit feature'"

2. **Clarification questions** (5-10 questions):
   - Business requirements
   - API contracts
   - Error scenarios
   - Dependencies
   - Database changes
   - Performance needs

3. **Generate spec file**: `.claude/requests/{request_id}/SPEC.md`

4. **User reviews and approves**: "approved"

---

### Phase 2: Design & Planning

**Master Orchestrator** coordinates:

1. **Consult Context Manager**:
   ```
   /context-manager "Check for similar features or relevant decisions"
   ```
   - Context Manager checks architecture.md
   - Routes to Code Archeologist for implementation patterns

2. **Delegate to Backend Architect**:
   ```
   /backend-architect "Review spec and create design document"
   ```
   - Backend Architect reads spec
   - Consults /context-manager for existing patterns
   - Makes architecture decisions
   - Creates DESIGN.md

3. **Create implementation plan**: `PLAN.md`
   - Phase breakdown
   - Task list with dependencies
   - Agent assignments
   - Complexity estimates

4. **User reviews and approves plan**: "approved"

---

### Phase 3: Implementation

**Task Coordinator** executes:

1. **Break down into tasks**:
   - Task 1: Domain models (Python Pro)
   - Task 2: Repositories (Python Pro)
   - Task 3: Use cases (Python Pro)
   - Task 4: API controllers (FastAPI Pro)
   - Task 5: Unit tests (Test Automator)
   - Task 6: QA tests (QA Tester)

2. **For each task**:

   **Domain/Use Case/Repository** (Python Pro):
   ```
   /python-pro "Implement task-1-domain-models.md. Follow DESIGN.md and consult context-manager for patterns."
   ```
   - Python Pro reads task file
   - Reads design document
   - If question arises → asks Task Coordinator
   - Task Coordinator checks design or asks Backend Architect
   - Backend Architect might consult Context Manager
   - Context Manager might check Code Archeologist
   - Implements code following patterns
   - Updates task file with completion notes

   **API Controllers** (FastAPI Pro):
   ```
   /fastapi-pro "Implement task-4-api-controllers.md. Integrate with use cases from Python Pro."
   ```
   - FastAPI Pro reads task and design
   - Reads use cases from Python Pro
   - If needs clarification on use cases → asks Task Coordinator
   - Task Coordinator coordinates between FastAPI Pro and Python Pro
   - Implements controllers (thin, no try/catch)
   - Creates Pydantic schemas
   - Updates task file

3. **Progress tracking**: Task Coordinator updates `status.md` after each task

---

### Phase 4: Testing

**Task Coordinator** coordinates:

#### Unit Testing

1. **Delegate to Test Automator**:
   ```
   /test-automator "Create comprehensive unit tests with 95%+ coverage"
   ```

2. **Test Automator**:
   - Reads testing-guidelines.md
   - Generates tests (AAA pattern, fixtures, mocks)
   - Runs: `poetry run pytest --cov=src --cov-report=term-missing`

3. **If tests fail**:
   
   **Task Coordinator creates debugger task**:
   ```markdown
   # Debugger Task: Fix Test Failures
   
   ## Issue
   3 tests failing in OrdersUseCase
   
   ## Failed Tests
   - test_create_order_with_invalid_customer: AssertionError
   - test_create_order_with_duplicate: ValueError
   
   ## Expected Behavior (from spec)
   Should raise OrderValidationError with message "Customer not found"
   
   ## Current Output
   Raises ValueError with message "Invalid customer"
   
   ## Components Involved
   - src/orders/use_cases/create_order_use_case.py
   - src/orders/domain/exceptions.py
   - tests/orders/test_create_order_use_case.py
   ```
   
   **Delegate to Debugger**:
   ```
   /debugger "Fix test failures in task-debug-tests.md"
   ```
   
   **Debugger fixes issues**
   
   **Re-run tests until all pass**

#### API Testing

1. **Delegate to QA Tester**:
   ```
   /qa-tester "Test all endpoints from SPEC.md using curl"
   ```

2. **QA Tester**:
   - Tests all endpoints (happy path, errors, edge cases)
   - Documents results in qa-test-results.md

3. **If QA tests fail**:
   
   **QA Tester creates detailed report**:
   ```markdown
   ## ❌ GET /api/orders/{id} - FAILED
   
   **Issue**: Returns 500 when order doesn't exist
   **Expected**: Should return 404
   
   **Test Command**:
   curl -X GET http://localhost:8000/api/orders/99999
   
   **Actual Response**: {"detail": "Internal Server Error"}
   **HTTP Status**: 500
   
   **Expected** (from spec):
   Status: 404
   Response: {"detail": "Order not found"}
   
   **Components**: 
   - src/orders/controllers/orders_controller.py
   - src/orders/use_cases/get_order_use_case.py
   ```
   
   **Task Coordinator delegates to Debugger**
   
   **Re-test after fixes**

---

### Phase 5: Documentation & Cleanup

**Master Orchestrator** finalizes:

1. **Document decisions**:
   ```
   /context-manager "Document architecture decisions from .claude/requests/{request_id}/ into context files"
   ```
   - Context Manager updates architecture.md
   - Requests Code Archeologist update code-patterns.md

2. **Final report to user**:
   ```markdown
   ## Implementation Complete
   
   **Feature**: Seller Visit Creation
   **Request ID**: 20251031-1430-seller-visit
   
   **Summary**:
   - 15 files created
   - 8 files modified
   - 42 unit tests added (97% coverage)
   - 6 API endpoints implemented
   - All QA tests passing
   
   **Deviations**: None
   
   **Documentation Updated**:
   - architecture.md: Added seller visit architecture decision
   - code-patterns.md: Documented GPS tracking pattern
   ```

3. **Cleanup**:
   ```bash
   rm -rf .claude/requests/{request_id}
   ```

---

## File Structure

### Request Directory

```
.claude/requests/{request_id}/
├── SPEC.md                      # Feature specification
├── DESIGN.md                    # Architecture design (backend-architect)
├── PLAN.md                      # Implementation plan (master-orchestrator)
├── status.md                    # Progress tracking (task-coordinator)
├── task-1-domain-models.md     # Individual tasks
├── task-2-repositories.md
├── task-3-use-cases.md
├── task-4-api-controllers.md
├── task-5-unit-tests.md
├── task-6-qa-testing.md
├── task-debug-*.md              # Temporary debugger tasks
└── qa-test-results.md           # QA test report (qa-tester)
```

### Context Directory

```
.claude/context/
├── architecture.md              # System architecture & decisions
├── code-patterns.md             # Coding patterns & standards
├── testing-guidelines.md        # Testing practices
└── er-diagram.md               # Database schema
```

---

## Question Resolution Flow

### Example: Implementation Question

**Scenario**: Python Pro asks "How should I handle database transactions?"

```
1. Python Pro has question
   ↓
2. Python Pro asks Task Coordinator
   ↓
3. Task Coordinator checks DESIGN.md
   - Not specified in design
   ↓
4. Task Coordinator asks Backend Architect
   "/backend-architect 'Python Pro needs guidance on transaction handling for use cases'"
   ↓
5. Backend Architect asks Context Manager
   "/context-manager 'Check for existing transaction handling patterns'"
   ↓
6. Context Manager routes to Code Archeologist
   "/code-archeologist 'How do we handle transactions in use cases?'"
   ↓
7. Code Archeologist searches codebase
   - Finds pattern in existing use cases
   - Provides example from src/orders/use_cases/create_order.py
   ↓
8. Context Manager returns answer to Backend Architect
   ↓
9. Backend Architect makes decision
   ↓
10. Task Coordinator relays to Python Pro
    ↓
11. Python Pro implements following pattern
```

### Example: New Decision Needed

**Scenario**: Backend Architect needs to decide on new pattern

```
1. Backend Architect encounters new scenario
   ↓
2. Checks Context Manager
   "/context-manager 'Check for decisions on event publishing'"
   ↓
3. Context Manager checks:
   - architecture.md - No existing decision
   - Code Archeologist - No existing pattern
   ↓
4. Context Manager escalates
   "No existing pattern found. This requires new architecture decision."
   ↓
5. Backend Architect evaluates options
   - Reviews industry best practices
   - Considers project constraints
   - Proposes recommendation
   ↓
6. Escalates to Master Orchestrator
   "Need user decision: Should we use message queue or direct REST calls?"
   ↓
7. Master Orchestrator asks user
   ↓
8. User decides
   ↓
9. Backend Architect documents in DESIGN.md
   ↓
10. Context Manager documents in architecture.md
```

---

## Available Agents from Plugins

### From `python-development` plugin:
- `/python-pro` - Python implementation
- `/fastapi-pro` - FastAPI controllers
- `/django-pro` - Django (if needed)

### From `backend-development` plugin:
- `/backend-architect` - Architecture decisions
- `/graphql-architect` - GraphQL (if needed)
- `/tdd-orchestrator` - TDD workflows

### From `unit-testing` plugin:
- `/test-automator` - Unit test generation
- `/debugger` - Bug fixes

### From `debugging-toolkit` plugin:
- `/debugger` - Error analysis
- `/dx-optimizer` - Developer experience

### From `error-debugging` plugin:
- `/debugger` - Error debugging
- `/error-detective` - Error investigation

### From `agent-orchestration` plugin:
- `/context-manager` - Context management

### From `code-review-ai` plugin:
- `/architect-review` - Architecture review

### From `documentation-generation` plugin:
- `/docs-architect` - Documentation
- `/api-documenter` - API docs
- `/mermaid-expert` - Diagrams

---

## Usage Examples

### Example 1: Complete Feature Implementation

```bash
# Start implementation
/master-orchestrator "Implement product review system with ratings, comments, and moderation"

# Answer questions
Q: Should reviews require approval?
A: Yes, reviews should go through moderation

Q: What rating scale?
A: 1-5 stars

Q: Can users edit reviews?
A: Yes, within 24 hours of posting

# Review spec
(Check .claude/requests/20251031-1500-product-reviews/SPEC.md)

# Approve
"approved"

# Review plan
(Check PLAN.md)

# Approve
"approved"

# Monitor progress
# Orchestrator provides updates automatically

# Done!
# All code implemented, tested, documented
```

### Example 2: Quick Question to Context Manager

```bash
# Ask about existing patterns
/context-manager "What's our authentication approach for APIs?"

# Response:
## Context: Authentication Pattern

**Source**: architecture.md (Section: Authentication)

**Current Approach**:
- JWT tokens with RS256 signing
- Access token: 15 minutes
- Refresh token: 7 days
- Stored in HTTP-only cookies

**Example**:
See implementation in: src/auth/jwt_service.py

**Related**:
- Authorization uses RBAC (see architecture.md)
- Token refresh endpoint: POST /api/auth/refresh
```

### Example 3: Code Pattern Question

```bash
# Ask via Context Manager
/context-manager "How do we structure use cases?"

# Context Manager routes to Code Archeologist
# Response:
## Pattern: Use Case Structure

**Current Practice**:
Use cases follow Clean Architecture with clear input/output

**Example from Codebase**:
File: `src/orders/use_cases/create_order_use_case.py`

```python
class CreateOrderUseCase:
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo
    
    async def execute(self, input_dto: CreateOrderInput) -> CreateOrderOutput:
        # Validation
        if not input_dto.customer_id:
            raise OrderValidationError("Customer ID required")
        
        # Business logic
        order = Order.create(...)
        
        # Persistence
        saved_order = await self._order_repo.create(order)
        
        # Return output
        return CreateOrderOutput.from_entity(saved_order)
```

**Pattern Notes**:
- Single responsibility
- Domain exceptions (not ValueError/TypeError)
- Async for all I/O operations
- Clear input/output DTOs
```

---

## Troubleshooting

### "Tool names must be unique" Error

**Cause**: Multiple plugins registered same tool names

**Solution**: 
```bash
# Disable some plugins
/plugin disable plugin-name

# Keep only essential ones:
# - python-development
# - backend-development  
# - unit-testing
# - debugging-toolkit
# - agent-orchestration
```

### Agent Not Responding

**Check**:
```bash
# List available agents
/agents

# Check if agents exists
ls ~/.claude/agents/
ls .claude/agents/
```

**Fix**: If custom agent missing, ensure .md file is in correct location

### Tests Failing Repeatedly

**Process**:
1. Task Coordinator creates detailed debugger task
2. Delegates to /debugger
3. Debugger analyzes and fixes
4. Re-run tests
5. If still failing after 3 iterations, escalate to Master Orchestrator

### Context Manager Can't Answer Question

**Expected flow**:
1. Context Manager checks context files
2. Routes to Code Archeologist
3. If still no answer, escalates to Backend Architect
4. Backend Architect may escalate to Master Orchestrator → User

**This is normal** for questions requiring new decisions

---

## Best Practices

### For Users

1. **Provide complete requirements** in initial request
2. **Answer clarification questions** thoroughly
3. **Review spec carefully** before approving
4. **Trust the agents** - they follow established patterns
5. **Don't add requirements mid-implementation** - finish current feature first

### For Orchestration

1. **Always use slash commands** to invoke agents (not Task tool)
2. **Follow chain of command** for questions
3. **Document decisions** after completion
4. **Keep context files current**
5. **Clean up** request directories after completion

### For Implementation

1. **Follow patterns** from Code Archeologist
2. **Consult design documents** before asking questions
3. **Update task files** with progress
4. **Ask questions early** - don't make assumptions
5. **Test thoroughly** - 95%+ coverage target

---

## Configuration

### Permissions

See `settings.local.json` for configured permissions.

Current permissions allow:
- Reading all project files
- Running Python, Docker, CLI commands
- Creating/modifying files
- Web searches (if needed)

### Custom Agent Installation

To add custom agents:

```bash
# User-level (available everywhere)
mkdir -p ~/.claude/agents
cp agents-name.md ~/.claude/agents/

# Project-level (this project only)  
mkdir -p .claude/agents
cp agents-name.md .claude/agents/

# Verify
/agents
```

---

## Maintenance

### Keeping Context Current

**Code Archeologist responsibilities**:
- Update code-patterns.md when new patterns emerge
- Remove obsolete patterns
- Add examples from new implementations

**Context Manager responsibilities**:
- Update architecture.md after each feature
- Archive deprecated decisions
- Link related decisions
- Keep documentation accurate

**Periodic tasks**:
1. Review context files monthly
2. Update patterns documentation
3. Archive completed request directories (if not auto-deleted)
4. Verify all agents are current

---

## Getting Help

### In Claude Code

```bash
# Check available agents
/agents

# Check available plugins
/plugin list

# Read this documentation
view .claude/README.md
```

### Agent-Specific Help

Each agent has detailed instructions in their `.md` file:
- `~/.claude/agents/master-orchestrator.md`
- `~/.claude/agents/code-archeologist.md`
- `~/.claude/agents/task-coordinator.md`
- `~/.claude/agents/context-manager.md`
- `~/.claude/agents/qa-tester.md`

---

## Version History

- **2025-10-31**: Complete multi-agent orchestration system
  - Master Orchestrator for feature coordination
  - Code Archeologist for codebase analysis
  - Task Coordinator for implementation
  - Enhanced Context Manager with Code Archeologist integration
  - QA Tester for API testing
  - Complete chain of command for question resolution
  - Request-based artifact management