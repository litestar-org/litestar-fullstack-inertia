---
description: Create a PRD with pattern learning and adaptive complexity
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, mcp__context7__resolve-library-id, mcp__context7__get-library-docs, mcp__sequential-thinking__sequentialthinking, mcp__pal__planner
---

# Intelligent PRD Creation Workflow

You are creating a Product Requirements Document for: **$ARGUMENTS**

## Intelligence Layer (ACTIVATE FIRST)

Before starting checkpoints:

1. **Read MCP Strategy**: Load `.claude/mcp-strategy.md` for tool selection
2. **Learn from Codebase**: Read 3-5 similar implementations
3. **Assess Complexity**: Determine simple/medium/complex
4. **Adapt Workflow**: Adjust checkpoint depth

## Critical Rules

1. **CONTEXT FIRST** - Read existing patterns before planning
2. **NO CODE MODIFICATION** - Planning only (specs/ directory only)
3. **PATTERN LEARNING** - Identify 3-5 similar features
4. **ADAPTIVE DEPTH** - Simple=6, Medium=8, Complex=10+ checkpoints
5. **RESEARCH GROUNDED** - Minimum 2000+ words research
6. **COMPREHENSIVE PRD** - Minimum 3200+ words

---

## Checkpoint 0: Intelligence Bootstrap

**Load project intelligence:**

1. Read `CLAUDE.md` (or `AGENTS.md`)
2. Read `specs/guides/patterns/README.md`
3. Read `.claude/mcp-strategy.md`

**Learn from existing implementations:**

For this Litestar project, search in:
- `app/domain/` for backend patterns
- `resources/pages/` for frontend patterns
- `app/db/models/` for data model patterns

**Assess complexity:**

- **Simple**: Single file, CRUD, config change → 6 checkpoints
- **Medium**: New controller/service, 2-3 files → 8 checkpoints
- **Complex**: New domain module, schema changes, 5+ files → 10+ checkpoints

**Output**: "✓ Checkpoint 0 complete - Complexity: [level], Checkpoints: [count]"

---

## Checkpoint 1: Pattern Recognition

**Identify similar implementations:**

```bash
# Search for related patterns in backend
grep -r "class.*Controller" app/domain/ | head -5
grep -r "class.*Service" app/domain/ | head -5

# Search for related patterns in frontend
ls resources/pages/
```

Read at least 3 similar files and document:

```markdown
## Similar Implementations

1. `app/domain/{feature}/controllers.py` - Description
2. `app/domain/{feature}/services.py` - Description
3. `resources/pages/{feature}/` - Description

## Patterns Observed

- Controller structure: Litestar controller with route decorators
- Service pattern: Extends SQLAlchemyAsyncRepositoryService
- Inertia integration: Returns Inertia responses with typed props
- Repository pattern: advanced-alchemy repositories
```

**Output**: "✓ Checkpoint 1 complete - Patterns identified from [N] files"

---

## Checkpoint 2: Workspace Creation

Create PRD workspace:

```bash
mkdir -p specs/active/{slug}/research
mkdir -p specs/active/{slug}/tmp
mkdir -p specs/active/{slug}/patterns
```

**Output**: "✓ Checkpoint 2 complete - Workspace at specs/active/{slug}/"

---

## Checkpoint 3: Intelligent Analysis

**Use appropriate tool based on complexity:**

- **Simple**: 10 structured thoughts (manual)
- **Medium**: `mcp__sequential-thinking__sequentialthinking` (15 thoughts)
- **Complex**: `mcp__pal__planner` or `mcp__pal__thinkdeep`

Analyze:
1. How does this feature fit Litestar's architecture?
2. What existing patterns can be reused?
3. What new patterns might be needed?
4. How does Inertia.js affect the implementation?
5. What database models/migrations are needed?

Save analysis to `specs/active/{slug}/research/analysis.md`

**Output**: "✓ Checkpoint 3 complete - Analysis using [tool]"

---

## Checkpoint 4: Research (2000+ words)

**Priority order:**

1. **Pattern Library**: `specs/guides/patterns/`
2. **Internal Guides**: `specs/guides/`, existing CLAUDE.md
3. **Context7**: Library documentation for Litestar, React, Inertia
4. **WebSearch**: Best practices, recent updates

**Context7 lookups for this project:**

```
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="{relevant_topic}",
    mode="code"
)
```

