# Contributing to NilAI

Thank you for your interest in contributing to NilAI! This document provides guidelines and workflows for contributing to the project.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Commit Message Guidelines](#commit-message-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Testing Requirements](#testing-requirements)
8. [Release Process](#release-process)
9. [Getting Help](#getting-help)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** (required)
- **uv** (Astral's package manager) - [Installation Guide](https://github.com/astral-sh/uv)
- **Docker & Docker Compose** (for running services locally)
- **Git** (for version control)
- **Make** (for running development commands)

### Quick Links

- **Code Style Guide:** [CODESTYLE.md](./CODESTYLE.md)
- **Security Guidelines:** [SECURITY.md](./SECURITY.md)
- **Project Plan:** [PLAN.md](./PLAN.md)

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/nilAI.git
cd nilAI
```

### 2. One-Command Setup

```bash
# Install dependencies and set up pre-commit hooks
make setup
```

This command will:
- Install all Python dependencies with `uv sync`
- Install pre-commit hooks
- Display next steps

### 3. Configure Environment

```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env with your configuration
# Required variables:
#   - DATABASE_URL
#   - REDIS_URL
#   - HF_TOKEN (for model downloads)
#   - BRAVE_SEARCH_API (for web search feature)
```

### 4. Run Database Migrations

```bash
make migration-upgrade
```

### 5. Verify Setup

```bash
# Run all checks to verify everything works
make ci
```

If all checks pass, you're ready to contribute! 🎉

---

## Development Workflow

### Daily Development Commands

```bash
# Start development server (auto-reload on changes)
make serve

# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run unit tests
make test-unit

# Run all tests
make test

# Run all CI checks locally
make ci
```

### Full Command Reference

Run `make help` to see all available commands:

```bash
$ make help

NilAI Development Commands

Usage:
  make <target>

General
  help                  Display this help message

Setup & Installation
  setup                 Complete project setup (install deps + pre-commit)
  install               Install all dependencies using uv
  pre-commit-install    Install pre-commit hooks

Code Quality
  format                Format code with ruff
  lint                  Lint code with ruff
  typecheck             Run type checking with pyright

Testing
  test                  Run all tests (unit + integration)
  test-unit             Run unit tests only
  test-integration      Run integration tests only
  test-e2e              Run end-to-end tests (requires GPU)
  test-cov              Run tests with coverage report
  bench                 Run performance benchmarks

Security
  audit                 Run all security audits
  audit-deps            Audit dependencies for vulnerabilities
  audit-code            Audit code for security issues

Database
  migration-create      Create a new database migration
  migration-upgrade     Upgrade database to latest migration
  migration-downgrade   Downgrade database by one migration

Development
  serve                 Start the FastAPI development server
  serve-prod            Start production server with gunicorn

Docker
  docker-build          Build all Docker images
  docker-up             Start all services with docker-compose
  docker-down           Stop all services

CI/CD
  ci                    Run all CI checks locally
  ci-full               Run complete CI pipeline

Cleanup
  clean                 Clean generated files and caches
  clean-all             Clean everything including .venv
```

---

## Code Standards

### Code Quality Requirements

All contributions must meet these standards:

1. **✅ Formatting:** Code must be formatted with `ruff format`
2. **✅ Linting:** No linting errors from `ruff check`
3. **✅ Type Checking:** No type errors from `pyright` (standard mode)
4. **✅ Tests:** All tests must pass (`make test`)
5. **✅ Coverage:** Changed code should have ≥80% test coverage
6. **✅ Security:** No high/critical vulnerabilities from `bandit` or `pip-audit`

### Pre-commit Hooks

Pre-commit hooks automatically run when you commit:

```bash
# Install hooks (done by make setup)
make pre-commit-install

# Run hooks manually on all files
make pre-commit-run
```

The hooks will:
- Format code with ruff
- Check for common issues
- Detect secrets in code
- Validate YAML, JSON, and TOML files

If hooks fail, fix the issues and commit again.

---

## Commit Message Guidelines

We follow **Conventional Commits** for clear, semantic commit messages.

### Commit Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation changes
- **style:** Code style changes (formatting, no logic changes)
- **refactor:** Code refactoring (no functionality change)
- **perf:** Performance improvements
- **test:** Adding or updating tests
- **chore:** Maintenance tasks (dependencies, tooling)
- **ci:** CI/CD pipeline changes

### Scopes (optional but recommended)

- `api` - FastAPI application changes
- `models` - Model daemon or vLLM integration
- `common` - Shared types and utilities
- `client` - Python SDK client
- `auth` - Authentication logic
- `db` - Database models or migrations
- `docs` - Documentation
- `ci` - CI/CD workflows

### Examples

#### ✅ Good Commit Messages

```
feat(api): add /v1/healthz and /v1/readyz endpoints

Implements health check endpoints for Kubernetes readiness and
liveness probes. /healthz returns 200 immediately, /readyz checks
vLLM engine availability.

Closes #123
```

```
fix(auth): handle expired NUC tokens gracefully

Previously, expired tokens caused 500 errors. Now returns 401
with clear error message.
```

```
refactor(api): extract validation logic to middleware

Moves request size and timeout validation to dedicated middleware
for better separation of concerns.
```

```
docs: update CONTRIBUTING.md with commit guidelines
```

```
chore(deps): upgrade ruff to v0.11.7

Updates ruff for improved performance and new linting rules.
```

#### ❌ Bad Commit Messages

```
fixed stuff
```

```
WIP
```

```
Update code
```

```
asdfasdf
```

### Commit Size

- **Prefer small, focused commits** - One logical change per commit
- **Each commit should be buildable** - Don't break the build mid-PR
- **Use fixup commits during review** - Squash before merging

---

## Pull Request Process

### Before Creating a PR

1. **Sync with main branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all CI checks**
   ```bash
   make ci-full
   ```

3. **Update documentation** if needed
   - Update README.md if adding user-facing features
   - Add docstrings to new functions
   - Update API documentation

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push -u origin feature/your-feature-name
   ```

2. **Open a PR on GitHub** with:
   - **Clear title** following Conventional Commits format
   - **Description** explaining what and why
   - **Test plan** describing how you tested the changes
   - **Screenshots/videos** if applicable (UI changes)
   - **Breaking changes** clearly documented

### PR Template

```markdown
## Summary
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Test Plan
How did you test this?

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Tested on GPU (if applicable)

## Breaking Changes
List any breaking changes and migration steps

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
```

### PR Review Process

1. **Automated Checks** run on every PR:
   - Formatting (ruff)
   - Linting (ruff)
   - Type checking (pyright)
   - Unit tests
   - Integration tests
   - Security audit
   - E2E tests (GPU runner)

2. **Code Review** by maintainers:
   - At least one approval required
   - Address all review comments
   - Re-request review after changes

3. **Merge Requirements:**
   - ✅ All CI checks pass
   - ✅ At least 1 approval
   - ✅ No merge conflicts
   - ✅ Branch is up to date with main

### After PR is Merged

1. **Delete your branch**
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**
   ```bash
   git checkout main
   git pull origin main
   ```

---

## Testing Requirements

### Test Coverage Expectations

- **New features:** 100% coverage of new code
- **Bug fixes:** Add regression test
- **Refactoring:** Maintain existing coverage
- **Overall project:** ≥80% coverage

### Test Types

#### Unit Tests (Fast, Isolated)
```python
# tests/unit/nilai_api/test_validation.py
def test_validate_temperature():
    """Test temperature validation rejects invalid values."""
    with pytest.raises(ValueError):
        validate_temperature(3.0)  # Too high
```

Run: `make test-unit`

#### Integration Tests (Database, Redis)
```python
# tests/integration/test_users_db.py
@pytest.mark.asyncio
async def test_create_user_in_db(db_session):
    """Test user creation in real database."""
    user = await create_user(db_session, "test@example.com")
    assert user.user_id is not None
```

Run: `make test-integration`

#### E2E Tests (Full Stack, GPU)
```python
# tests/e2e/test_chat_completions.py
@pytest.mark.e2e
async def test_chat_completion_with_real_model(test_client):
    """Test chat completion with actual vLLM model."""
    response = await test_client.post("/v1/chat/completions", json={
        "model": "llama-3.2-1b",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code == 200
```

Run: `make test-e2e` (requires GPU)

### Running Tests

```bash
# Run specific test file
uv run pytest tests/unit/nilai_api/test_app.py -v

# Run specific test function
uv run pytest tests/unit/nilai_api/test_app.py::test_cors_config -v

# Run with coverage
make test-cov

# Run only fast tests (skip GPU tests)
uv run pytest -m "not gpu and not slow"
```

---

## Release Process

### Versioning

We use **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Release Checklist

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Create release branch**
   ```bash
   git checkout -b release/v0.2.0
   ```
4. **Run full test suite**
   ```bash
   make ci-full
   ```
5. **Create PR** to main branch
6. **After merge, create GitHub release**
   - Tag: `v0.2.0`
   - Title: `v0.2.0 - Feature Release`
   - Description: Copy from CHANGELOG.md
7. **CI/CD automatically publishes** Docker images to ECR

---

## Getting Help

### Communication Channels

- **GitHub Issues:** Bug reports and feature requests
- **GitHub Discussions:** Questions and general discussion
- **Pull Request Comments:** Code review discussions

### Reporting Issues

When reporting bugs, include:

1. **Environment:**
   - Python version
   - OS and version
   - GPU info (if applicable)

2. **Steps to reproduce**

3. **Expected vs actual behavior**

4. **Error messages and logs**

5. **Minimal reproducible example**

### Asking Questions

Before asking:
1. Check existing issues and discussions
2. Read the documentation
3. Search the codebase

When asking:
- Be specific
- Provide context
- Show what you've tried

---

## Code of Conduct

### Our Standards

- **Be respectful** and professional
- **Be constructive** in feedback
- **Be collaborative** and open to ideas
- **Be inclusive** and welcoming

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Spam or off-topic content
- Publishing others' private information

### Enforcement

Violations will be addressed by project maintainers. Serious or repeated violations may result in a ban from the project.

---

## License

By contributing to NilAI, you agree that your contributions will be licensed under the Apache 2.0 License.

---

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes (for significant contributions)
- Project README (for major features)

Thank you for contributing to NilAI! 🚀

---

**Last Updated:** 2025-11-05
**Version:** 1.0
