<!-- markdownlint-disable -->
<p align="center">
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Light.svg#gh-light-mode-only" alt="Litestar Logo - Light" width="100%" height="auto" />
  <img src="https://raw.githubusercontent.com/litestar-org/branding/1dc4635b192d29d864fcee6f3f73ea0ff6fecf10/assets/Branding%20-%20SVG%20-%20Transparent/Fullstack%20-%20Banner%20-%20Inline%20-%20Dark.svg#gh-dark-mode-only" alt="Litestar Logo - Dark" width="100%" height="auto" />
</p>
<!-- markdownlint-restore -->

<div align="center">

[![Tests and Linting](https://github.com/litestar-org/litestar-fullstack-inertia/actions/workflows/ci.yaml/badge.svg)](https://github.com/litestar-org/litestar-fullstack-inertia/actions/workflows/ci.yaml)
[![Documentation Building](https://github.com/litestar-org/litestar-fullstack-inertia/actions/workflows/docs.yaml/badge.svg)](https://github.com/litestar-org/litestar-fullstack-inertia/actions/workflows/docs.yaml)
[![License - MIT](https://img.shields.io/badge/license-MIT-202235.svg?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://spdx.org/licenses/)
[![Litestar Framework](https://img.shields.io/badge/Litestar-Framework-202235?logo=python&labelColor=202235&color=edb641&logoColor=edb641)](https://litestar.dev)

</div>

# Litestar Fullstack Inertia

A modern, production-ready fullstack reference application. It seamlessly integrates a **Litestar** (Python) backend with a **React 19** (TypeScript) frontend using **Inertia.js 3**—eliminating the complexity of building separate APIs and SPAs.

## 🚀 Overview

This project serves as a comprehensive template for building scalable web applications. It comes pre-configured with best practices for authentication, database management, and deployment.

### Features

- **Authentication** — Email/password login, registration, password reset
- **OAuth** — Sign in with GitHub or Google
- **MFA** — TOTP-based two-factor authentication
- **Email Verification** — Configurable verification flow
- **Teams** — Multi-tenant workspaces with invitations and member roles
- **User Profiles** — Avatar uploads, connected accounts management
- **Admin Panel** — Superuser management for users and teams
- **Role-Based Access** — Granular permission system

### Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | [Litestar](https://litestar.dev/) | High-performance ASGI framework. |
| **Frontend** | [React 19](https://react.dev/) | UI library with TypeScript. |
| **Glue** | [Inertia.js 3](https://inertiajs.com/) | Classic server-driven routing for SPAs. |
| **Database** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Modern async ORM. |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS framework. |
| **UI Kit** | [shadcn/ui](https://ui.shadcn.com/) | Reusable components built with Radix UI. |
| **Tooling** | [uv](https://github.com/astral-sh/uv) | Extremely fast Python package manager. |

---

## 🛠️ Setup

**Prerequisites:**

- Python 3.12+
- Node.js & npm (or Bun)
- Docker & Docker Compose
- `uv` (Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Step-by-Step Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/litestar-org/litestar-fullstack-inertia.git
    cd litestar-fullstack-inertia
    ```

2. **Install Dependencies**
    This installs both Python (virtualenv) and JavaScript dependencies.

    ```bash
    make install
    ```

3. **Configure Environment**
    Create the environment file from the example.

    ```bash
    cp .env.local.example .env
    ```

4. **Start Infrastructure**
    Spin up the local PostgreSQL container used for development.

    ```bash
    make start-infra
    ```

5. **Run Migrations & Seed Data**
    Apply database schema and create default roles.

    ```bash
    uv run app database upgrade
    uv run app users create-roles
    ```

6. **Run the Application**
    Start the development server (Backend + Vite HMR).

    ```bash
    uv run app run --reload
    ```

**Measurable Outcome:**
> You should be able to access the application at **[http://localhost:8000](http://localhost:8000)**.
> The API docs are available at **[http://localhost:8000/schema](http://localhost:8000/schema)**.

---

## 💻 Usage & Development

We use `make` to manage common development tasks.

### Running Tests

Execute the full test suite (unit + integration).

```bash
make test
```

**Outcome:** All tests passed with a summary report.

### Code Quality (Linting & Formatting)

Run all linters (Ruff, Mypy, Biome, Slotscheck).

```bash
make lint
```

**Outcome:** Zero errors reported. Code is formatted and type-checked.

### Documentation

Build and serve the documentation locally.

```bash
make docs-serve
```

**Outcome:** Documentation running at `http://localhost:8002`.

### Database Management

The application CLI handles database operations.

```bash
uv run app database --help
# Examples:
uv run app database make-migrations -m "add_user_field"  # Create migration
uv run app database upgrade                              # Apply migrations
```

---

## 📂 Project Structure

```text
├── app/                  # Python Backend
│   ├── domain/           # Feature modules (accounts, teams, web)
│   ├── db/               # Models & Migrations
│   ├── server/           # App configuration & plugins
│   └── lib/              # Shared utilities
├── resources/            # Frontend Assets
│   ├── pages/            # Inertia Pages
│   ├── components/       # React Components (shadcn/ui)
│   └── layouts/          # Page Layouts
├── specs/                # Project Specifications & Guides
└── tests/                # Pytest Suite
```

---

## 🤝 Contribution

We welcome contributions! Please follow these steps:

1. **Fork & Clone** the repository.
2. **Install** dependencies using `make install`.
3. **Branch** off `main` for your feature/fix.
4. **Implement** your changes.
5. **Verify** with `make test` and `make lint`.
6. **Submit** a Pull Request.

**Note:** This project uses [Conventional Commits](https://www.conventionalcommits.org/).

For more details, see [CONTRIBUTING.rst](CONTRIBUTING.rst).