Write research to `specs/active/{slug}/research/plan.md`

**Verify word count:**
```bash
wc -w specs/active/{slug}/research/plan.md
```

**Output**: "✓ Checkpoint 4 complete - Research ([word_count] words)"

---

## Checkpoint 5: Write PRD (3200+ words)

Write comprehensive PRD to `specs/active/{slug}/prd.md`:

```markdown
# PRD: {Feature Name}

## Intelligence Context

- **Complexity**: [simple|medium|complex]
- **Similar Features Analyzed**: [list]
- **Patterns to Follow**: [list]
- **Tool Used for Analysis**: [tool]

## Problem Statement

[Clear problem definition]

## Goals & Success Metrics

[Measurable goals]

## Acceptance Criteria

- [ ] Specific, measurable criterion 1
- [ ] Specific, measurable criterion 2
- [ ] Tests pass with 90%+ coverage on new code
- [ ] Type checking passes (mypy + pyright)
- [ ] Linting passes (ruff + biome)

## Technical Approach

### Backend (Litestar)

- Controller: `app/domain/{feature}/controllers.py`
- Service: `app/domain/{feature}/services.py`
- Repository: `app/domain/{feature}/repositories.py`
- Models: `app/db/models/{model}.py`

### Frontend (React/Inertia)

- Page: `resources/pages/{feature}/index.tsx`
- Components: `resources/components/{feature}/`

### Database

[Migrations needed]

## Testing Strategy

- Unit tests for services
- Integration tests for controllers
- Frontend component tests (if applicable)

## Pattern Compliance

[How this follows existing patterns]
```

**Verify word count:**
```bash
wc -w specs/active/{slug}/prd.md
```

**Output**: "✓ Checkpoint 5 complete - PRD ([word_count] words)"

---

## Checkpoint 6: Task Breakdown

Adapt task count to complexity:

- **Simple**: 5-8 tasks
- **Medium**: 8-12 tasks
- **Complex**: 12-20 tasks

Write to `specs/active/{slug}/tasks.md`:

```markdown
# Implementation Tasks

## Phase 1: Backend Foundation
- [ ] Create database models
- [ ] Create migration
- [ ] Create repository
- [ ] Create service

## Phase 2: API Layer
- [ ] Create controller
- [ ] Add routes
- [ ] Add dependencies

## Phase 3: Frontend
- [ ] Create Inertia page
- [ ] Create components
- [ ] Add navigation

## Phase 4: Testing
- [ ] Unit tests for service
- [ ] Integration tests for controller
- [ ] Frontend tests (if applicable)

## Phase 5: Documentation
- [ ] Update patterns library if new patterns
```

**Output**: "✓ Checkpoint 6 complete - [N] tasks defined"

---

## Checkpoint 7: Recovery Guide

Create `specs/active/{slug}/RECOVERY.md`:

```markdown
# Recovery Guide for {Feature}

## Intelligence Context (for session resumption)

- Complexity: [level]
- Patterns identified: [list]
- Similar features: [list]

## Current Status

- [ ] PRD complete
- [ ] Tasks defined
- [ ] Ready for implementation

## Key Files

- PRD: `specs/active/{slug}/prd.md`
- Tasks: `specs/active/{slug}/tasks.md`
- Research: `specs/active/{slug}/research/`

## To Resume

1. Read this file
2. Read PRD
3. Check task completion status
4. Run `/implement {slug}` to continue
```

**Output**: "✓ Checkpoint 7 complete - Recovery guide created"

---

## Checkpoint 8: Git Verification

```bash
git status --porcelain app/ resources/ | grep -v "^??"
```

**Expected**: No modified source files (only specs/ directory)

**Output**: "✓ Checkpoint 8 complete - No source code modified"

---

## Final Summary

```
PRD Phase Complete ✓

Workspace: specs/active/{slug}/
Complexity: [simple|medium|complex]
Checkpoints: [N] completed

Intelligence:
- ✓ Pattern library consulted
- ✓ [N] similar features analyzed
- ✓ Tool selection optimized: [tool]

Files Created:
- specs/active/{slug}/prd.md ([N] words)
- specs/active/{slug}/tasks.md ([N] tasks)
- specs/active/{slug}/research/plan.md
- specs/active/{slug}/research/analysis.md
- specs/active/{slug}/RECOVERY.md

Next: Run `/implement {slug}`
```
