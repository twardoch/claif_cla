#!/usr/bin/env python3
"""Windows-specific installation helper for Claude CLI."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def check_npm():
    """Check if npm is available."""
    return shutil.which("npm") is not None


def check_bun():
    """Check if bun is available."""
    return shutil.which("bun") is not None


def get_npm_global_path():
    """Get npm global installation path."""
    try:
        result = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, check=True)
        return Path(result.stdout.strip()).parent
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def install_with_npm():
    """Install Claude CLI using npm."""
    try:
        subprocess.run(["npm", "install", "-g", "@anthropic-ai/claude-code"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def install_with_bun():
    """Install Claude CLI using bun."""
    try:
        subprocess.run(["bun", "add", "-g", "@anthropic-ai/claude-code"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def create_wrapper_scripts():
    """Create Windows wrapper scripts in Claif bin directory."""
    claif_bin = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "claif" / "bin"
    claif_bin.mkdir(parents=True, exist_ok=True)

    # Find the installed claude location
    claude_cmd = shutil.which("claude")
    if not claude_cmd:
        npm_path = get_npm_global_path()
        if npm_path:
            claude_cmd = npm_path / "claude.cmd"
            if not claude_cmd.exists():
                claude_cmd = npm_path / "@anthropic-ai" / "claude-code" / "bin" / "claude"

    if not claude_cmd or not Path(claude_cmd).exists():
        return False

    # Create batch wrapper
    batch_wrapper = claif_bin / "claude.cmd"
    batch_content = f'''@echo off
"{claude_cmd}" %*
'''
    batch_wrapper.write_text(batch_content)

    # Create PowerShell wrapper
    ps_wrapper = claif_bin / "claude.ps1"
    ps_content = f'''& "{claude_cmd}" @args
exit $LASTEXITCODE
'''
    ps_wrapper.write_text(ps_content)

    # Add to PATH if not present
    current_path = os.environ.get("PATH", "")
    if str(claif_bin) not in current_path:
        pass

    return True


def main():
    """Main installation function."""
    if platform.system() != "Windows":
        sys.exit(1)

    # Check for package managers
    has_npm = check_npm()
    has_bun = check_bun()

    if not has_npm and not has_bun:
        sys.exit(1)

    # Try installation
    installed = False

    if has_bun:
        # Prefer bun for speed
        installed = install_with_bun()

    if not installed and has_npm:
        installed = install_with_npm()

    if not installed:
        sys.exit(1)

    # Create wrapper scripts
    if create_wrapper_scripts():
        pass
    else:
        pass

    # Test installation
    try:
        result = subprocess.run(["claude", "--version"], check=False, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
