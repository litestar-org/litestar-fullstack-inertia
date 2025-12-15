# MCP Tool Strategy

## Tool Selection by Task Type

### Complex Architectural Decisions
1. **Primary**: `mcp__pal__thinkdeep`
2. **Secondary**: `mcp__sequential-thinking__sequentialthinking`
3. **Fallback**: Manual structured thinking

### Library Documentation Lookup
1. **Primary**: `mcp__context7__get-library-docs`
2. **Fallback**: WebSearch

**Context7 Library IDs for this project:**
- Litestar: `/litestar-org/litestar`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- React: `/facebook/react`
- Inertia.js: `/inertiajs/inertia`
- Tailwind CSS: `/tailwindlabs/tailwindcss`

### Multi-Phase Planning
1. **Primary**: `mcp__pal__planner`
2. **Fallback**: TodoWrite with structured checkpoints

### Code Analysis
1. **Primary**: `mcp__pal__analyze`
2. **Fallback**: Grep + Read for manual analysis

### Debugging
1. **Primary**: `mcp__pal__debug`
2. **Fallback**: Manual investigation with Bash

### Consensus Building
1. **Primary**: `mcp__pal__consensus`
2. **Use for**: Technology decisions, architecture trade-offs

## Complexity-Based Tool Selection

### Simple Features (6 checkpoints)
- Use basic tools (Read, Edit, Grep)
- Manual analysis acceptable
- Focus on speed

**Triggers:**
- Single file modification
- Simple CRUD operation
- Configuration change

### Medium Features (8 checkpoints)
- Use `mcp__sequential-thinking__sequentialthinking` (12-15 steps)
- Include pattern analysis
- Moderate research depth

**Triggers:**
- New service or controller
- 2-3 files modified
- New API endpoint

### Complex Features (10+ checkpoints)
- Use `mcp__pal__thinkdeep` or `mcp__pal__planner`
- Deep pattern analysis
- Comprehensive documentation research
- Multi-model consensus for decisions

**Triggers:**
- Architecture change
- 5+ files modified
- New domain module
- Database schema changes

## Tool Usage Examples

### Context7 for Litestar Documentation
```
mcp__context7__resolve-library-id(libraryName="litestar")
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="controllers",
    mode="code"
)
```

### Sequential Thinking for Feature Analysis
```
mcp__sequential-thinking__sequentialthinking(
    thought="Step 1: Analyze existing service patterns...",
    thoughtNumber=1,
    totalThoughts=12,
    nextThoughtNeeded=true
)
```

### ThinkDeep for Architecture Decisions
```
mcp__pal__thinkdeep(
    step="Analyzing authentication flow architecture...",
    step_number=1,
    total_steps=3,
    next_step_required=true,
    findings="...",
    relevant_files=["app/domain/accounts/services.py", ...]
)
```

## When NOT to Use MCP Tools

- Simple file edits or typo fixes
- Adding comments or documentation
- Formatting changes
- Single-line bug fixes
- Following explicit user instructions
