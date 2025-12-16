# Code Style Guide

**Project**: Litestar Fullstack Inertia
**Status**: Active

## Python Style

We use **Ruff** for linting and formatting, and **Mypy** + **Pyright** for static type checking.

### Key Rules

- **Line Length**: 120 characters
- **Quotes**: Double quotes
- **Type Hints**: strict usage
  - Use `T | None` (PEP 604) instead of `Optional[T]`.
  - **NO** `from __future__ import annotations`.
  - Built-in generics (`list[str]`, `dict[str, Any]`) instead of `typing.List`, `typing.Dict`.
- **Docstrings**: Google Style.
- **Imports**: Sorted by Ruff (isort compatible).

### Tools

- `ruff check`: Linting (fix with `--fix`)
- `ruff format`: Formatting
- `mypy`: Type checking
- `pyright`: Type checking
- `slotscheck`: Validates `__slots__` usage

## TypeScript / Frontend Style

We use **Biome** for linting and formatting.

### Key Rules

- **Indent**: Tab (width 2)
- **Line Length**: 180 characters
- **Quotes**: Double quotes
- **Semicolons**: As needed
- **Imports**: Organized by Biome

### Tools

- `npx biome check resources/`: Linting and formatting check
- `npx biome check --write resources/`: Fix issues

## Pre-Commit Hooks

We use `pre-commit` to enforce these standards. Run `make lint` to execute all checks.
