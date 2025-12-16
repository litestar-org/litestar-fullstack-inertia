# Gemini Agent System for litestar-fullstack-inertia

This document provides behavioral instructions and project context for Gemini CLI agents.

---

## BEHAVIORAL REQUIREMENTS (READ FIRST)

### Core Principles

1. **Verify Before Acting** - Never assume; always confirm understanding
2. **Research Before Implementing** - Search codebase and docs first
3. **Follow Existing Patterns** - Match the style of surrounding code
4. **Ask When Uncertain** - Questions are better than wrong assumptions

### Before ANY Code Changes

You MUST complete these steps before modifying source code:

1. **Verify Understanding**
   - Restate the task in your own words
   - Identify what success looks like
   - List the components that will be affected

2. **Search First**
   - Use `grep`/`find` to locate relevant existing code
   - Read similar implementations in the codebase
   - Check `specs/guides/` for documented patterns

3. **Check Patterns**
   - Read existing code that does similar things
   - Match the naming conventions used
   - Follow the error handling patterns

### STOP Conditions

**Stop and ask the user if**:

- More than 3 files need modification without explicit approval
- You cannot find similar patterns in the codebase
- The technical approach is unclear
- Requirements seem contradictory or ambiguous

---

## Project Overview

- **Name**: litestar-fullstack-inertia
- **Description**: Opinionated template for a Litestar application.
- **Languages**: Python, TypeScript
- **Frameworks**: Litestar, React, Inertia, Tailwind, SQLAlchemy
- **Testing**: pytest, Vitest
- **Linting**: ruff, mypy, biome

## Code Style Requirements (CRITICAL)

### Python

| Rule | Standard |
|------|----------|
| Type hints | PEP 604: `T | None` |
| Future annotations | **NEVER** - no `from __future__ import annotations` |
| Docstrings | Google style |
| Line length | 120 characters |
| Tests | Function-based only (no `class Test...`) |

### TypeScript

- Biome for formatting/linting
- Strict mode enabled
- Vitest for testing

## Checkpoint-Based Workflow

### Feature Lifecycle

1. **Planning (`/prd`)**: Create Product Requirements Document
2. **Implementation (`/implement`)**: Write code based on PRD
3. **Testing (`/test`)**: Create comprehensive test suite
4. **Review (`/review`)**: Verify quality gates and archive

### Quality Gates

All code must pass:

- **Tests**: `make test` - All tests passing
- **Linting**: `make lint` - Zero errors
- **Coverage**: 90%+ for modified modules
- **Anti-patterns**: No violations

## MCP Tools Available

### Context7 (Library Documentation)

```python
mcp__context7__resolve-library-id(libraryName="litestar")
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="plugins middleware",
    mode="code"
)
```

### Sequential Thinking (Complex Analysis)

```python
mcp__sequential-thinking__sequentialthinking(
    thought="Step 1: Analyze the requirement",
    thought_number=1,
    total_thoughts=10,
    next_thought_needed=True
)
```

### Zen Tools

- `mcp__zen__planner` - Multi-step planning
- `mcp__zen__thinkdeep` - Architectural analysis
- `mcp__zen__debug` - Systematic debugging
- `mcp__zen__analyze` - Code analysis
- `mcp__zen__consensus` - Multi-model decisions

## Remember

1. **Read before writing** - Always read existing code first
2. **Match existing patterns** - Don't invent new conventions
3. **Test everything** - 90%+ coverage required
4. **Document decisions** - Explain non-obvious choices
5. **Ask when uncertain** - Questions prevent mistakes
