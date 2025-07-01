# this_file: claif_cla/src/claif_cla/install.py

from pathlib import Path
from typing import Optional

from loguru import logger

# Import common install functionality
try:
    from claif.install import (
        ensure_bun_installed,
        get_install_location,
        install_npm_package_globally,
        bundle_all_tools,
        install_claude_bundled,
        uninstall_tool,
    )
except ImportError:
    # Fallback if claif package not available
    logger.warning("claif package not found, using local implementations")
    from .install_fallback import (
        ensure_bun_installed,
        get_install_location,
        install_npm_package_globally,
        bundle_all_tools,
        install_claude_bundled,
        uninstall_tool,
    )


def install_claude() -> dict:
    """Install Claude CLI with bundled approach."""
    if not ensure_bun_installed():
        return {"installed": [], "failed": ["claude"], "message": "bun installation failed"}

    install_dir = get_install_location()

    # Install npm package globally first
    logger.info("Installing @anthropic-ai/claude-code...")
    if not install_npm_package_globally("@anthropic-ai/claude-code"):
        return {"installed": [], "failed": ["claude"], "message": "@anthropic-ai/claude-code installation failed"}

    # Bundle all tools (this creates the dist directory with all tools)
    logger.info("Bundling CLI tools...")
    dist_dir = bundle_all_tools()
    if not dist_dir:
        return {"installed": [], "failed": ["claude"], "message": "bundling failed"}

    # Install Claude specifically
    logger.info("Installing claude...")
    if install_claude_bundled(install_dir, dist_dir):
        logger.success("🎉 Claude installed successfully!")
        logger.info(f"You can now use 'claude' command from anywhere")
        return {"installed": ["claude"], "failed": []}
    else:
        return {"installed": [], "failed": ["claude"], "message": "claude installation failed"}


def uninstall_claude() -> dict:
    """Uninstall Claude CLI."""
    logger.info("Uninstalling claude...")

    if uninstall_tool("claude"):
        logger.success("✓ Claude uninstalled successfully")
        return {"uninstalled": ["claude"], "failed": []}
    else:
        return {"uninstalled": [], "failed": ["claude"], "message": "claude uninstallation failed"}


def is_claude_installed() -> bool:
    """Check if Claude is installed."""
    install_dir = get_install_location()
    claude_executable = install_dir / "claude"
    claude_dir = install_dir / "claude"

    return (claude_executable.exists() and claude_executable.is_file()) or (claude_dir.exists() and claude_dir.is_dir())


def get_claude_status() -> dict:
    """Get Claude installation status."""
    if is_claude_installed():
        install_dir = get_install_location()
        claude_path = install_dir / "claude"
        return {"installed": True, "path": str(claude_path), "type": "bundled (claif-owned)"}
    else:
        return {"installed": False, "path": None, "type": None}
