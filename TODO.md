# claif_cla TODO List

## Immediate Tasks (v1.1)

### 🔴 Critical Bugs
- [ ] Add proper error handling for missing API keys
- [ ] Implement async cleanup in wrapper (replace time.sleep with asyncio.sleep)
- [ ] Add timeout handling for long-running queries
- [ ] Validate claude-code-sdk options before passing through

### 🟡 Essential Features
- [ ] Create integration tests with mocked Claude responses  
- [ ] Add unit tests for all modules (current coverage ~0%)
- [ ] Test CLI entry point installation
- [ ] Add --version flag for CLI
- [ ] Create minimal working examples in docs/

### 🟢 Documentation
- [ ] Add troubleshooting guide
- [ ] Document all CLI commands with examples
- [ ] Create getting started guide
- [ ] Add API reference documentation

## Near-term Improvements (v1.2)

### Features
- [ ] Session search functionality
- [ ] Session tags and metadata
- [ ] Progress indicators for long operations
- [ ] Debug logging mode
- [ ] Performance benchmarks

### Code Quality
- [ ] Improve error messages with actionable suggestions
- [ ] Add more specific exception types
- [ ] Profile memory usage for large sessions
- [ ] Optimize session loading performance

## Known Issues

### High Priority
- [ ] Session timestamps may lack timezone info in some cases
- [ ] Cache directory creation could fail silently
- [ ] No validation for claude-code-sdk responses

### Medium Priority  
- [ ] Some imports could be optimized
- [ ] Consider using pathlib throughout instead of string paths
- [ ] Standardize logging format across modules

## Technical Debt

1. **Testing**: Minimal test coverage - need comprehensive test suite
2. **Error Handling**: Some generic exception catching should be more specific
3. **Type Safety**: Some dict parameters could use TypedDict for better typing

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