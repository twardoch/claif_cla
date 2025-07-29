# claif_cla - Claude Provider for Claif

A Claif provider for Anthropic's Claude with full OpenAI client API compatibility. This package wraps the `claude-code-sdk` to provide a consistent interface following the `client.chat.completions.create()` pattern.

## Features

- **OpenAI Client API Compatible**: Use the familiar `client.chat.completions.create()` pattern
- **Full Type Safety**: Returns standard `ChatCompletion` and `ChatCompletionChunk` objects
- **Streaming Support**: Real-time streaming with proper chunk handling
- **Session Management**: Persistent conversation history with atomic operations
- **Tool Approval**: Fine-grained control over MCP tool usage
- **Response Caching**: Intelligent caching to reduce API costs
- **Fire-based CLI**: Rich terminal interface with multiple output formats

## Quickstart

```bash
# Install
pip install claif_cla

# Basic usage - OpenAI compatible
python -c "
from claif_cla import ClaudeClient
client = ClaudeClient()
response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Hello Claude!'}],
    model='claude-3-5-sonnet-20241022'
)
print(response.choices[0].message.content)
"

# CLI usage
claif-cla query "Explain quantum computing"
claif-cla chat --model claude-3-opus-20240229
```

## What is claif_cla?

`claif_cla` is a Python wrapper that integrates Anthropic's Claude into the Claif framework with full OpenAI client API compatibility. It provides a thin layer over the [`claude_code_sdk`](https://github.com/anthropics/claude-code-sdk-python) package, adding session management, tool approval strategies, and response caching while maintaining full compatibility with Claude's capabilities.

**Key Features:**
- **Session persistence** - Save and restore conversations across sessions
- **Tool approval strategies** - Fine-grained control over MCP tool usage
- **Response caching** - Reduce API costs with intelligent caching
- **Rich CLI** - Beautiful terminal interface with Fire framework
- **Async support** - Full async/await for efficient operations
- **Type safety** - Comprehensive type hints throughout

## Installation

### Basic Installation

```bash
# Core package only
pip install claif_cla

# With Claif framework
pip install claif claif_cla
```

### Installing Claude CLI

The Claude CLI can be installed automatically:

```bash
# Using claif_cla installer
python -m claif_cla.install

# Or manually via npm
npm install -g @anthropic-ai/claude-code

# Or using Claif's installer
pip install claif && claif install claude
```

### Development Installation

```bash
git clone https://github.com/twardoch/claif_cla.git
cd claif_cla
pip install -e ".[dev,test]"
```

## Usage

### Basic Usage (OpenAI-Compatible)

```python
from claif_cla import ClaudeClient

# Initialize the client
client = ClaudeClient(
    api_key="your-api-key"  # Optional, uses ANTHROPIC_API_KEY env var
)

# Create a chat completion - exactly like OpenAI
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Explain machine learning"}
    ],
    temperature=0.7,
    max_tokens=1000
)

# Access the response
print(response.choices[0].message.content)
print(f"Model: {response.model}")
print(f"Usage: {response.usage}")
```

### Streaming Responses

```python
from claif_cla import ClaudeClient

client = ClaudeClient()

# Stream responses in real-time
stream = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Write a haiku about programming"}
    ],
    stream=True
)

# Process streaming chunks
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## CLI Usage

```bash
# Basic query
claif-cla query "What is the theory of relativity?"

# With specific model
claif-cla query "Explain Python decorators" --model claude-3-opus-20240229

# Interactive chat mode
claif-cla chat --model claude-3-5-sonnet-20241022

# List available models
claif-cla models

# JSON output
claif-cla query "Hello" --json-output
```

### Session Management

```bash
# List all sessions
python -m claif_cla.cli session list

# Create new session with optional metadata
python -m claif_cla.cli session create --metadata '{"project": "my-app"}'

# Show session messages
python -m claif_cla.cli session show SESSION_ID

# Continue existing session
python -m claif_cla.cli ask "Continue our discussion" --session SESSION_ID

# Export session to file
python -m claif_cla.cli session export SESSION_ID --format markdown --output chat.md
python -m claif_cla.cli session export SESSION_ID --format json --output chat.json

# Delete session
python -m claif_cla.cli session delete SESSION_ID
```

### Advanced Features

```bash
# Benchmark response time
python -m claif_cla.cli benchmark "Complex analysis task" --iterations 5

# Set approval strategy for tools
python -m claif_cla.cli ask "Analyze this file" --approval allow_list --allowed-tools "read_file,search"

# Use with caching
python -m claif_cla.cli ask "Expensive computation" --cache --cache-ttl 3600

