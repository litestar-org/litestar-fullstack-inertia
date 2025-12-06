---
description: Explore codebase for patterns and understanding
allowed-tools: Read, Glob, Grep, Bash, Task, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
---

# Codebase Exploration

You are exploring: **$ARGUMENTS**

## Exploration Modes

Based on the query, use the appropriate exploration mode:

### Mode 1: Architecture Overview
**Trigger**: "architecture", "structure", "overview", "how does"

```bash
# Project structure
tree -L 2 -d app/ resources/

# Core configuration
cat app/server/core.py
cat app/config.py
```

### Mode 2: Feature Discovery
**Trigger**: "where is", "find", "locate"

```bash
# Search for patterns
grep -r "{pattern}" app/ --include="*.py"
grep -r "{pattern}" resources/ --include="*.tsx"

# Find files
find app/ -name "*{keyword}*"
find resources/ -name "*{keyword}*"
```

### Mode 3: Pattern Understanding
**Trigger**: "how to", "pattern", "example"

```bash
# Read existing implementations
cat app/domain/accounts/controllers.py
cat app/domain/accounts/services.py
cat resources/pages/dashboard.tsx
```

### Mode 4: Dependency Analysis
**Trigger**: "uses", "depends on", "related to"

```bash
# Find imports
grep -r "from app.domain.{feature}" app/
grep -r "import.*{feature}" resources/
```

---

## Quick Reference Exploration

### Backend Architecture

**Controllers** (Litestar with Inertia):
```bash
ls app/domain/*/controllers.py
cat app/domain/accounts/controllers.py | head -100
```

**Services** (advanced-alchemy):
```bash
ls app/domain/*/services.py
cat app/domain/accounts/services.py | head -100
```

**Models** (SQLAlchemy 2.0):
```bash
ls app/db/models/
cat app/db/models/user.py
```

**Repositories**:
```bash
ls app/domain/*/repositories.py
cat app/domain/accounts/repositories.py | head -50
```

### Frontend Architecture

**Pages** (React/Inertia):
```bash
ls resources/pages/
cat resources/pages/dashboard.tsx
```

**Components** (shadcn/ui):
```bash
ls resources/components/ui/
cat resources/components/ui/button.tsx
```

**Layouts**:
```bash
ls resources/layouts/
cat resources/layouts/app-layout.tsx
```

### Configuration

**App config**:
```bash
cat app/config.py | head -100
```

**Plugins**:
```bash
cat app/server/plugins.py
```

**Settings**:
```bash
cat app/lib/settings.py
```

---

## Library Documentation Lookup

Use Context7 for library-specific questions:

```
mcp__context7__get-library-docs(
    context7CompatibleLibraryID="/litestar-org/litestar",
    topic="{topic}",
    mode="code"
)
```

**Available library IDs**:
- Litestar: `/litestar-org/litestar`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- React: `/facebook/react`
- Inertia.js: `/inertiajs/inertia`

---

## Deep Exploration with Subagent

For complex explorations, use the Explore subagent:

```
Task(
    subagent_type="Explore",
    prompt="Explore {topic} in this codebase. Find all related files, understand the patterns, and explain how it works."
)
```

---

## Output Format

After exploration, provide:

```markdown
## Exploration: {topic}

### Summary
[Brief overview of what was found]

### Key Files
- `path/to/file.py` - Description
- `path/to/file.tsx` - Description

### Patterns Found
1. Pattern description
2. Pattern description

### Code Examples
[Relevant code snippets]

### Related Documentation
[Links or references to docs]
```
