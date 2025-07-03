"""Tool approval strategies for Claude, defining how tool use is authorized."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class ApprovalStrategy(ABC):
    """Abstract base class for tool approval strategies."""

    @abstractmethod
    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        """Determine if a tool use should be approved."""
        raise NotImplementedError

    def get_description(self) -> str:
        """Get a description of this strategy."""
        return self.__class__.__name__


class AllowAll(ApprovalStrategy):
    """Approve all tool uses."""

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        logger.debug(f"AllowAll: Approving {tool_name}")
        return True

    def get_description(self) -> str:
        return "Allow all tools"


class DenyAll(ApprovalStrategy):
    """Deny all tool uses."""

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        logger.debug(f"DenyAll: Denying {tool_name}")
        return False

    def get_description(self) -> str:
        return "Deny all tools"


class AllowList(ApprovalStrategy):
    """Approve tools from an allowed list."""

    def __init__(self, allowed_tools: list[str]):
        self.allowed_tools = set(allowed_tools)

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        approved = tool_name in self.allowed_tools
        logger.debug(f"AllowList: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        return f"Allow only: {', '.join(sorted(self.allowed_tools))}"


class DenyList(ApprovalStrategy):
    """Deny tools from a denied list."""

    def __init__(self, denied_tools: list[str]):
        self.denied_tools = set(denied_tools)

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        approved = tool_name not in self.denied_tools
        logger.debug(f"DenyList: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        return f"Deny only: {', '.join(sorted(self.denied_tools))}"


class Pattern(ApprovalStrategy):
    """Approve tools matching regex patterns."""

    def __init__(self, patterns: list[str], *, deny: bool = False):
        self.patterns: list[re.Pattern] = [re.compile(p) for p in patterns]
        self.deny = deny

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        matches = any(p.match(tool_name) for p in self.patterns)
        approved = not matches if self.deny else matches
        logger.debug(f"Pattern: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        action = "Deny" if self.deny else "Allow"
        return f"{action} patterns: {[p.pattern for p in self.patterns]}"


class Composite(ApprovalStrategy):
    """Combine multiple strategies with AND/OR logic."""

    def __init__(self, strategies: list[ApprovalStrategy], *, require_all: bool = False):
        self.strategies = strategies
        self.require_all = require_all

    def should_approve(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        if self.require_all:
            approved = all(s.should_approve(tool_name, tool_input) for s in self.strategies)
        else:
            approved = any(s.should_approve(tool_name, tool_input) for s in self.strategies)
        logger.debug(f"Composite: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        op = "AND" if self.require_all else "OR"
        descriptions = [s.get_description() for s in self.strategies]
        return f"({op.join(descriptions)})"


class Interactive(ApprovalStrategy):
    """Ask user for approval interactively."""

    def __init__(self, *, auto_approve_safe: bool = True) -> None:
        """
        Initializes the Interactive strategy.

        Args:
            auto_approve_safe: If True, automatically approves a predefined set of safe tools.
        """
        self.auto_approve_safe: bool = auto_approve_safe
        self.safe_tools: set[str] = {
            "ls",
            "cat",
            "search_code",
            "search_file",
            "view_file",
            "view_symbol",
        }

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        """
        Determines approval based on safety or by defaulting to denial in non-interactive mode.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy for direct approval).

        Returns:
            True if the tool is in the safe list and `auto_approve_safe` is True.
            False otherwise (as interactive prompting is not supported in this backend context).
        """
        if self.auto_approve_safe and tool_name in self.safe_tools:
            logger.debug(f"Interactive: Auto-approving safe tool {tool_name}")
            return True

        # In a non-interactive environment, we cannot prompt the user.
        # Therefore, any tool not auto-approved as safe is denied.
        logger.debug(f"Interactive: Tool {tool_name} would require user prompt, denying in non-interactive environment.")
        return False

    def get_description(self) -> str:
        """
        Returns a description for the Interactive strategy.
        """
        return "Interactive approval" + (" (auto-approve safe)" if self.auto_approve_safe else "")



