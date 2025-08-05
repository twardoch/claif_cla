---
# this_file: src_docs/md/cli/overview.md
title: Chapter 6 - CLI Usage & Commands
description: Complete CLI reference with interactive modes, batch operations, and configuration
---

# Chapter 6: CLI Usage & Commands

claif_cla provides a powerful command-line interface built with Python Fire, offering both interactive and batch processing capabilities for working with Claude AI.

## Command Overview

The CLI is accessible through multiple entry points:

```bash
# Primary command
claif-cla [command] [options]

# Alternative module access
python -m claif_cla.cli [command] [options]

# Direct module execution
python -m claif_cla [command] [options]
```

## Basic Commands

### query - Single Queries

Execute one-off queries with immediate responses:

```bash
# Simple query
claif-cla query "What is machine learning?"

# With model selection
claif-cla query "Explain quantum computing" --model claude-3-opus-20240229

# With parameters
claif-cla query "Write a poem" --temperature 0.9 --max-tokens 200

# JSON output
claif-cla query "What is 2+2?" --json-output
```

### chat - Interactive Mode

Start interactive conversations:

```bash
# Basic interactive mode
claif-cla chat

# With specific model
claif-cla chat --model claude-3-5-sonnet-20241022

# With session continuation
claif-cla chat --session SESSION_ID

# With custom system prompt
claif-cla chat --system "You are a Python expert"
```

### ask - Contextual Queries

Execute queries with session context:

```bash
# Ask with automatic session creation
claif-cla ask "Help me debug this code"

# Continue existing session
claif-cla ask "What about error handling?" --session SESSION_ID

# With file context
claif-cla ask "Review this code" --file script.py
```

## Session Commands

### session - Session Management

Complete session lifecycle management:

```bash
# List all sessions
claif-cla session list

# List with filtering
claif-cla session list --template coding --limit 10

# Create new session
claif-cla session create --title "Bug Investigation"

# Create with template
claif-cla session create --template coding --metadata '{"language": "python"}'

# Show session details
claif-cla session show SESSION_ID

# Show with message limit
claif-cla session show SESSION_ID --limit 5 --format json

# Delete session
claif-cla session delete SESSION_ID

# Delete with confirmation skip
claif-cla session delete SESSION_ID --force
```

### export - Session Export

Export conversations in various formats:

```bash
# Export as Markdown
claif-cla session export SESSION_ID --format markdown --output chat.md

# Export as JSON
claif-cla session export SESSION_ID --format json --output chat.json

# Export with metadata
claif-cla session export SESSION_ID --format markdown --include-metadata --include-timestamps

# Export to stdout
claif-cla session export SESSION_ID --format markdown
```

## Utility Commands

### models - Model Information

List and describe available models:

```bash
# List all models
claif-cla models

# Detailed model info
claif-cla models --detailed

# Model comparison
claif-cla models --compare
```

### health - System Health

Check system status and connectivity:

```bash
# Basic health check
claif-cla health

# Detailed diagnostics
claif-cla health --verbose

# API connectivity test
claif-cla health --test-api
```

### version - Version Information

Display version and system information:

```bash
# Version info
claif-cla version

# System information
claif-cla version --system

# Dependencies info
claif-cla version --deps
```

## Advanced Features

### Stream - Real-time Streaming

Stream responses for long-form content:

```bash
# Stream a response
claif-cla stream "Write a long essay about AI"

# Stream with model selection
claif-cla stream "Explain quantum physics" --model claude-3-opus-20240229

# Stream to file
claif-cla stream "Generate documentation" --output doc.md
```

### benchmark - Performance Testing

Test and benchmark API performance:

```bash
# Basic benchmark
claif-cla benchmark "Simple math question" --iterations 5

# Model comparison benchmark
claif-cla benchmark "Code review task" --models claude-3-haiku-20240307,claude-3-5-sonnet-20241022

# Detailed benchmarking
claif-cla benchmark "Complex analysis" --iterations 10 --verbose --output benchmark.json
```

### search - Content Search

Search through session content:

```bash
# Search all sessions
claif-cla search "machine learning" --limit 10

# Search with metadata filtering
claif-cla search "bug" --template coding --format json

# Search with time range
claif-cla search "python" --since "2024-01-01" --before "2024-02-01"
```

## Configuration Commands

### config - Configuration Management

Manage CLI configuration:

```bash
# Show current config
claif-cla config show

# Set configuration value
claif-cla config set default_model claude-3-5-sonnet-20241022

# List all settings
claif-cla config list

# Reset to defaults
claif-cla config reset
```

### install - Component Installation

Install and manage dependencies:

```bash
# Install Claude CLI
claif-cla install claude

# Check installation status
claif-cla install status

# Update components
claif-cla install update
```

## Output Formatting

### Format Options

Control output appearance and structure:

```bash
# Rich terminal output (default)
claif-cla query "Hello" --format rich

# Plain text output
claif-cla query "Hello" --format plain

# JSON output
claif-cla query "Hello" --format json

# YAML output
claif-cla query "Hello" --format yaml

# Table format (for lists)
claif-cla session list --format table
```

### Verbosity Control

Adjust output detail level:

```bash
# Quiet mode (minimal output)
claif-cla query "Hello" --quiet

# Verbose mode (detailed output)
claif-cla query "Hello" --verbose

# Debug mode (maximum detail)
claif-cla query "Hello" --debug
```

## Parameter Reference

### Global Parameters

Available for all commands:

