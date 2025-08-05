---
# this_file: src_docs/md/getting-started/installation.md
title: Chapter 1 - Getting Started & Installation
description: Complete installation guide for claif_cla including system requirements, environment setup, and troubleshooting
---

# Chapter 1: Getting Started & Installation

This chapter provides comprehensive guidance for installing and setting up claif_cla in your development environment.

## System Requirements

### Python Version
- **Python 3.10+** (3.10, 3.11, 3.12 supported)
- **CPython** or **PyPy** implementation

### Operating Systems
- **Linux** (Ubuntu 20.04+, CentOS 8+, Arch Linux)
- **macOS** (10.15+ Catalina or newer)
- **Windows** (10/11, PowerShell or Command Prompt)

### Dependencies
claif_cla has minimal core dependencies:
- `openai>=1.0.0` - OpenAI client compatibility
- `anthropic>=0.18.0` - Anthropic API client
- `python-fire` - CLI framework
- `rich>=13.9.4` - Terminal formatting
- `loguru>=0.7.0` - Logging
- `httpx` - HTTP client
- `pydantic>=2.0.0` - Data validation

## Installation Methods

### 1. Basic Installation (Recommended)

Install claif_cla from PyPI using pip:

```bash
# Core package only
pip install claif_cla

# Verify installation
python -c "import claif_cla; print(f'claif_cla version: {claif_cla.__version__}')"
```

### 2. Installation with Claif Framework

For full ecosystem integration:

```bash
# Install with main Claif framework
pip install claif claif_cla

# Verify both packages
python -c "import claif, claif_cla; print('Both packages installed successfully')"
```

### 3. Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/twardoch/claif_cla.git
cd claif_cla

# Install in development mode with all extras
pip install -e ".[dev,test,docs,all]"

# Verify development setup
python -m pytest --version
uvx hatch --version
```

### 4. Using uv (Ultra-fast Alternative)

For faster dependency resolution:

```bash
# Install uv if not already available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install claif_cla with uv
uv pip install claif_cla

# Development installation with uv
uv pip install -e ".[dev,test]"
```

## Claude CLI Installation

claif_cla requires the Claude CLI for full functionality. Multiple installation options:

### Automatic Installation (Recommended)

```bash
# Using claif_cla installer
python -m claif_cla.install

# Or using Claif framework installer (if installed)
claif install claude
```

### Manual Installation via npm

```bash
# Install Node.js and npm first (if not available)
# Then install Claude CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Alternative: Bun Installation (Faster)

```bash
# Install Bun (if not available)
curl -fsSL https://bun.sh/install | bash

# Install Claude CLI with Bun
bun install -g @anthropic-ai/claude-code

# Create standalone executable (optional)
bun compile claude
```

## Environment Configuration

### API Key Setup

claif_cla requires an Anthropic API key:

```bash
# Option 1: Environment variable (recommended)
export ANTHROPIC_API_KEY="your-api-key-here"

# Option 2: In your shell profile (.bashrc, .zshrc, etc.)
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# Option 3: .env file in your project
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

!!! warning "Security Note"
    Never commit API keys to version control. Use environment variables or secure secret management systems.

### Optional Environment Variables

```bash
# Custom session directory
export CLAIF_SESSION_DIR="$HOME/.local/share/claif/sessions"

# Default cache TTL (in seconds)
export CLAIF_CACHE_TTL=3600

# Default Claude model
export CLAIF_DEFAULT_MODEL="claude-3-5-sonnet-20241022"

# Logging level
export LOGURU_LEVEL="INFO"
```

### Configuration File

Create a global configuration file:

```bash
# Create config directory
mkdir -p ~/.claif

# Create config file
cat > ~/.claif/config.json << 'EOF'
{
    "providers": {
        "claude": {
            "model": "claude-3-5-sonnet-20241022",
            "api_key_env": "ANTHROPIC_API_KEY",
            "cache_ttl": 3600,
            "enable_cache": true,
            "session_dir": "~/.claif/sessions"
        }
    },
    "cli": {
        "default_output": "rich",
        "verbose": false,
        "color": true
    }
}
EOF
```

## Verification & Testing

### Basic Functionality Test

```python
#!/usr/bin/env python3
"""Test basic claif_cla functionality"""

