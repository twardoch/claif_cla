# claif_cla TODO List

## Essential MVP Tasks

### Core Functionality
- [ ] Add proper error handling for missing API keys
- [ ] Implement async cleanup in wrapper (replace time.sleep with asyncio.sleep)
- [ ] Add timeout handling for long-running queries
- [ ] Validate claude-code-sdk options before passing through

### Auto-Install Support (Issue #201) - ✅ COMPLETED
- [x] Implement auto-install of claude-code-sdk when missing
- [x] Add CLI detection and installation prompts
- [x] Integrate with bun bundling for offline installation
- [x] Wire existing install commands as exception handlers
- [x] Add post-install configuration prompts with terminal opening

### Rich Dependencies - ✅ COMPLETED
- [x] Remove all rich dependencies from CLI
- [x] Replace rich.console with loguru logging
- [x] Simplify progress indicators and output formatting
- [x] Use plain text output with clear formatting

### Testing
- [ ] Create integration tests with mocked Claude responses
- [ ] Add unit tests for all modules
- [ ] Test CLI entry point installation
- [ ] Add --version flag for CLI

### Documentation
- [ ] Add troubleshooting guide
- [ ] Document all CLI commands with examples
- [ ] Create getting started guide

## Known Issues
- [ ] Session timestamps may lack timezone info
- [ ] Cache directory creation could fail silently
- [ ] No validation for claude-code-sdk responses

## Technical Debt
- [ ] Improve error messages with actionable suggestions
- [ ] Add more specific exception types
- [ ] Consider using pathlib throughout instead of string paths

## Contributing Guidelines

- [ ] Create CONTRIBUTING.md
- [ ] Set up issue templates
- [ ] Create PR template
- [ ] Define code review process

## Notes

- Focus on stability and reliability for v1.x releases
- Keep the wrapper thin and maintainable
- Prioritize developer experience
- Test thoroughly with real claude-code-sdk before each release