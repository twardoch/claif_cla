---
# this_file: src_docs/md/index.md
title: claif_cla Documentation
description: Complete documentation for claif_cla - A Claif provider for Anthropic Claude with OpenAI client API compatibility
---

# claif_cla Documentation

Welcome to the comprehensive documentation for **claif_cla**, a Claif provider for Anthropic's Claude that offers full OpenAI client API compatibility.

## 🚀 Quick TLDR

**claif_cla** is a Python package that provides a unified interface to interact with Anthropic's Claude AI models using the familiar OpenAI client API pattern. It wraps the `claude-code-sdk` while adding session management, tool approval strategies, response caching, and a rich CLI interface.

### Key Features at a Glance

- ✅ **OpenAI API Compatible** - Drop-in replacement using `client.chat.completions.create()`
- 🔄 **Session Management** - Persistent conversation history with atomic operations
- 🛡️ **Tool Approval** - Fine-grained control over MCP tool usage with 8+ strategies
- ⚡ **Response Caching** - Intelligent caching to reduce API costs
- 🎨 **Rich CLI** - Beautiful terminal interface with Fire framework
- 🔒 **Type Safety** - Full type hints and returns standard OpenAI objects
- 📊 **Streaming Support** - Real-time streaming responses

### Installation & Quick Start

```bash
# Install package
pip install claif_cla

# Basic usage - OpenAI compatible
from claif_cla import ClaudeClient
client = ClaudeClient()
response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Hello Claude!'}],
    model='claude-3-5-sonnet-20241022'
)
print(response.choices[0].message.content)

# CLI usage
claif-cla query "Explain quantum computing" --model claude-3-opus-20240229
```

---

## 📚 Table of Contents

This documentation is organized into 9 comprehensive chapters covering every aspect of claif_cla:

### [Chapter 1: Getting Started & Installation](getting-started/installation.md)
**TLDR**: Complete installation guide, system requirements, and environment setup for claif_cla.

Learn how to install claif_cla, set up the Claude CLI, configure environment variables, and verify your installation. Covers installation via pip, npm, and development setup with comprehensive troubleshooting.

### [Chapter 2: Basic Usage & API Reference](api/openai-compatibility.md)
**TLDR**: Core API usage patterns, OpenAI compatibility layer, and basic programming examples.

Master the fundamental API patterns for querying Claude using OpenAI-compatible methods. Covers synchronous/asynchronous operations, streaming responses, parameter handling, and response object structure.

### [Chapter 3: OpenAI Client Compatibility](api/client-methods.md)
**TLDR**: Deep dive into OpenAI API compatibility, method mappings, and migration strategies.

Understand how claif_cla achieves full OpenAI client compatibility, including method mappings, response format conversion, error handling alignment, and migration from existing OpenAI codebases.

### [Chapter 4: Session Management](sessions/overview.md)
**TLDR**: Persistent conversation handling, session lifecycle, and history management.

Explore comprehensive session management capabilities including creating, saving, loading, and organizing conversations. Covers session metadata, templates, export formats, and atomic operations.

### [Chapter 5: Tool Approval Strategies](tools/strategies.md)
**TLDR**: Security-focused tool usage control with 8+ built-in approval strategies.

Learn to control MCP tool usage through sophisticated approval strategies. Covers allow/deny lists, pattern-based approval, risk thresholds, category-based controls, and custom strategy development.

### [Chapter 6: CLI Usage & Commands](cli/overview.md)
**TLDR**: Complete CLI reference with interactive modes, batch operations, and configuration.

Master the powerful Fire-based CLI interface including interactive chat modes, batch processing, session management commands, output formatting, and configuration options.

### [Chapter 7: Testing & Development](testing/running.md)
**TLDR**: Comprehensive testing framework, development setup, and contribution guidelines.

Understand the robust testing infrastructure including unit tests, integration tests, mocking strategies, coverage reporting, and development environment setup for contributors.

### [Chapter 8: Architecture & Internals](architecture/overview.md)
**TLDR**: System architecture, component design, and integration patterns.

Dive deep into claif_cla's architecture including the wrapper pattern, message flow, caching mechanisms, session storage, and integration points with the claude-code-sdk.

### [Chapter 9: Advanced Features & Configuration](advanced/caching.md)
**TLDR**: Performance optimization, caching strategies, configuration options, and troubleshooting.

Explore advanced capabilities including response caching, performance tuning, environment configuration, logging setup, and comprehensive troubleshooting guides.

---

## 🎯 Quick Navigation

### For New Users
1. Start with [Installation](getting-started/installation.md)
2. Follow the [Quick Start Guide](getting-started/quickstart.md)
3. Try [Basic Examples](getting-started/examples.md)

### For Developers
1. Review [API Reference](api/openai-compatibility.md)
2. Understand [Architecture](architecture/overview.md)
3. Set up [Development Environment](testing/development.md)

### For Advanced Users
1. Configure [Tool Approval](tools/strategies.md)
2. Optimize with [Caching](advanced/caching.md)
3. Customize [CLI Usage](cli/overview.md)

---

## 🔗 External Resources

- **[GitHub Repository](https://github.com/twardoch/claif_cla)** - Source code and issues
- **[PyPI Package](https://pypi.org/project/claif_cla/)** - Latest releases
- **[Claif Framework](https://github.com/twardoch/claif)** - Main framework
- **[Claude Code SDK](https://github.com/anthropics/claude-code-sdk-python)** - Underlying SDK
- **[Anthropic API Docs](https://docs.anthropic.com/)** - Claude API reference

---

## 💡 Need Help?

- 📖 **Documentation**: Browse the chapters above for comprehensive guides
- 🐛 **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/twardoch/claif_cla/issues)
- 💬 **Discussions**: Join conversations on [GitHub Discussions](https://github.com/twardoch/claif_cla/discussions)
- 🚀 **Examples**: Check the [Examples section](examples/basic.md) for practical use cases

---

## 📄 License

claif_cla is released under the MIT License. See the [LICENSE](https://github.com/twardoch/claif_cla/blob/main/LICENSE) file for details.

Copyright © 2025 Adam Twardoch