import os
from claif_cla import ClaudeClient

def test_installation():
    """Test that claif_cla is properly installed and configured"""
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False
    
    print(f"✅ API key configured: {api_key[:8]}...")
    
    # Test client initialization
    try:
        client = ClaudeClient()
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False
    
    # Test basic query (requires valid API key)
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Hello from claif_cla!'"}],
            model="claude-3-5-sonnet-20241022",
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print(f"✅ API call successful: {content[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

if __name__ == "__main__":
    success = test_installation()
    exit(0 if success else 1)
```

Save as `test_installation.py` and run:

```bash
python test_installation.py
```

### CLI Functionality Test

```bash
# Test CLI is installed
claif-cla --help

# Test basic query (requires API key)
claif-cla query "What is 2+2?" --model claude-3-haiku-20240307

# Test session management
claif-cla session list

# Test health check
python -m claif_cla.cli health
```

## Troubleshooting

### Common Installation Issues

#### 1. Python Version Compatibility

```bash
# Check Python version
python --version

# If using Python < 3.10, upgrade:
# - macOS: brew install python@3.12
# - Ubuntu: sudo apt install python3.12
# - Windows: Download from python.org
```

#### 2. Permission Errors

```bash
# Linux/macOS: Use user installation
pip install --user claif_cla

# Or use virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install claif_cla
```

#### 3. Network/Proxy Issues

```bash
# Configure pip for proxy
pip install --proxy http://proxy.company.com:8080 claif_cla

# Or use corporate certificate bundle
pip install --cert /path/to/cert.pem claif_cla
```

#### 4. Claude CLI Not Found

```bash
# Check if Claude CLI is in PATH
which claude  # Linux/macOS
where claude  # Windows

# If not found, add to PATH or reinstall
npm install -g @anthropic-ai/claude-code
```

### Runtime Issues

#### 1. API Key Problems

```python
# Test API key validity
import os
from anthropic import Anthropic

try:
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    # This will raise an exception if key is invalid
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=10,
        messages=[{"role": "user", "content": "test"}]
    )
    print("✅ API key is valid")
except Exception as e:
    print(f"❌ API key issue: {e}")
```

#### 2. Import Errors

```python
# Check all dependencies are installed
try:
    import openai, anthropic, fire, rich, loguru, httpx, pydantic
    print("✅ All dependencies available")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install claif_cla[all]")
```

#### 3. Session Directory Issues

```bash
# Check session directory permissions
ls -la ~/.claif/sessions/

# Create if missing
mkdir -p ~/.claif/sessions
chmod 755 ~/.claif/sessions
```

### Getting Help

#### Debug Mode

```bash
# Enable verbose logging
export LOGURU_LEVEL=DEBUG
claif-cla query "test" --verbose

# Or in Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Version Information

```bash
# Check installed versions
pip show claif_cla
python -m claif_cla.cli version

# Check system info
python -m claif_cla.cli system-info
```

#### Support Channels

- **GitHub Issues**: [Report bugs](https://github.com/twardoch/claif_cla/issues)
- **Discussions**: [Ask questions](https://github.com/twardoch/claif_cla/discussions)
- **Documentation**: [Read more guides](https://twardoch.github.io/claif_cla/)

## Next Steps

Once installation is complete:

1. **[Quick Start Guide](quickstart.md)** - Learn basic usage patterns
2. **[Basic Examples](examples.md)** - Try practical examples
3. **[API Reference](../api/openai-compatibility.md)** - Understand the API
4. **[CLI Usage](../cli/overview.md)** - Master the command-line interface

---

## Installation Checklist

- [ ] Python 3.10+ installed and verified
- [ ] claif_cla package installed via pip
- [ ] Claude CLI installed and accessible
- [ ] ANTHROPIC_API_KEY environment variable set
- [ ] Basic functionality test passed
- [ ] CLI commands working
- [ ] Session directory created and writable
- [ ] Configuration file created (optional)

Congratulations! You're ready to start using claif_cla. 🎉