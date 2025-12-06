---
description: Quality gate verification and pattern extraction
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, mcp__pal__analyze
---

# Review Workflow

You are reviewing the feature: **$ARGUMENTS**

## Review Objectives

1. **Quality Gate Verification**: All checks must pass
2. **Pattern Extraction**: Document new patterns for future use
3. **Documentation Update**: Ensure patterns library is updated
4. **Final Approval**: Ready for commit/merge

---

## Checkpoint 0: Load Review Context

**Load feature context:**

```bash
cat specs/active/{slug}/prd.md
cat specs/active/{slug}/tasks.md
cat specs/active/{slug}/tmp/new-patterns.md 2>/dev/null
```

**Identify modified files:**

```bash
git diff --name-only HEAD~5 | head -20
# or
git status --short
```

**Output**: "✓ Checkpoint 0 complete - [N] files to review"

---

## Checkpoint 1: Quality Gate - Tests

**Run full test suite:**

```bash
make test
```

**Expected**: All tests pass

**If failures**: Stop and fix before continuing.

**Output**: "✓ Checkpoint 1 complete - All tests pass"

---

## Checkpoint 2: Quality Gate - Linting

**Run pre-commit hooks:**

```bash
make pre-commit
```

**Run type checking:**

```bash
make type-check
```

**Run slots check:**

```bash
make slotscheck
```

**Run frontend linting:**

```bash
npx biome check resources/
```

**Expected**: All linting passes with zero errors

**Output**: "✓ Checkpoint 2 complete - All linting passes"

---

## Checkpoint 3: Quality Gate - Coverage

**Run coverage analysis:**

```bash
make coverage
```

**Check coverage for modified modules:**

```bash
uv run pytest tests/ --cov=app/domain/{feature} --cov-report=term-missing
```

**Required**: 90%+ coverage on new/modified code

**Output**: "✓ Checkpoint 3 complete - Coverage: [N]%"

---

## Checkpoint 4: Code Quality Analysis

**Use analyze tool for comprehensive review:**

```
mcp__pal__analyze(
    step="Reviewing code quality for {slug}...",
    step_number=1,
    total_steps=2,
    next_step_required=true,
    findings="...",
    analysis_type="quality",
    relevant_files=["app/domain/{feature}/..."]
)
```

**Check for:**

1. **Anti-patterns** from quality-gates.yaml
2. **Type hint consistency** (PEP 604 style)
3. **Docstring coverage**
4. **Error handling patterns**
5. **Security considerations**

**Document findings in `specs/active/{slug}/tmp/review-findings.md`**

**Output**: "✓ Checkpoint 4 complete - Code quality verified"

---

## Checkpoint 5: Pattern Compliance Check

**Verify patterns match existing codebase:**

Read similar implementations and compare:

```bash
# Compare controller structure
diff <(grep -A20 "class.*Controller" app/domain/accounts/controllers.py) \
     <(grep -A20 "class.*Controller" app/domain/{feature}/controllers.py)
```

**Check pattern compliance:**

- [ ] Controllers follow domain structure
- [ ] Services extend SQLAlchemyAsyncRepositoryService
- [ ] Inertia pages receive typed props
- [ ] Frontend uses shadcn/ui components
- [ ] Tests are function-based with pytest

**Output**: "✓ Checkpoint 5 complete - Pattern compliance verified"

---

## Checkpoint 6: Extract New Patterns

**If new patterns were discovered:**

Move from `specs/active/{slug}/tmp/new-patterns.md` to `specs/guides/patterns/`:

```bash
# Create pattern documentation
cat > specs/guides/patterns/{pattern-name}.md << 'EOF'
# Pattern: {Pattern Name}

## When to Use
[Describe use cases]

## Implementation
[Code example with reference to actual file]

## Reference Files
- `app/domain/{feature}/...`

## Added From
Feature: {slug}
Date: $(date +%Y-%m-%d)
EOF
```

**Update `specs/guides/patterns/README.md`** with new patterns.

**Output**: "✓ Checkpoint 6 complete - [N] patterns extracted"

---

## Checkpoint 7: Documentation Verification

**Check all tasks are complete:**

```bash
grep -c "^\- \[x\]" specs/active/{slug}/tasks.md
grep -c "^\- \[ \]" specs/active/{slug}/tasks.md
```

**Update RECOVERY.md with final status:**

```markdown
## Final Status: COMPLETE

All quality gates passed on [date].

### Summary
- Tests: PASS
- Coverage: [N]%
- Linting: PASS
- Type Check: PASS

### Files Modified
[list from git status]

### Ready for commit/merge
```

**Output**: "✓ Checkpoint 7 complete - Documentation updated"

---

## Checkpoint 8: Pre-Commit Final Check

**Run all quality gates one final time:**

```bash
make check-all
```

**Verify git status:**

```bash
git status
git diff --stat
```

**Output**: "✓ Checkpoint 8 complete - Ready for commit"

---

## Checkpoint 9: Archive Feature Spec

**Move completed spec to archive:**

```bash
mv specs/active/{slug} specs/archive/{slug}-$(date +%Y%m%d)
```

**Or keep in active if follow-up work planned.**

**Output**: "✓ Checkpoint 9 complete - Feature spec archived"

---

## Final Summary

```
Review Phase Complete ✓

Feature: {slug}
Status: APPROVED

Quality Gates:
- ✓ make test passes
- ✓ make lint passes
- ✓ make type-check passes
- ✓ make coverage (90%+)
- ✓ Frontend linting passes

Patterns:
- ✓ Pattern compliance verified
- [N] new patterns extracted to library

Documentation:
- ✓ All tasks complete
- ✓ RECOVERY.md updated
- ✓ Patterns library updated

Files Modified: [N]
Coverage: [N]%

Ready for commit!

Suggested commit message:
feat({feature}): {brief description}

- Add {feature} controller and service
- Add Inertia page for {feature}
- Add tests with {N}% coverage
```
