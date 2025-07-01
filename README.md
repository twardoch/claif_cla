# claif_cla

**CLAIF (Command-Line Artificial Intelligence Framework) provider for Anthropic's Claude Code CLI**

`claif_cla` is a Python package that provides a thin wrapper around the [`claude_code_sdk`](https://github.com/anthropics/claude-code-sdk-python) package, integrating Anthropic's [Claude Code CLI](https://github.com/anthropics/claude-code) into the CLAIF ecosystem. It enables seamless interaction with Claude's agentic capabilities through both command-line and programmatic interfaces.

## What is claif_cla?

`claif_cla` serves as a bridge between the CLAIF framework and Claude's powerful AI capabilities. It provides:

- **Thin wrapper architecture** around `claude_code_sdk` for minimal overhead
- **Advanced session management** with persistence, branching, and merging
- **Flexible tool approval strategies** for MCP (Model Context Protocol) tools
- **Response caching** with configurable TTL to reduce API costs
- **Retry logic** with exponential backoff for robust operation
- **Rich CLI interface** built with Fire and Rich libraries
- **Full async/await support** for efficient concurrent operations

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

### With Development Dependencies

```bash
pip install claif_cla[dev,test]
```

## Command Line Usage

`claif_cla` provides a Fire-based CLI with rich terminal output. The package does not currently install any command-line scripts, but you can access the CLI through Python:

```bash
python -m claif_cla.cli --help
```

### Basic Commands

#### Simple Queries
```bash
# Ask Claude a question
python -m claif_cla.cli ask "What is the theory of relativity?"

# Use specific model
python -m claif_cla.cli ask "Explain quantum computing" --model claude-3-opus-20240229

# Customize parameters
python -m claif_cla.cli ask "Write a haiku" --temperature 0.8 --max-tokens 100
```

#### Streaming Responses
```bash
# Stream responses in real-time
python -m claif_cla.cli stream "Tell me about machine learning"

# Stream with session tracking
python -m claif_cla.cli stream "Continue the explanation" --session my-session-id
```

#### Interactive Mode
```bash
# Start interactive conversation
python -m claif_cla.cli interactive

# Resume existing session
python -m claif_cla.cli interactive --session existing-session-id
```

### Session Management

Sessions are stored in `~/.claif/sessions/` as JSON files.

```bash
# List all sessions
python -m claif_cla.cli session list

# Create new session
python -m claif_cla.cli session create

# Show session messages
python -m claif_cla.cli session show SESSION_ID

# Export session to markdown
python -m claif_cla.cli session export SESSION_ID --format markdown --output chat.md

# Branch session at specific message
python -m claif_cla.cli session branch SESSION_ID --point 5

# Merge two sessions
python -m claif_cla.cli session merge TARGET_ID --other SOURCE_ID --strategy append
```

### Health Check and Benchmarking

```bash
# Check Claude service health
python -m claif_cla.cli health

# Benchmark performance
python -m claif_cla.cli benchmark --iterations 10 --model claude-3-opus-20240229
```

## Python API Usage

### Basic Query

```python
import asyncio
from claif_cla import query
from claif.common import ClaifOptions

async def main():
    # Simple query - returns Claude messages
    async for message in query("Hello, Claude!"):
        print(f"{message.role}: {message.content}")
    
    # Query with options
    options = ClaifOptions(
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=500,
        system_prompt="You are a helpful assistant.",
        cache=True  # Enable response caching
    )
    
    async for message in query("Explain Python decorators", options):
        print(message.content)

asyncio.run(main())
```

### Using the Enhanced Wrapper

```python
from claif_cla.wrapper import ClaudeWrapper
from claif.common import Config, ClaifOptions

# Create wrapper with configuration
config = Config()
config.cache_ttl = 7200  # 2 hours
config.retry_config = {
    "count": 3,
    "delay": 1.0,
    "backoff": 2.0
}

wrapper = ClaudeWrapper(config)

# Query with automatic retry and caching
async def query_with_wrapper():
    options = ClaifOptions(cache=True)
    async for message in wrapper.query("Complex question", options):
        print(message.content)
```

### Session Management

```python
from claif_cla.session import SessionManager, Session, SessionTemplate
from claif.common import Message, MessageRole

# Initialize session manager
session_mgr = SessionManager()  # Uses ~/.claif/sessions by default

# Create and manage sessions
session_id = session_mgr.create_session()

# Add messages
message = Message(
    role=MessageRole.USER,
    content="What is machine learning?"
)
session_mgr.add_message(session_id, message)

# Get session info
info = session_mgr.get_session_info(session_id)
print(f"Session {info['id']} has {info['message_count']} messages")

# Export session
markdown_export = session_mgr.export_session(session_id, format="markdown")
json_export = session_mgr.export_session(session_id, format="json")

# Branch session
new_session_id = session_mgr.branch_session(session_id, at_point=3)

# Use session templates
code_review_session = SessionTemplate.create_from_template("code_review")
debug_session = SessionTemplate.create_from_template("debugging")
```

### MCP Tool Approval Strategies

```python
from claif_cla.approval import create_approval_strategy, STRATEGY_PRESETS

# Basic strategies
allow_all = create_approval_strategy("allow_all")
deny_all = create_approval_strategy("deny_all")

# Allow specific tools only
safe_tools = create_approval_strategy("allow_list", {
    "allowed_tools": ["read_file", "list_files", "search"]
})

# Deny dangerous tools
deny_dangerous = create_approval_strategy("deny_list", {
    "denied_tools": ["delete_file", "execute_command", "write_file"]
})

# Pattern-based approval
allow_read_patterns = create_approval_strategy("pattern", {
    "patterns": ["read_.*", "list_.*", "get_.*"],
    "deny": False
})

# Conditional approval based on parameters
conditional = create_approval_strategy("conditional", {
    "conditions": {
        "read_file": {
            "path": {"allowed": ["/safe/path", "/data"]}
        },
        "execute_command": {
            "command": {"allowed": ["ls", "pwd", "echo"]}
        }
    }
})

# Composite strategies with AND/OR logic
composite = create_approval_strategy("composite", {
    "strategies": [
        {"type": "deny_list", "config": {"denied_tools": ["delete_file"]}},
        {"type": "pattern", "config": {"patterns": [".*_safe"], "deny": False}}
    ],
    "require_all": True  # AND logic
})

# Use predefined presets
dev_strategy = create_approval_strategy(**STRATEGY_PRESETS["development"])
prod_strategy = create_approval_strategy(**STRATEGY_PRESETS["production"])
```

## Why Use claif_cla?

1. **Seamless CLAIF Integration**: Provides a consistent interface for Claude within the CLAIF ecosystem
2. **Advanced Session Management**: Persistent sessions with branching, merging, and export capabilities
3. **Flexible Tool Control**: Fine-grained control over MCP tool approval with multiple strategy types
4. **Production-Ready**: Built-in caching, retry logic, and comprehensive error handling
5. **Developer-Friendly**: Rich CLI with interactive mode and extensive Python API
6. **Type-Safe**: Full type hints throughout the codebase for better IDE support

## How It Works

### Architecture Overview

The package follows a layered architecture:

```
┌─────────────────────────┐
│   CLAIF Framework       │
├─────────────────────────┤
│     claif_cla           │
│  ┌─────────────────┐    │
│  │   CLI (Fire)    │    │
│  ├─────────────────┤    │
│  │    Wrapper      │    │
│  ├─────────────────┤    │
│  │Session Manager  │    │
│  ├─────────────────┤    │
│  │Approval Strategy│    │
│  └─────────────────┘    │
├─────────────────────────┤
│   claude_code_sdk       │
├─────────────────────────┤
│   Anthropic Claude API  │
└─────────────────────────┘
```

### Core Components

#### 1. **Main Module** (`__init__.py`)
The entry point that provides the `query` function. It:
- Accepts CLAIF-standard options
- Converts them to `ClaudeCodeOptions`
- Passes through to `claude_code_sdk`
- Yields messages back to the caller

#### 2. **CLI Module** (`cli.py`)
A comprehensive Fire-based CLI that provides:
- `ask`: Single query execution with formatting options
- `stream`: Real-time streaming responses
- `interactive`: Full interactive conversation mode
- `session`: Complete session management commands
- `health`: Service health checking
- `benchmark`: Performance testing

#### 3. **Wrapper Module** (`wrapper.py`)
Enhances the basic query functionality with:
- `ResponseCache`: TTL-based caching using SHA256 keys
- `ClaudeWrapper`: Adds retry logic, caching, and error handling
- Automatic message serialization/deserialization

#### 4. **Session Module** (`session.py`)
Provides conversation persistence:
- `Session`: Individual conversation with messages and metadata
- `SessionManager`: CRUD operations for sessions
- `SessionTemplate`: Pre-configured templates for common tasks
- Checkpoint support for session restoration

#### 5. **Approval Module** (`approval.py`)
Implements MCP tool approval strategies:
- `AllowAllStrategy`: Permits all tool usage
- `DenyAllStrategy`: Blocks all tool usage
- `AllowListStrategy`: Whitelist specific tools
- `DenyListStrategy`: Blacklist specific tools
- `PatternStrategy`: Regex-based approval
- `CompositeStrategy`: Combine strategies with AND/OR logic
- `InteractiveStrategy`: User prompts (with safe tool auto-approval)
- `ConditionalStrategy`: Parameter-based conditions

### Data Flow

1. **Query Input**: User provides prompt and options
2. **Option Conversion**: CLAIF options → Claude options
3. **SDK Call**: Request forwarded to `claude_code_sdk`
4. **Response Stream**: Messages streamed from Claude API
5. **Caching**: Responses optionally cached by prompt+options hash
6. **Session Storage**: Messages saved to session if ID provided
7. **Output**: Formatted messages returned to user

### Configuration

The package uses CLAIF's configuration system with additional Claude-specific settings:

```python
# Configuration structure (from CLAIF)
config = {
    "verbose": False,
    "session_dir": "~/.claif/sessions",
    "cache_ttl": 3600,  # 1 hour
    "retry_config": {
        "count": 3,
        "delay": 1.0,
        "backoff": 2.0
    }
}
```

## Development

### Project Structure

```
claif_cla/
├── src/claif_cla/
│   ├── __init__.py      # Main query function
│   ├── cli.py           # Fire-based CLI
│   ├── wrapper.py       # Enhanced wrapper with caching
│   ├── session.py       # Session management
│   ├── approval.py      # MCP tool approval strategies
│   └── __version__.py   # Version info (generated)
├── tests/               # Test suite
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/claif_cla --cov-report=term-missing

# Run specific test file
pytest tests/test_session.py
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
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [CLAIF](https://github.com/twardoch/claif) - The main CLAIF framework
- [claude-code-sdk](https://github.com/anthropics/claude-code-sdk-python) - Anthropic's Claude SDK
- [claif_cod](https://github.com/twardoch/claif_cod) - CLAIF provider for OpenAI Codex
- [claif_gem](https://github.com/twardoch/claif_gem) - CLAIF provider for Google Gemini

## Links

- [GitHub Repository](https://github.com/twardoch/claif_cla)
- [PyPI Package](https://pypi.org/project/claif_cla/)
- [Issue Tracker](https://github.com/twardoch/claif_cla/issues)
- [Documentation](https://github.com/twardoch/claif_cla#readme)