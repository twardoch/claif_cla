from .cli import ClaudeCLI
from .cli import main
from .approval import create_approval_strategy
from .approval import STRATEGY_PRESETS
from .install import install_claude, uninstall_claude, is_claude_installed, get_claude_status
from .session import SessionManager

__all__ = [
    "ClaudeCLI",
    "main",
    "STRATEGY_PRESETS",
    "create_approval_strategy",
    "install_claude",
    "uninstall_claude",
    "is_claude_installed",
    "get_claude_status",
    "SessionManager",
]