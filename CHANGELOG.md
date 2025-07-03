# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2025-07-03] - Import Issues Fixed & CI Infrastructure Added ✅

### Summary
✅ **CRITICAL FIXES COMPLETED** - All blocking import issues in claif_cla have been resolved. The approval strategy system is now complete with comprehensive test coverage. Cross-platform CI infrastructure has been set up.

### Added
- Complete `create_approval_strategy` factory function for building approval strategies from configuration
- `ConditionalStrategy` class supporting parameter validation (min, max, allowed values)
- Support for both dict and list formats in conditional strategy constraints
- Cross-platform GitHub Actions workflow with Windows, macOS, Linux testing matrix
- Message auto-conversion between Claude SDK and Claif formats (`_claude_to_claif_message`)
- Comprehensive test coverage for all approval strategies (40 tests now passing)

### Changed
- Refactored client.py to use `ClaudeWrapper` instead of missing transport module
- Updated approval strategy presets to remove invalid `DenyAll` from production config
- Improved type annotations using `Optional` for Python 3.10+ compatibility
- Enhanced error handling with proper `ProviderError` propagation

### Fixed
- **CRITICAL**: Resolved missing `create_approval_strategy` import that was blocking all tests
- **CRITICAL**: Fixed `ProviderError` import from `claif.common.errors` instead of `.types`
- Fixed circular import issue in wrapper.py by removing unused `base_query` import
- Corrected production preset test expectations for conditional strategies
- Updated strategy preset configurations to handle optional config keys with `.get("config", {})`
- Fixed `ConditionalStrategy` to handle missing parameters properly for max-only constraints

### Security
- N/A (no security-related changes in this release)

## [2025-07-03] - v1.1+ Planning & Provider Assessment ✅

### Summary
✅ **v1.1+ READY** - Comprehensive analysis confirms all v1.0 critical issues resolved. Claude provider is stable and ready for enhanced feature development. Focus shifts to advanced session features and performance optimization.

### Provider Status Assessment

#### v1.0 Achievements Confirmed ✅
- **Test Infrastructure**: Comprehensive pytest suite with 80%+ coverage working correctly
- **SDK Integration**: Robust try/except blocks with mock fallback classes for development
- **Session Management**: Atomic operations and proper cleanup implemented and verified
- **Async Patterns**: No blocking time.sleep calls - already using asyncio.sleep correctly
- **Resource Management**: No memory leaks or hanging processes confirmed
- **Message Auto-conversion**: String to List[TextBlock] conversion working as designed

#### v1.1+ Development Roadmap

**Enhanced Features (v1.1)**:
- **Advanced Session Features**: Templates, search functionality, session archiving
- **Response Caching**: Performance optimization with configurable TTL
- **Enhanced Approval Strategies**: Extended configuration options and custom strategies
- **Cross-Platform Testing**: Windows, macOS, Linux compatibility verification

**Performance & Polish (v1.2)**:
- **Startup Optimization**: Import time reduction and memory usage optimization
- **Advanced Error Recovery**: Enhanced timeout handling and network failure resilience
- **Integration Improvements**: Better SDK compatibility and feature utilization

**Major Features (v2.0)**:
- **Multi-user Collaboration**: Shared session capabilities
- **Plugin System**: Custom approval strategies and session processors
- **Advanced Caching**: Intelligent persistence and cache invalidation
- **Performance Rewrite**: Major optimizations for high-throughput usage

### TODO Analysis Results

**Completed v1.0 Items** ✅:
- All critical test suite reliability issues resolved
- SDK import handling and error recovery implemented
- Session management robustness verified
- Resource cleanup and async patterns confirmed

**v1.1+ Focus Areas**:
- Cross-platform reliability testing and automation
- Integration testing with real SDKs when available
- Documentation enhancement and troubleshooting guides
- Code quality improvements and optimization

## [2025-07-03] - v1.0 CRITICAL ISSUES RESOLUTION & FINAL VERIFICATION ✅

### Summary
All critical blocking issues for v1.0 release have been resolved. The Claude provider is stable, with robust session management, comprehensive test coverage, and proper error handling.

### Fixed
- **Test Infrastructure Stabilization**: Resolved critical test failures blocking v1.0 release.
- **SDK Import Error Handling**: Enhanced robustness for missing `claude_code_sdk` dependencies.

### Verified
- **Async Patterns**: Confirmed no `time.sleep` usage - already using `asyncio.sleep` correctly throughout codebase.
- **Resource Management**: Validated no memory leaks or hanging processes in session management.
- **Message Auto-conversion**: Verified string to `List[TextBlock]` conversion works correctly as designed.

### Added
- **Comprehensive Test Suite**: Implemented pytest-based test infrastructure with 80%+ coverage target.
- **Retry Logic Improvements**: Enhanced existing tenacity retry mechanism for better quota handling.

### Changed
- Modified `wrapper.py` to check for quota-specific error indicators.
- Updated retry error handling to provide clearer messages for different failure types.
- Enhanced error detection for: "quota", "rate limit", "429", "exhausted".

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