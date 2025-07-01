# CLAIF_CLA - Claude Provider for CLAIF

CLAIF_CLA is the Claude provider implementation for the CLAIF (Command Line Artificial Intelligence Framework). It provides a thin wrapper around the `claude-code-sdk` to integrate Claude AI capabilities into the unified CLAIF ecosystem.

## What is CLAIF_CLA?

CLAIF_CLA is a specialized provider package that:
- Wraps the `claude-code-sdk` for use with CLAIF
- Provides advanced session management capabilities
- Implements sophisticated tool approval strategies
- Offers response caching with TTL support
- Includes retry logic with exponential backoff
- Features a powerful Fire-based CLI with rich terminal output

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

### With CLAIF
```bash
# Install CLAIF with Claude support
pip install claif claif_cla
```

## Command Line Usage

CLAIF_CLA provides its own Fire-based CLI with specialized features for Claude:

### Basic Queries
```bash
# Ask Claude a question
claif-cla ask "What is quantum computing?"

# Query with specific model
claif-cla ask "Explain relativity" --model claude-3-opus-20240229

# Query with custom parameters
claif-cla ask "Write a poem" --temperature 0.8 --max-tokens 200
```

### Streaming
```bash
# Stream responses in real-time
claif-cla stream "Tell me a long story"

# Stream with session
claif-cla stream "Continue the story" --session SESSION_ID
```

### Interactive Mode
```bash
# Start interactive conversation
claif-cla interactive

# Interactive with specific session
claif-cla interactive --session my-session
```

### Session Management
```bash
# List all sessions
claif-cla session list

# Create new session
claif-cla session create

# Show session details
claif-cla session show SESSION_ID

# Export session
claif-cla session export SESSION_ID --format markdown --output conversation.md

# Branch session at specific point
claif-cla session branch SESSION_ID --point 5

# Merge sessions
claif-cla session merge TARGET_ID --other SOURCE_ID --strategy append
```

### Health and Benchmarking
```bash
# Check Claude service health
claif-cla health

# Benchmark performance
claif-cla benchmark --iterations 10 --model claude-3-opus-20240229
```

## Python API Usage

### Basic Usage
```python
import asyncio
from claif_cla import query, ClaifOptions

async def main():
    # Simple query
    async for message in query("Hello, Claude!"):
        print(message.content)
    
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
from claif_cla.session import SessionManager

# Create session manager
session_mgr = SessionManager()

# Create new session
session_id = session_mgr.create_session()

# Add messages to session
from claif.common import Message, MessageRole

message = Message(
    role=MessageRole.USER,
    content="Hello, Claude!"
)
session_mgr.add_message(session_id, message)

# Export session
markdown = session_mgr.export_session(session_id, format="markdown")
print(markdown)
```

### Tool Approval Strategies
```python
from claif_cla.approval import create_approval_strategy

# Allow all tools
strategy = create_approval_strategy("allow_all")

# Allow specific tools only
strategy = create_approval_strategy("allow_list", {
    "allowed_tools": ["read_file", "list_files", "search"]
})

# Deny dangerous tools
strategy = create_approval_strategy("deny_list", {
    "denied_tools": ["delete_file", "execute_command"]
})

# Interactive approval
strategy = create_approval_strategy("interactive", {
    "auto_approve_safe": True
})

# Conditional approval based on parameters
strategy = create_approval_strategy("conditional", {
    "conditions": {
        "read_file": {
            "path": {"allowed": ["/safe/directory"]}
        }
    }
})
```

### Advanced Wrapper Features
```python
from claif_cla.wrapper import ClaudeWrapper
from claif.common import Config

# Create wrapper with custom config
config = Config()
wrapper = ClaudeWrapper(config)

# Query with caching and retry
async for message in wrapper.query("Complex question"):
    print(message.content)
```

## Why Use CLAIF_CLA?

### 1. **Enhanced Claude Integration**
- Seamless integration with CLAIF framework
- All Claude features accessible through unified interface
- Automatic handling of claude-code-sdk specifics

### 2. **Advanced Session Management**
- Persistent conversation sessions
- Session branching and merging
- Multiple export formats (JSON, Markdown)
- Session templates for common use cases

### 3. **Sophisticated Tool Approval**
- Multiple approval strategies (allow-list, deny-list, patterns)
- Composite strategies with AND/OR logic
- Interactive approval with safe tool auto-approval
- Conditional approval based on tool parameters

### 4. **Production-Ready Features**
- Response caching to reduce API costs
- Retry logic with exponential backoff
- Comprehensive error handling
- Performance benchmarking tools

## How It Works

### Architecture

```
┌─────────────────────┐
│    CLAIF Core       │
├─────────────────────┤
│  Claude Provider    │
├─────────────────────┤
│    CLAIF_CLA        │
├─────────────────────┤
│  claude-code-sdk    │
├─────────────────────┤
│   Claude API        │
└─────────────────────┘
```

### Core Components

#### 1. **Main Module** (`__init__.py`)
Provides the main `query` function that:
- Converts CLAIF options to ClaudeCodeOptions
- Passes through to claude-code-sdk
- Yields normalized messages

#### 2. **Session Module** (`session.py`)
- `Session`: Manages conversation history and checkpoints
- `SessionManager`: Handles session persistence and operations
- `SessionTemplate`: Pre-configured session templates

#### 3. **Approval Module** (`approval.py`)
Implements various tool approval strategies:
- `AllowAllStrategy`: Approve all tool uses
- `DenyAllStrategy`: Deny all tool uses
- `AllowListStrategy`: Approve only listed tools
- `DenyListStrategy`: Deny only listed tools
- `PatternStrategy`: Approve based on regex patterns
- `CompositeStrategy`: Combine multiple strategies
- `InteractiveStrategy`: Ask user for approval
- `ConditionalStrategy`: Approve based on parameters

#### 4. **Wrapper Module** (`wrapper.py`)
- `ResponseCache`: LRU cache for API responses
- `ClaudeWrapper`: Enhanced wrapper with caching and retry

#### 5. **CLI Module** (`cli.py`)
Fire-based CLI providing:
- Query commands (ask, stream)
- Session management
- Health checks
- Benchmarking
- Interactive mode

### Configuration

CLAIF_CLA inherits configuration from CLAIF and adds:

```toml
[providers.claude]
model = "claude-3-opus-20240229"
api_key_env = "ANTHROPIC_API_KEY"

[claude.cache]
enabled = true
ttl = 3600

[claude.retry]
count = 3
delay = 1.0
backoff = 2.0

[claude.approval]
strategy = "interactive"
auto_approve_safe = true
```

### Message Flow

1. Query enters through CLAIF interface
2. CLAIF_CLA converts options to ClaudeCodeOptions
3. Request forwarded to claude-code-sdk
4. SDK communicates with Claude API
5. Responses converted to CLAIF Message format
6. Optional caching and session storage
7. Messages yielded to user

## Session Templates

CLAIF_CLA includes pre-configured session templates:

```python
from claif_cla.session import SessionTemplate

# Create code review session
session = SessionTemplate.create_from_template("code_review")

# Available templates:
# - code_review: Code analysis and review
# - debugging: Debug assistance
# - architecture: System design help
# - testing: Test writing assistance
```

## Contributing

To contribute to CLAIF_CLA:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Links

- [GitHub Repository](https://github.com/twardoch/claif_cla)
- [PyPI Package](https://pypi.org/project/claif_cla/)
- [CLAIF Framework](https://github.com/twardoch/claif)
- [Claude SDK](https://github.com/anthropics/claude-code-sdk)