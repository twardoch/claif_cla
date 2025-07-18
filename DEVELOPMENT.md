# Development Guide

This guide covers the development workflow for the claif_cla package.

## Quick Start

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Run tests:**
   ```bash
   make test
   ```

3. **Build package:**
   ```bash
   make build
   ```

## Development Scripts

### Build Script (`scripts/build.sh`)

Comprehensive build script with quality checks:

```bash
./scripts/build.sh                 # Full build with all checks
./scripts/build.sh --skip-tests    # Skip tests
./scripts/build.sh --skip-quality  # Skip quality checks
./scripts/build.sh --skip-verify   # Skip package verification
```

### Test Script (`scripts/test.sh`)

Flexible test runner:

```bash
./scripts/test.sh                  # Run all tests
./scripts/test.sh --unit           # Unit tests only
./scripts/test.sh --integration    # Integration tests only
./scripts/test.sh --coverage       # Tests with coverage
./scripts/test.sh --parallel       # Parallel execution
./scripts/test.sh --watch          # Watch mode
./scripts/test.sh --marker slow    # Run tests with specific marker
```

### Release Script (`scripts/release.sh`)

Automated release management:

```bash
./scripts/release.sh suggest       # Show version suggestions
./scripts/release.sh check         # Pre-release checks
./scripts/release.sh release 1.0.30 # Create release
./scripts/release.sh tags          # List recent tags
```

## Makefile Commands

### Setup
- `make install` - Install dependencies and setup environment
- `make dev-setup` - Complete development setup with pre-commit hooks

### Testing
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-coverage` - Run tests with coverage report
- `make test-parallel` - Run tests in parallel
- `make test-watch` - Watch for changes and re-run tests

### Code Quality
- `make format` - Format code with ruff
- `make lint` - Run linting with ruff
- `make type-check` - Run type checking with mypy
- `make quality` - Run all quality checks
- `make fix` - Auto-fix code issues

### Build & Release
- `make build` - Build the package
- `make verify` - Verify the built package
- `make check-release` - Run pre-release checks
- `make release VERSION=1.0.30` - Create a new release

### Utilities
- `make clean` - Clean build artifacts
- `make version` - Show current version
- `make suggest-version` - Show suggested next version

## Version Management

The project uses git-tag-based semantic versioning:

1. **Current version** is automatically derived from git tags
2. **Development versions** include commit hash (e.g., `1.0.30.dev10+ge27bb8f`)
3. **Release versions** match git tags (e.g., `v1.0.30`)

### Creating a Release

```bash
# Check current status
make check-release

# See version suggestions
make suggest-version

# Create release
make release VERSION=1.0.30
```

This will:
1. Run pre-release checks
2. Create and push git tag
3. Trigger GitHub Actions for PyPI publication

## GitHub Actions CI/CD

The CI/CD pipeline includes:

### Code Quality
- Ruff formatting and linting
- MyPy type checking
- Security scanning with Bandit

### Testing
- Cross-platform testing (Linux, Windows, macOS)
- Multi-version Python support (3.10, 3.11, 3.12)
- Coverage reporting

### Build & Release
- Package building and verification
- Binary compilation for multiple platforms
- Docker image building
- TestPyPI and PyPI publication
- GitHub release creation

## Testing Strategy

### Test Categories

Tests are organized by markers:
- `unit` - Unit tests for individual components
- `integration` - Integration tests with external dependencies
- `benchmark` - Performance benchmarks

### Running Specific Tests

```bash
# Run by marker
pytest -m unit
pytest -m integration
pytest -m benchmark

# Run specific test file
pytest tests/test_session.py -v

# Run with coverage
pytest --cov=src/claif_cla --cov-report=html
```

### Test Structure

```
tests/
├── test_approval.py      # Approval strategy tests
├── test_cli.py           # CLI interface tests
├── test_client.py        # Client functionality tests
├── test_session.py       # Session management tests
├── test_wrapper.py       # Wrapper functionality tests
└── conftest.py          # Test fixtures and configuration
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone https://github.com/twardoch/claif_cla.git
cd claif_cla

# Setup development environment
make dev-setup

# Activate virtual environment
source .venv/bin/activate
```

### 2. Make Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Run tests
make test

# Run quality checks
make quality

# Fix formatting issues
make fix
```

### 3. Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

```bash
# Install hooks (done by make dev-setup)
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### 4. Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Watch mode for development
make test-watch
```

### 5. Build and Verify

```bash
# Build package
make build

# Verify package works
make verify
```

### 6. Release

```bash
# Check release readiness
make check-release

# Create release
make release VERSION=1.0.30
```

## Docker Support

### Build Docker Image

```bash
make docker-build
```

### Test in Docker

```bash
make docker-test
```

### Run in Docker

```bash
make docker-run
```

## IDE Integration

### VS Code

Recommended extensions:
- Python
- Ruff
- MyPy
- GitLens

### PyCharm

Enable:
- Ruff for formatting/linting
- MyPy for type checking
- Pre-commit integration

## Troubleshooting

### Common Issues

1. **Tests failing**: Check if dependencies are installed with `make install`
2. **Build issues**: Clean artifacts with `make clean` and rebuild
3. **Pre-commit failures**: Run `make fix` to auto-fix issues
4. **Version issues**: Check git tags with `git tag -l`

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s --tb=long

# Run with pdb on failure
pytest --pdb

# Run specific test with debugging
pytest tests/test_session.py::test_specific_function -v -s
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the development workflow
4. Ensure all tests pass
5. Submit a pull request

## Resources

- [Project Repository](https://github.com/twardoch/claif_cla)
- [PyPI Package](https://pypi.org/project/claif_cla/)
- [Documentation](https://github.com/twardoch/claif_cla#readme)
- [Issue Tracker](https://github.com/twardoch/claif_cla/issues)