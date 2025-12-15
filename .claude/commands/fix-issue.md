---
description: Fix GitHub issue with pattern compliance
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebFetch, mcp__pal__debug, mcp__pal__thinkdeep
---

# GitHub Issue Fix Workflow

You are fixing issue: **$ARGUMENTS**

## Workflow Overview

1. Load issue context
2. Investigate root cause
3. Implement fix with pattern compliance
4. Test thoroughly
5. Verify quality gates

---

## Checkpoint 0: Load Issue Context

**Fetch issue details:**

```bash
gh issue view {issue_number}
```

**Or if URL provided:**

Use WebFetch to read issue content.

**Extract key information:**

- Issue description
- Expected behavior
- Actual behavior
- Steps to reproduce
- Related files mentioned

**Output**: "✓ Checkpoint 0 complete - Issue loaded: {title}"

---

## Checkpoint 1: Root Cause Investigation

**Use debug tool for complex issues:**

```
mcp__pal__debug(
    step="Investigating issue #{issue_number}...",
    step_number=1,
    total_steps=3,
    next_step_required=true,
    findings="Issue description: ...",
    hypothesis="The root cause might be..."
)
```

**Search for related code:**

```bash
# Find related files
grep -r "{keyword}" app/ --include="*.py"
grep -r "{keyword}" resources/ --include="*.tsx"

# Find error sources
grep -r "{error_message}" app/
```

**Read related files:**

```bash
cat {related_file}
```

**Document findings:**

```markdown
## Investigation Findings

### Root Cause
[Description of the root cause]

### Affected Files
- `path/to/file.py:line` - Description
- `path/to/file.tsx:line` - Description

### Proposed Fix
[Description of the fix approach]
```

**Output**: "✓ Checkpoint 1 complete - Root cause identified"

---

## Checkpoint 2: Pattern Check

**Before implementing fix, verify patterns:**

Read similar implementations to understand existing patterns:

```bash
# Find similar code
grep -r "similar_pattern" app/
```

**Ensure fix follows:**

- [ ] Existing code style
- [ ] Type hint conventions (T | None)
- [ ] Error handling patterns
- [ ] Test patterns

**Output**: "✓ Checkpoint 2 complete - Patterns verified"

---

## Checkpoint 3: Implement Fix

**Make minimal, focused changes:**

- Only fix what's broken
- Don't refactor surrounding code
- Don't add unrelated improvements

**Edit files:**

Use Edit tool for precise changes.

**Document changes:**

```markdown
## Changes Made

### File: `path/to/file.py`
- Line X: Changed Y to Z
- Reason: [explanation]
```

**Output**: "✓ Checkpoint 3 complete - Fix implemented"

---

## Checkpoint 4: Add Tests

**Create test for the fix:**

```python
@pytest.mark.asyncio
async def test_issue_{issue_number}_fix() -> None:
    """Regression test for issue #{issue_number}."""
    # Test that the bug is fixed
    ...
```

**Ensure test would have caught the bug:**

- Test should fail without the fix
- Test should pass with the fix

**Output**: "✓ Checkpoint 4 complete - Test added"

---

## Checkpoint 5: Run Quality Gates

**Run tests:**

```bash
make test
```

**Run linting:**

```bash
make lint
```

**Run type checking:**

```bash
make type-check
```

**All must pass.**

**Output**: "✓ Checkpoint 5 complete - All quality gates pass"

---

## Checkpoint 6: Verify Fix

**Manual verification (if applicable):**

1. Start the application
2. Reproduce the original issue steps
3. Verify the issue is fixed

**Automated verification:**

```bash
uv run pytest tests/ -k "issue_{issue_number}" -v
```

**Output**: "✓ Checkpoint 6 complete - Fix verified"

---

## Final Summary

```
Issue Fix Complete ✓

Issue: #{issue_number} - {title}
Root Cause: {brief description}

Changes:
- `path/to/file.py` - {change description}

Tests Added:
- `tests/unit/test_issue_{issue_number}.py`

Quality Gates:
- ✓ make test passes
- ✓ make lint passes
- ✓ make type-check passes

Suggested commit message:
fix: {brief description of fix}

Fixes #{issue_number}

Suggested PR title:
fix: {title} (#{issue_number})
```