# Verbose mode for debugging
python -m claif_cla.cli ask "Debug this" --verbose
```

## Testing

The `claif_cla` package includes comprehensive tests to ensure robust functionality:

### Running Tests

```bash
# Install with test dependencies
pip install -e ".[test]"

# Run all tests
uvx hatch test

# Run specific test modules
uvx hatch test -- tests/test_functional.py -v
uvx hatch test -- tests/test_client.py -v

# Run with coverage
uvx hatch test -- --cov=src/claif_cla --cov-report=html
```

### Test Structure

```
tests/
├── test_functional.py       # End-to-end functionality tests
├── test_client.py          # Client API tests
├── test_session.py         # Session management tests
├── test_approval.py        # Tool approval strategy tests
├── test_wrapper.py         # Caching and retry tests
└── conftest.py             # Test fixtures and configuration
```

### Example Test Usage

The functional tests demonstrate how to use `claif_cla` effectively:

```python
# Test basic query functionality
def test_basic_query():
    client = ClaudeClient(api_key="test-key")
    
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Hello Claude"}]
    )
    
    assert isinstance(response, ChatCompletion)
    assert response.choices[0].message.role == "assistant"
    assert len(response.choices[0].message.content) > 0

# Test streaming responses
def test_streaming():
    client = ClaudeClient()
    
    stream = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": "Count to 3"}],
        stream=True
    )
    
    chunks = list(stream)
    assert len(chunks) > 0
    
    # Reconstruct full message
    content = "".join(
        chunk.choices[0].delta.content or ""
        for chunk in chunks
        if chunk.choices and chunk.choices[0].delta.content
    )
    assert len(content) > 0

# Test parameter passing
def test_with_parameters():
    client = ClaudeClient()
    
    response = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a hello world function"}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    assert response.model == "claude-3-5-sonnet-20241022"
    assert response.usage.total_tokens > 0
```

### Mock Testing for CI/CD

The tests use comprehensive mocking to work in CI environments without requiring actual API keys:

```python
from unittest.mock import patch, MagicMock

