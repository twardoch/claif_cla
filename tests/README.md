# claif_cla Test Suite

This directory contains the comprehensive test suite for the claif_cla package.

## Test Structure

- `conftest.py` - Shared fixtures and mocks for all tests
- `test_init.py` - Tests for the main module (message conversion, auto-install)
- `test_session.py` - Session management tests
- `test_approval.py` - MCP tool approval strategy tests
- `test_cli.py` - CLI functionality tests
- `test_install.py` - Installation functionality tests
- `test_wrapper.py` - Enhanced wrapper tests (caching, retry)
- `test_package.py` - Package structure tests

## Running Tests

### Basic test run:
```bash
pytest
```

### With coverage:
```bash
pytest --cov=claif_cla --cov-report=term-missing
```

### Run specific test file:
```bash
pytest tests/test_session.py
```

### Run tests with specific marker:
```bash
pytest -m unit  # Run only unit tests
pytest -m "not slow"  # Skip slow tests
```

### Using the helper script:
```bash
python run_tests.py  # Basic run
python run_tests.py --coverage  # With coverage
python run_tests.py tests/test_cli.py  # Specific file
```

## Test Markers

- `unit` - Unit tests that don't require external dependencies
- `integration` - Integration tests that may use real APIs
- `slow` - Tests that take longer than usual
- `network` - Tests that require network access
- `install` - Tests related to installation functionality
- `session` - Tests for session management
- `approval` - Tests for approval strategies
- `cli` - Tests for CLI functionality

## Mocking Strategy

All external dependencies are mocked:
- `claude-code-sdk` - Mocked in conftest.py
- `claif.common` - Mocked when not available
- File system operations - Use temp directories
- Async operations - Use AsyncMock
- Subprocess calls - Mocked for install tests

## Coverage Goals

Target: 80%+ coverage across all modules

Current focus areas:
- Core functionality (query, message conversion)
- Session management
- Approval strategies
- CLI commands
- Installation logic