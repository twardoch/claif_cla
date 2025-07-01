# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-01

### Added
- Initial release of claif_cla - CLAIF provider for Anthropic's Claude Code CLI
- Thin wrapper around claude-code-sdk for seamless CLAIF integration
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
- AGENTS.md with CLAIF development guidelines
- CLAUDE.md with project instructions
- Inline docstrings for all public APIs