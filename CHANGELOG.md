# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-01-03

### Added
- **Comprehensive Test Suite**: Implemented pytest-based test infrastructure with 80%+ coverage target
  - Created `pytest.ini` with test discovery patterns and async support
  - Created `.coveragerc` with detailed coverage configuration
  - Added test markers: unit, integration, slow, network, install, session, approval, cli
  - Implemented comprehensive fixtures in `conftest.py` for mocking external dependencies
  - **Test Files Created**:
    - `test_init.py` - Tests for main module including message conversion and auto-install
    - `test_session.py` - Session management tests (Session and SessionManager classes)
    - `test_approval.py` - MCP tool approval strategy tests (all strategies and factory)
    - `test_cli.py` - CLI command tests (ask, stream, session, health, benchmark, install)
    - `test_install.py` - Installation functionality tests
    - `test_wrapper.py` - Enhanced wrapper tests (caching, retry logic)
    - `test_package.py` - Package structure and export tests
  - **Testing Improvements**:
    - All external dependencies mocked (claude-code-sdk, claif.common)
    - Async test patterns for testing async operations
    - Proper temp directory handling for file-based tests
    - Mock logger to prevent test output noise
    - Created `run_tests.py` helper script for easy test execution

### Enhanced
- **Retry Logic Improvements**: Enhanced existing tenacity retry mechanism for better quota handling
  - Added `no_retry` field support in `ClaifOptions` 
  - Improved error categorization to detect quota/rate limit errors specifically
  - Enhanced error messages to indicate quota exhaustion vs other failures
  - Added --no_retry CLI flag support in `ask` command

### Changed
- Modified `wrapper.py` to check for quota-specific error indicators
- Updated retry error handling to provide clearer messages for different failure types
- Enhanced error detection for: "quota", "rate limit", "429", "exhausted"

## [1.0.11] - 2025-01-02

### Added
- **Comprehensive Test Suite**: Implemented pytest-based test infrastructure with 80%+ coverage target
  - Created `pytest.ini` with test discovery patterns and async support
  - Created `.coveragerc` with detailed coverage configuration
  - Added test markers: unit, integration, slow, network, install, session, approval, cli
  - Implemented comprehensive fixtures in `conftest.py` for mocking external dependencies
  
### Testing
- **Test Files Created**:
  - `test_init.py` - Tests for main module including message conversion and auto-install
  - `test_session.py` - Session management tests (Session and SessionManager classes)
  - `test_approval.py` - MCP tool approval strategy tests (all strategies and factory)
  - `test_cli.py` - CLI command tests (ask, stream, session, health, benchmark, install)
  - `test_install.py` - Installation functionality tests
  - `test_wrapper.py` - Enhanced wrapper tests (caching, retry logic)
  - `test_package.py` - Package structure and export tests

### Infrastructure
- **Testing Improvements**:
  - All external dependencies mocked (claude-code-sdk, claif.common)
  - Async test patterns for testing async operations
  - Proper temp directory handling for file-based tests
  - Mock logger to prevent test output noise
  - Created `run_tests.py` helper script for easy test execution

## [1.0.10] - 2025-01-02

### Added
- **Auto-Install Exception Handling**: Added automatic CLI detection and installation when claude-code tools are missing
- Added `_is_cli_missing_error()` function to detect missing CLI tool errors
- Added automatic retry logic after successful installation
- Added post-install configuration prompts with terminal opening utilities

### Changed
- **Rich Dependencies Removed**: Completely removed all rich library dependencies
- Replaced rich.console with simple print functions and loguru logging
- Simplified CLI output using `_print`, `_print_error`, `_print_success`, `_print_warning` helper functions
- Streamlined installation process integration with main claif client

### Fixed
- Fixed import issues with claif.common modules
- Resolved CLI missing error detection across different platforms
- Improved error handling during auto-install process

### Removed
- Removed all rich imports (rich.console, rich.progress, rich.table, rich.live, rich.syntax)
- Removed complex UI formatting in favor of simple, clean output

## [1.0.9] - 2025-01-02

### Changed
- Enhanced auto-install functionality with better error detection
- Improved integration with claif core install system

## [1.0.8] - 2025-01-01

### Added
- Added reference documentation file (claude-cli-usage.txt)
- Added message conversion functions to properly handle UserMessage, AssistantMessage, and SystemMessage types from claude-code-sdk
- Added proper conversion of content blocks to text for assistant messages

### Changed
- Improved message type handling with explicit conversion between claude-code-sdk and Claif message formats
- Enhanced imports to include more specific message types (AssistantMessage, ResultMessage, SystemMessage, UserMessage)
- Import organization improvements in session.py

### Fixed
- Fixed message conversion issues between claude-code-sdk and Claif formats
- Proper handling of different message content types and blocks

## [1.0.7] - 2025-01-01

[Previous version - no changelog entry]

## [1.0.6] - 2025-01-01

[Previous version - no changelog entry]

## [1.0.5] - 2025-01-01

[Previous version - no changelog entry]

## [1.0.4] - 2025-01-01

[Previous version - no changelog entry]

## [1.0.3] - 2025-01-01

[Previous version - no changelog entry]

## [1.0.2] - 2025-01-01

### Changed
- Migrated logging from `claif.common.get_logger` to direct `loguru` usage for simplified logging
- Refactored session management internal structure for better code organization
- Updated approval strategies with keyword-only arguments for better API clarity
- Improved session export functionality with cleaner implementation

### Fixed
- Fixed unused argument warnings in approval strategies by prefixing with underscore
- Addressed linting issues related to boolean positional arguments
- Resolved import organization issues

## [1.0.1] - 2025-01-01

### Fixed
- Minor bug fixes and improvements

## [1.0.0] - 2025-01-01

### Added
- Initial release of claif_cla - Claif provider for Anthropic's Claude Code CLI
- Thin wrapper around claude-code-sdk for seamless Claif integration
- Fire-based CLI with rich terminal output
- Advanced session management with persistence, branching, and merging
- Multiple MCP tool approval strategies (allow-all, deny-all, whitelist, blacklist, patterns, etc.)
- Response caching with configurable TTL to reduce API costs
- Retry logic with exponential backoff for robust operation
- Interactive mode for conversational interactions
- Health check and benchmarking commands
- Session templates for common use cases (code review, debugging, architecture, testing)
- Full async/await support for efficient concurrent operations
- Type hints throughout the codebase for better IDE support
- Comprehensive error handling with custom error types
- Export sessions to JSON or Markdown formats
- Command-line script entry point: `claif-cla`

### Infrastructure
- GitHub Actions workflows for CI/CD
- Pre-commit hooks configuration
- Pytest-based test framework setup
- Hatch-based build system with VCS versioning
- Ruff for linting and formatting
- MyPy for type checking
- Coverage reporting configuration
- Python 3.10+ support

### Documentation
- Comprehensive README with installation, usage, and API documentation
- AGENTS.md with Claif development guidelines
- CLAUDE.md with project instructions
- Inline docstrings for all public APIs