# claif_cla Development Plan - MVP Focus

## Project Vision

`claif_cla` is a minimal, production-ready wrapper around `claude-code-sdk` that integrates seamlessly with theClaif ecosystem. The focus is on delivering a stable, cross-platform MVP that auto-installs dependencies and works reliably.

## MVP Requirements (v1.0)

### Core Functionality
1. **Thin Claude SDK Wrapper**
   - Async message streaming via claude-code-sdk
   -Claif-compatible provider interface
   - Proper error handling and timeouts
   - Loguru-based logging (no rich dependencies)

2. **Auto-Install Support (Issue #201)**
   - Detect missing claude-code-sdk installation
   - Auto-install via npm when missing
   - Integrate with bun bundling for offline scenarios
   - Clear user guidance during installation

3. **CLI Interface**
   - Fire-based CLI with simple output (no rich)
   - Essential commands: ask, stream, health
   - Session management (create, list, show, delete)
   - Version information and help

4. **Cross-Platform Compatibility**
   - Works on Windows, macOS, Linux
   - Handles different Node.js installation paths
   - Robust subprocess management

### Streamlined Architecture

```
claif_cla/
├── wrapper.py     # Core Claude SDK integration
├── cli.py         # Fire-based CLI (loguru only)
├── session.py     # Session management
├── approval.py    # Tool approval strategies
└── install.py     # Auto-install functionality
```

## Implementation Priorities

### Phase 1: Core Stability
- [ ] Remove all rich dependencies, use loguru for output
- [ ] Implement robust error handling
- [ ] Add async cleanup and timeout handling
- [ ] Validate claude-code-sdk options

### Phase 2: Auto-Install
- [ ] CLI detection logic
- [ ] npm installation wrapper
- [ ] Bun bundle integration
- [ ] User-friendly installation prompts

### Phase 3: Testing & Polish
- [ ] Unit tests for core modules
- [ ] Integration tests with mocked responses
- [ ] Cross-platform testing
- [ ] Documentation and examples

## Design Decisions

### Simplified Dependencies
- **Remove**: rich, complex UI libraries
- **Keep**: loguru, fire, claude-code-sdk
- **Add**: Auto-install utilities

### Error Handling Strategy
- Fail fast with clear error messages
- Actionable suggestions for common issues
- Graceful degradation when possible

### Session Management
- JSON-based persistence (simple, reliable)
- Basic templates for common use cases
- Export capabilities (JSON, Markdown)

## Success Metrics

1. **Reliability**: Works out-of-box with `uvx claif_cla`
2. **Performance**: < 100ms overhead per query
3. **Usability**: Clear error messages, auto-install works
4. **Maintainability**: < 1000 lines of code total
5. **Cross-platform**: Tested on Windows, macOS, Linux

## Non-Goals for MVP

- Complex UI/rich formatting
- Advanced session features
- Performance optimizations
- Extensive configuration options
- Web interfaces

## Release Strategy

1. **v1.0**: MVP with auto-install
2. **v1.1**: Bug fixes and polish
3. **v1.2**: Enhanced features based on feedback

This plan prioritizes shipping a working, reliable tool that users can install and use immediately without manual setup.
