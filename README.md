# claif_cla

**Claif provider for Anthropic's Claude Code CLI**

## Quickstart

`claif_cla` is a Python wrapper for Claude that provides session management, tool approval strategies, and a rich CLI interface. Version 1.0.8 improves message type handling between claude-code-sdk and Claif formats. Install it and start chatting with Claude in seconds:

```bash
pip install claif_cla && python -m claif_cla.cli ask "Hello, Claude!"
```

`claif_cla` is a Python package that provides a thin wrapper around the [`claude_code_sdk`](https://github.com/anthropics/claude-code-sdk-python) package, integrating Anthropic's [Claude Code CLI](https://github.com/anthropics/claude-code) into the Claif (Command-Line AI Framework) ecosystem.

## What is claif_cla?

This package acts as a bridge between the Claif framework and Claude's AI capabilities. It provides a minimal interface that:

- Wraps `claude_code_sdk` with Claif-standard options
- Manages persistent conversation sessions
- Implements flexible tool approval strategies for MCP (Model Context Protocol) tools
- Provides response caching to reduce API costs
- Offers a rich CLI interface built with Fire and Rich libraries

## Installation

### From PyPI

```bash
pip install claif_cla
```

### From Source

```bash
git clone https://github.com/twardoch/claif_cla.git
cd claif_cla
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev,test]"
```

## Command Line Usage

The package provides a Fire-based CLI interface. Run commands through Python:

```bash
python -m claif_cla.cli --help
```

### Basic Commands

```bash
# Ask Claude a question
python -m claif_cla.cli ask "What is the theory of relativity?"

# Stream responses in real-time
python -m claif_cla.cli stream "Tell me about machine learning"

# Interactive conversation mode
python -m claif_cla.cli interactive

# Check service health
python -m claif_cla.cli health
```

### Session Management

```bash
# List sessions
python -m claif_cla.cli session list

# Create new session
python -m claif_cla.cli session create

# Show session messages
python -m claif_cla.cli session show SESSION_ID

# Export session
python -m claif_cla.cli session export SESSION_ID --format markdown --output chat.md
```

## Python API Usage

### Basic Query

```python
import asyncio
from claif_cla import query
from claif.common import ClaifOptions

async def main():
    # Simple query
    async for message in query("Hello, Claude!"):
        print(f"{message.role}: {message.content}")
    
    # Query with options
    options = ClaifOptions(
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=500
    )
    
    async for message in query("Explain Python decorators", options):
        print(message.content)

asyncio.run(main())
```

### Session Management

```python
from claif_cla.session import SessionManager, Session
from claif.common import Message, MessageRole

# Initialize session manager
session_mgr = SessionManager()

# Create session
session_id = session_mgr.create_session()

# Add messages
message = Message(
    role=MessageRole.USER,
    content="What is machine learning?"
)
session_mgr.add_message(session_id, message)

# Export session
markdown = session_mgr.export_session(session_id, export_format="markdown")
```

### Tool Approval Strategies

```python
from claif_cla.approval import create_approval_strategy

# Allow specific tools only
safe_tools = create_approval_strategy("allow_list", {
    "allowed_tools": ["read_file", "list_files", "search"]
})

# Deny dangerous tools
deny_dangerous = create_approval_strategy("deny_list", {
    "denied_tools": ["delete_file", "execute_command"]
})

# Pattern-based approval
patterns = create_approval_strategy("pattern", {
    "patterns": ["read_.*", "list_.*"],
    "deny": False
})
```

## Why Use claif_cla?

1. **Minimal Overhead**: Thin wrapper design adds minimal complexity to claude-code-sdk
2. **Session Persistence**: Save and restore conversations across sessions
3. **Tool Control**: Fine-grained control over MCP tool approval
4. **Response Caching**: Built-in caching reduces API costs
5. **Claif Integration**: Works seamlessly with other Claif providers

## How It Works

### Architecture

The package consists of five main modules:

```
claif_cla/
├── __init__.py      # Main query function and exports
├── cli.py           # Fire-based CLI interface
├── wrapper.py       # Enhanced wrapper with caching and retry logic
├── session.py       # Session management and persistence
└── approval.py      # MCP tool approval strategies
```

### Core Components

1. **Main Module** (`__init__.py`)
   - Provides the `query` function that converts Claif options to Claude options
   - Thin wrapper around `claude_code_sdk.query`
   - Uses loguru for logging

2. **CLI Module** (`cli.py`)
   - Fire-based command-line interface
   - Commands: ask, stream, interactive, session, health, benchmark
   - Rich terminal formatting for better user experience

3. **Wrapper Module** (`wrapper.py`)
   - `ResponseCache`: SHA256-based caching with TTL support
   - `ClaudeWrapper`: Adds retry logic with exponential backoff
   - Handles errors and timeouts gracefully

4. **Session Module** (`session.py`)
   - `Session`: Data class for conversation storage
   - `SessionManager`: CRUD operations for sessions
   - Session templates for common use cases
   - Export to JSON and Markdown formats

5. **Approval Module** (`approval.py`)
   - Abstract `ApprovalStrategy` base class
   - Eight concrete strategy implementations
   - Factory function for strategy creation
   - Predefined strategy presets

### Data Flow

1. User provides prompt and options
2.Claif options are converted to ClaudeCodeOptions
3. Request is forwarded to claude_code_sdk
4. Responses are streamed back from Claude API
5. Optional caching based on prompt+options hash
6. Messages saved to session if ID provided
7. Formatted output returned to user

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/claif_cla --cov-report=term-missing
```

### Code Quality

```bash
# Format code
ruff format src/claif_cla tests

# Run linting
ruff check src/claif_cla tests

# Type checking
mypy src/claif_cla
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [Claif](https://github.com/twardoch/claif) - The main Claif framework
- [claude-code-sdk](https://github.com/anthropics/claude-code-sdk-python) - Anthropic's Claude SDK
- [claif_cod](https://github.com/twardoch/claif_cod) -Claif provider for OpenAI Codex
- [claif_gem](https://github.com/twardoch/claif_gem) -Claif provider for Google Gemini