# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Environment Setup
```bash
make install          # Install project dependencies and setup environment
uv sync --all-extras --dev  # Alternative dependency installation
```

### Running the Application
```bash
uv run app run         # Start the Litestar application server
make start-infra       # Start local Docker containers (PostgreSQL, Redis)
make stop-infra        # Stop local Docker containers
```

### Frontend Development
```bash
npm run dev           # Start Vite development server for React frontend
npm run build         # Build frontend assets for production
npm run watch         # Watch mode for frontend builds
```

### Testing & Quality Assurance
```bash
make test             # Run pytest test suite
make test-all         # Run all tests including marked tests
make coverage         # Run tests with coverage reporting
make lint             # Run all linting (pre-commit, type-check, slotscheck)
make pre-commit       # Run pre-commit hooks (ruff, codespell)
make type-check       # Run mypy and pyright type checking
```

### Database Operations
```bash
uv run app database upgrade        # Apply database migrations
uv run app database make-migrations # Create new migration
uv run app database downgrade      # Rollback database migrations
```

### Background Workers
```bash
uv run app worker run             # Start SAQ background workers
```

### Documentation
```bash
make docs             # Build Sphinx documentation
make docs-serve       # Serve docs locally with auto-reload
```

## Project Architecture

This is a modern Litestar fullstack application built with **Inertia.js**, **React**, and **shadcn/ui**, providing a seamless SPA experience without API endpoints.

### Core Litestar Stack
- **Litestar SAQ**: Background job processing with Redis queue integration (`litestar-saq` plugin)
- **Litestar Granian**: High-performance ASGI server with HTTP/2 support (`litestar-granian` plugin)
- **Litestar Vite**: Frontend asset bundling with hot module replacement (`litestar-vite` plugin)
- **Litestar Inertia**: Server-side rendering with SPA navigation (via `litestar-vite.inertia`)

### Backend Architecture (Python/Litestar)
- **Domain-Driven Design**: Business logic organized in `app/domain/` with separate modules for accounts, teams, tags, and web
- **Plugin-Based Configuration**: Core functionality configured through `ApplicationCore` plugin in `app/server/core.py`
- **Repository Pattern**: Data access abstracted through services and repositories
- **Database**: SQLAlchemy 2.0 with Alembic migrations, supports PostgreSQL
- **Background Jobs**: Litestar SAQ integration with Redis backend for async task processing
- **ASGI Server**: Litestar Granian for production-grade HTTP/1.1 and HTTP/2 support
- **Authentication**: Session-based auth with OAuth2 support (Google, GitHub)
- **Caching**: Redis-backed response caching and session storage

### Frontend Architecture (TypeScript/React + Inertia.js)
- **Inertia.js Integration**: Server-side rendering without traditional API endpoints - pages are React components rendered server-side
- **React 18**: Modern React with TypeScript for component development
- **shadcn/ui**: Comprehensive UI component library built on Radix UI primitives
- **Litestar Vite Plugin**: Seamless asset bundling with HMR, handles React JSX compilation and CSS processing
- **Tailwind CSS**: Utility-first CSS framework with custom design system
- **Resources Directory**: Frontend code in `resources/` with components, layouts, pages structure matching Inertia.js conventions

### Key Configuration Files
- `app/config/_app.py`: Core Litestar plugin configurations (SAQ, Vite, Granian, Inertia)
- `app/server/core.py`: Main application plugin with routes and middleware setup
- `vite.config.ts`: Litestar-Vite plugin configuration with React and Inertia.js setup
- `pyproject.toml`: Python dependencies including all Litestar plugins
- `Makefile`: Development workflow automation
- `components.json`: shadcn/ui component configuration and aliases

### Domain Structure
- `app/domain/accounts/`: User management, authentication, profiles
- `app/domain/teams/`: Multi-tenant team functionality with invitations and roles
- `app/domain/tags/`: Tagging system for resources
- `app/domain/web/`: Inertia.js page controllers and compiled Vite assets

### Environment Configuration
- Copy `.env.local.example` to `.env` for local development
- Database runs on port 15432, Redis on 16379 in development
- Litestar-Vite dev server runs on port 5173, Litestar+Granian API on port 8089
- Inertia.js automatically handles page routing between frontend and backend

## Development Workflow

1. **Environment Setup**: `make install` followed by `. .venv/bin/activate`
2. **Infrastructure**: `make start-infra` to start databases
3. **Database**: `uv run app database upgrade` to apply migrations
4. **Development**: `uv run app run` starts Litestar+Granian server with integrated Vite dev server
5. **Testing**: `make test` and `make lint` before committing changes

## Inertia.js Development Notes

- Pages are React components in `resources/pages/` that receive props from Litestar controllers
- No API endpoints needed - data flows directly from Python controllers to React components
- Use Inertia's `router.visit()` for navigation instead of traditional HTTP requests
- Form submissions handled through Inertia's form helpers with CSRF protection
- Shared data (like user info) configured in Inertia plugin settings

## Testing Strategy

- Unit tests in `tests/unit/` for business logic and utilities
- Integration tests in `tests/integration/` for API endpoints and database operations
- Use pytest with asyncio support for async operations
- Test databases isolated using pytest-databases plugin
