# claif_cla TODO List

## Immediate Tasks (Before 1.0.0 Release)

### 🔴 Critical
- [x] Fix test_version by exposing __version__ in __init__.py
- [ ] Add basic integration tests for core functionality
- [ ] Test with actual claude-code-sdk installation
- [ ] Verify all imports work with published claif package
- [ ] Test CLI entry point installation

### 🟡 Important
- [ ] Add error handling for missing API keys
- [ ] Implement proper async cleanup in wrapper
- [ ] Add timeout handling for long-running queries
- [ ] Create minimal working examples

### 🟢 Nice to Have
- [ ] Add CLI command aliases for common operations
- [ ] Implement --version flag for CLI
- [ ] Add progress indicators for long operations
- [ ] Create getting started guide

## Post-1.0.0 Tasks

### Documentation
- [ ] Create API reference documentation
- [ ] Add troubleshooting guide
- [ ] Document all approval strategies with examples
- [ ] Create video tutorial for CLI usage

### Testing
- [ ] Add unit tests for all modules
- [ ] Integration tests with mock Claude responses
- [ ] Performance benchmarks
- [ ] Test coverage > 80%

### Features
- [ ] Add session search functionality
- [ ] Implement session tags and metadata
- [ ] Add session compression for large conversations
- [ ] Create more session templates

### Code Quality
- [ ] Add docstring examples
- [ ] Improve error messages
- [ ] Add debug logging mode
- [ ] Profile memory usage

## Known Issues

### High Priority
- [x] `time.sleep()` in async function (wrapper.py:153) - use `asyncio.sleep()` (FIXED)
- [ ] Missing proper MCP tool integration
- [ ] No validation for claude-code-sdk options
- [x] Session timestamps lack timezone info (FIXED)

### Medium Priority
- [ ] Unused function arguments in approval strategies
- [ ] Boolean positional arguments should use keyword-only
- [ ] Some imports could be optimized
- [ ] Cache directory creation could fail silently

### Low Priority
- [ ] Line length exceeds 120 chars in one place
- [ ] Consider using pathlib throughout instead of string paths
- [ ] Add more specific exception types
- [ ] Standardize logging format

## Technical Debt

1. **Import Structure**: Currently using absolute imports for claif, but this assumes claif is installed. Need to handle cases where it might not be available.

2. **Testing**: Minimal test coverage - only a version test exists. Need comprehensive test suite.

3. **Error Handling**: Generic exception catching in some places should be more specific.

4. **Async Best Practices**: Using `time.sleep()` in async context should be `asyncio.sleep()`.

5. **Type Safety**: Some areas could benefit from stricter typing, especially for dict parameters.

## Future Considerations

### Performance
- Implement connection pooling for API calls
- Add request batching for multiple queries
- Optimize session loading for large files
- Consider using SQLite for session storage

### Security
- Add API key validation
- Implement secure session storage
- Add rate limiting support
- Consider encryption for sensitive data

### Integrations
- VS Code extension support
- Jupyter notebook integration
- IDE plugins for other editors
- CI/CD pipeline examples

## Contributing Guidelines Needed

- [ ] Create CONTRIBUTING.md
- [ ] Define code review process
- [ ] Set up issue templates
- [ ] Create PR template
- [ ] Define release process

## Notes

- Focus on MVP functionality for 1.0.0
- Avoid scope creep - save advanced features for later versions
- Prioritize developer experience and documentation
- Keep the wrapper thin and maintainable
- Test thoroughly with real claude-code-sdk before release