@patch("claif_cla.client.ClaudeCodeClient")
def test_client_initialization(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    client = ClaudeClient(api_key="test-key", timeout=300)
    
    # Verify proper initialization
    mock_client_class.assert_called_once_with(
        api_key="test-key", 
        timeout=300
    )
```

## API Compatibility

This package is fully compatible with the OpenAI Python client API:

```python
# You can use it as a drop-in replacement
from claif_cla import ClaudeClient as OpenAI

client = OpenAI()
# Now use exactly like the OpenAI client
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Migration from Old Async API

If you were using the old async-based Claif API:

```python
# Old API (deprecated)
import asyncio
from claif_cla import query
from claif.common import ClaifOptions

async def old_way():
    async for message in query("Hello, Claude!"):
        print(f"{message.role}: {message.content}")
    
# New API (OpenAI-compatible)
from claif_cla import ClaudeClient

def new_way():
    client = ClaudeClient()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello, Claude!"}],
        model="claude-3-5-sonnet-20241022"
    )
    print(response.choices[0].message.content)
```

### Key Changes

1. **Synchronous by default**: No more `async/await` for basic usage
2. **OpenAI-compatible structure**: `client.chat.completions.create()` pattern
3. **Standard message format**: `[{"role": "user", "content": "..."}]`
4. **Streaming support**: Use `stream=True` for real-time responses
5. **Type-safe responses**: Returns `ChatCompletion` objects from OpenAI types

### Session Management

```python
from claif_cla.session import SessionManager, Session
from claif.common import Message, MessageRole

# Initialize session manager
session_mgr = SessionManager()

# Create new session
session_id = session_mgr.create_session(
    metadata={"project": "my-app", "user": "john"}
)

# Add messages to session
user_msg = Message(
    role=MessageRole.USER,
    content="What is machine learning?"
)
session_mgr.add_message(session_id, user_msg)

# Get session history
session = session_mgr.get_session(session_id)
for msg in session.messages:
    print(f"{msg.role}: {msg.content}")

# Export session
markdown_export = session_mgr.export_session(session_id, export_format="markdown")
print(markdown_export)

# Save session to disk
session_mgr.save_session(session_id)
```

### Tool Approval Strategies

```python
from claif_cla.approval import create_approval_strategy

# Strategy 1: Allow specific tools only
safe_tools = create_approval_strategy("allow_list", {
    "allowed_tools": ["read_file", "list_files", "search"]
})

# Strategy 2: Deny dangerous tools
deny_dangerous = create_approval_strategy("deny_list", {
    "denied_tools": ["delete_file", "execute_command", "write_file"]
})

# Strategy 3: Pattern-based approval
patterns = create_approval_strategy("pattern", {
    "patterns": ["read_.*", "list_.*", "search_.*"],
    "deny": False  # Allow matching patterns
})

# Strategy 4: Threshold-based (by risk score)
threshold = create_approval_strategy("threshold", {
    "max_risk": 3  # Only allow tools with risk <= 3
})

# Use strategy in query
from claif_cla import ClaudeCodeOptions

options = ClaudeCodeOptions(
    tool_approval_strategy=safe_tools,
    model="claude-3-opus-20240229"
)
```

### Response Caching

```python
from claif_cla.wrapper import ClaudeWrapper, ResponseCache

# Create wrapper with caching
wrapper = ClaudeWrapper(
    cache_ttl=3600,  # 1 hour cache
    enable_cache=True
)

# First call - hits API
response1 = await wrapper.query("Expensive analysis", options)

# Second call - returns from cache
response2 = await wrapper.query("Expensive analysis", options)

# Clear cache if needed
wrapper.cache.clear()
```

### Using with Claif Framework

```python
from claif import query as claif_query, Provider, ClaifOptions

# Query through Claif framework
options = ClaifOptions(
    provider=Provider.CLAUDE,
    model="claude-3-opus-20240229",
    temperature=0.5
)

async for message in claif_query("Hello from Claif!", options):
    print(message.content)
```

## How It Works

### Architecture Overview

```
┌─────────────────────────────┐
│    User Application         │
├─────────────────────────────┤
│    claif_cla CLI           │ ← Fire-based CLI with rich output
├─────────────────────────────┤
│    claif_cla Core          │ ← Main query function & types
├─────────────────────────────┤
│    Session Manager         │ ← Conversation persistence
├─────────────────────────────┤
│    Approval Strategies     │ ← Tool usage control
├─────────────────────────────┤
│    Response Cache          │ ← Cost optimization
├─────────────────────────────┤
│    claude_code_sdk         │ ← Anthropic's SDK
└─────────────────────────────┘
```

### Core Components

#### Main Module (`__init__.py`)

The entry point that provides the `query` function:

```python
async def query(
    prompt: str,
    options: ClaifOptions | None = None
) -> AsyncIterator[Message]:
    """Query Claude with Claif-compatible interface."""
    # Convert Claif options to Claude options
    claude_options = _convert_options(options)
    
    # Delegate to claude_code_sdk
    async for message in claude_query(prompt, claude_options):
        yield message
```

Key features:
- Thin wrapper design for minimal overhead
- Option conversion between Claif and Claude formats
- Direct message passthrough
- Loguru-based debug logging

#### CLI Module (`cli.py`)

Fire-based command-line interface with rich formatting:

```python
class ClaudeCLI:
    def ask(self, prompt: str, **kwargs):
        """Ask Claude a question."""
        
    def stream(self, prompt: str, **kwargs):
        """Stream responses in real-time."""
        
    def interactive(self):
        """Start interactive chat session."""
        
    def session(self, action: str, **kwargs):
        """Manage conversation sessions."""
```

Commands:
- `ask` - Single query with options
- `stream` - Real-time streaming responses
- `interactive` - Chat mode with history
- `session` - CRUD operations for conversations
- `health` - Check Claude availability
- `benchmark` - Performance testing

#### Session Module (`session.py`)

Persistent conversation management:

```python
@dataclass
class Session:
    id: str
    messages: list[Message]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
class SessionManager:
    def __init__(self, session_dir: Path | None = None):
        self.session_dir = session_dir or Path.home() / ".claif" / "sessions"
```

Features:
- JSON-based session storage
- Atomic file operations
- Session templates (coding, analysis, creative)
- Export to Markdown/JSON formats
- Metadata for organization

#### Approval Module (`approval.py`)

Fine-grained control over MCP tool usage:

```python
class ApprovalStrategy(ABC):
    @abstractmethod
    def should_approve(self, tool_name: str, tool_metadata: dict) -> bool:
        """Decide if tool should be approved."""

# Eight concrete strategies:
1. AllowAllStrategy - Approve everything
2. DenyAllStrategy - Deny everything  
3. AllowListStrategy - Only allow specific tools
4. DenyListStrategy - Deny specific tools
5. PatternStrategy - Regex-based approval
6. ThresholdStrategy - Risk score based
7. CategoryStrategy - Approve by category
8. CompositeStrategy - Combine multiple strategies
```

Factory function for easy creation:
```python
strategy = create_approval_strategy("allow_list", {
    "allowed_tools": ["read_file", "search"]
})
```

#### Wrapper Module (`wrapper.py`)

Enhanced functionality around claude_code_sdk:

```python
class ResponseCache:
    """SHA256-based response caching."""
    def get_cache_key(self, prompt: str, options: dict) -> str:
        data = json.dumps({"prompt": prompt, "options": options})
        return hashlib.sha256(data.encode()).hexdigest()

class ClaudeWrapper:
    """Adds retry logic and caching."""
    async def query_with_retry(self, prompt: str, options, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await self._query(prompt, options)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
```

Features:
- SHA256-based cache keys
- TTL support for cache entries
- Exponential backoff retry logic
- Graceful error handling

### Code Structure

```
claif_cla/
├── src/claif_cla/
│   ├── __init__.py      # Main query function and exports
│   ├── cli.py           # Fire-based CLI interface
│   ├── wrapper.py       # Caching and retry logic
│   ├── session.py       # Session management
│   ├── approval.py      # Tool approval strategies
│   └── install.py       # CLI installation helper
├── tests/
│   ├── test_session.py  # Session tests
│   ├── test_approval.py # Strategy tests
│   └── test_wrapper.py  # Cache tests
├── pyproject.toml       # Package configuration
├── README.md            # This file
└── CLAUDE.md            # Development guide
```

### Message Flow

1. **User Input** → CLI command or API call
2. **Option Conversion** → ClaifOptions → ClaudeCodeOptions
3. **Session Check** → Load existing session if specified
4. **Cache Lookup** → Check for cached response
5. **SDK Call** → Forward to claude_code_sdk
6. **Tool Approval** → Apply strategy if tools requested
7. **Response Stream** → Yield messages as they arrive
8. **Cache Storage** → Store response if caching enabled
9. **Session Update** → Save messages to session
10. **Output Format** → Display with rich formatting

### Configuration

Environment variables:
- `ANTHROPIC_API_KEY` - Required for Claude API
- `CLAIF_SESSION_DIR` - Custom session directory
- `CLAIF_CACHE_TTL` - Default cache duration
- `CLAIF_DEFAULT_MODEL` - Default Claude model

Config file (`~/.claif/config.json`):
```json
{
    "providers": {
        "claude": {
            "model": "claude-3-opus-20240229",
            "api_key_env": "ANTHROPIC_API_KEY",
            "cache_ttl": 3600,
            "enable_cache": true
        }
    }
}
```

## Installation with Bun

`claif_cla` includes an installer that uses Bun for fast installation:

```python
# install.py
def install_claude():
    """Install Claude Code CLI using bun."""
    # 1. Ensure bun is installed
    # 2. Install @anthropic-ai/claude-code globally
    # 3. Bundle with bun compile
    # 4. Copy to ~/.local/bin
```

Benefits:
- 10x faster than npm
- Creates standalone executables
- No Node.js conflicts
- Cross-platform support

## Why Use claif_cla?

### 1. **Minimal Overhead**
- Thin wrapper adds < 100ms latency
- Direct SDK passthrough
- No unnecessary abstractions

### 2. **Session Persistence**
- Continue conversations across runs
- Export chat history
- Organize with metadata

### 3. **Tool Control**
- Eight approval strategies
- Combine strategies
- Custom implementations

### 4. **Cost Optimization**
- Response caching
- Retry logic
- Request deduplication

### 5. **Developer Experience**
- Type hints everywhere
- Rich CLI output
- Comprehensive logging
- Easy integration

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/twardoch/claif_cla.git
cd claif_cla

# Install with dev dependencies
pip install -e ".[dev,test]"

# Run tests
pytest

# Code quality
ruff format src/claif_cla tests
ruff check src/claif_cla tests
mypy src/claif_cla
```

### Testing

```bash
# Unit tests
pytest tests/test_session.py -v
pytest tests/test_approval.py -v

# Integration tests
pytest tests/test_integration.py -v

# Coverage report
pytest --cov=src/claif_cla --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Adam Twardoch

## Links

### claif_cla Resources

- [GitHub Repository](https://github.com/twardoch/claif_cla) - Source code
- [PyPI Package](https://pypi.org/project/claif_cla/) - Latest release
- [Issue Tracker](https://github.com/twardoch/claif_cla/issues) - Bug reports
- [Discussions](https://github.com/twardoch/claif_cla/discussions) - Q&A

### Related Projects

**Claif Ecosystem:**
- [Claif](https://github.com/twardoch/claif) - Main framework
- [claif_gem](https://github.com/twardoch/claif_gem) - Gemini provider
- [claif_cod](https://github.com/twardoch/claif_cod) - Codex provider

**Upstream Projects:**
- [Claude Code](https://github.com/anthropics/claude-code) - Anthropic's CLI
- [claude-code-sdk](https://github.com/anthropics/claude-code-sdk-python) - Python SDK
- [Anthropic API](https://docs.anthropic.com/) - API documentation

**Tools & Libraries:**
- [Fire](https://github.com/google/python-fire) - CLI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Loguru](https://github.com/Delgan/loguru) - Logging library
- [Bun](https://bun.sh) - Fast JavaScript runtime