| Parameter | Type | Description |
|-----------|------|-------------|
| `--model` | str | Claude model to use |
| `--temperature` | float | Sampling temperature (0.0-1.0) |
| `--max-tokens` | int | Maximum response tokens |
| `--top-p` | float | Nucleus sampling parameter |
| `--timeout` | int | Request timeout in seconds |
| `--retries` | int | Maximum retry attempts |
| `--format` | str | Output format (rich/plain/json/yaml) |
| `--output` | str | Output file path |
| `--verbose` | flag | Enable verbose output |
| `--quiet` | flag | Suppress non-essential output |
| `--debug` | flag | Enable debug logging |

### Query-Specific Parameters

For `query`, `ask`, and `stream` commands:

| Parameter | Type | Description |
|-----------|------|-------------|
| `--system` | str | System message/prompt |
| `--session` | str | Session ID to use |
| `--file` | str | Input file path |
| `--stream` | flag | Enable streaming output |
| `--json-output` | flag | Force JSON response format |
| `--include-usage` | flag | Include token usage info |

### Session Parameters

For session management commands:

| Parameter | Type | Description |
|-----------|------|-------------|
| `--title` | str | Session title |
| `--template` | str | Session template name |
| `--metadata` | str | JSON metadata string |
| `--limit` | int | Limit number of results |
| `--include-metadata` | flag | Include metadata in output |
| `--include-timestamps` | flag | Include timestamps |
| `--force` | flag | Skip confirmation prompts |

## Interactive Mode Features

### Chat Interface

The interactive chat mode provides:

```bash
claif-cla chat
```

**Features:**
- Multi-line input support
- Command history
- Tab completion
- Session persistence
- Real-time streaming
- Rich text formatting

**Interactive Commands:**
```
/help          - Show help
/history       - Show message history
/clear         - Clear screen
/save          - Save current session
/load ID       - Load session by ID
/export FORMAT - Export current session
/model NAME    - Switch model
/quit          - Exit chat
```

### Batch Mode

Process multiple inputs efficiently:

```bash
# From file
claif-cla batch --input queries.txt --output responses.json

# From stdin
echo "What is AI?" | claif-cla batch --format json

# Multiple queries
claif-cla batch \
    --queries "What is Python?" "What is JavaScript?" \
    --model claude-3-haiku-20240307 \
    --output batch_results.json
```

## Configuration Files

### Global Configuration

Location: `~/.claif/config.json`

```json
{
    "default_model": "claude-3-5-sonnet-20241022",
    "default_temperature": 0.7,
    "default_max_tokens": 1000,
    "session_dir": "~/.claif/sessions",
    "auto_save": true,
    "output_format": "rich",
    "verbose": false,
    "api": {
        "timeout": 120,
        "max_retries": 3,
        "base_url": null
    },
    "display": {
        "colors": true,
        "width": 80,
        "pager": "auto"
    }
}
```

### Project Configuration

Location: `.claif.json` (in project directory)

```json
{
    "model": "claude-3-opus-20240229",
    "system_message": "You are a helpful coding assistant for this Python project.",
    "session_template": "coding",
    "metadata": {
        "project": "my-app",
        "language": "python"
    }
}
```

## Scripting and Automation

### Shell Integration

Add to your shell profile for enhanced experience:

```bash
# Bash/Zsh completion
eval "$(claif-cla completion bash)"  # or zsh

# Aliases
alias claude="claif-cla query"
alias claudec="claif-cla chat"
alias claudes="claif-cla session"

# Functions
claude_file() {
    claif-cla ask "Review this file: $(cat $1)" --file "$1"
}

claude_commit() {
    local diff=$(git diff --staged)
    claif-cla query "Generate a commit message for: $diff" --max-tokens 50
}
```

### Environment Variables

```bash
# API Configuration
export ANTHROPIC_API_KEY="your-key"
export CLAIF_DEFAULT_MODEL="claude-3-5-sonnet-20241022"
export CLAIF_SESSION_DIR="$HOME/.local/share/claif/sessions"

# CLI Behavior
export CLAIF_OUTPUT_FORMAT="rich"
export CLAIF_VERBOSE="false"
export CLAIF_AUTO_SAVE="true"
```

### Pipeline Integration

```bash
# Code review pipeline
git diff HEAD~1 | claif-cla query "Review these changes" --stream

# Documentation generation
find . -name "*.py" -exec claif-cla ask "Document this file: $(cat {})" --output docs/{}.md \;

# Log analysis
tail -f app.log | claif-cla stream "Analyze these logs for issues"
```

## Error Handling

### Common Issues and Solutions

```bash
# API key issues
claif-cla health --test-api
# Check: echo $ANTHROPIC_API_KEY

# Session not found
claif-cla session list --verbose
# Shows available sessions and paths

# Model not available
claif-cla models --detailed
# Lists all available models

# Timeout issues
claif-cla query "test" --timeout 300
# Increase timeout for complex queries

# Permission issues
ls -la ~/.claif/
# Check session directory permissions
```

### Debug Mode

Enable comprehensive debugging:

```bash
# Debug specific command
claif-cla query "test" --debug

# Debug with log file
claif-cla query "test" --debug --log debug.log

# Debug environment
export LOGURU_LEVEL=DEBUG
claif-cla query "test"
```

## Performance Tips

### Optimization Strategies

```bash
# Use faster models for simple tasks
claif-cla query "simple question" --model claude-3-haiku-20240307

# Batch similar queries
claif-cla batch --input questions.txt --model claude-3-haiku-20240307

# Limit response length
claif-cla query "explain briefly" --max-tokens 100

# Use sessions for context reuse
claif-cla ask "continue" --session existing_session_id
```

### Resource Management

```bash
# Clean old sessions
claif-cla session clean --older-than 30d

# Compact session storage
claif-cla session compact

# Monitor usage
claif-cla stats --usage --time-range 30d
```

The CLI provides a powerful, flexible interface for all your Claude AI interactions! 🖥️