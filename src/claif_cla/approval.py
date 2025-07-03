"""MCP tool approval strategies for Claude."""

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

    def __init__(self, *, auto_approve_safe: bool = True):
        self.auto_approve_safe = auto_approve_safe
        self.safe_tools = {
            "ls",
            "cat",
            "search_code",
            "search_file",
            "view_file",
            "view_symbol",
        }

    def should_approve(self, tool_name: str, _tool_input: dict[str, Any]) -> bool:
        if self.auto_approve_safe and tool_name in self.safe_tools:
            logger.debug(f"Interactive: Auto-approving safe tool {tool_name}")
            return True

        # Fallback to interactive prompt (not implemented for backend)
        logger.debug(f"Interactive: Would prompt for {tool_name}")
        return False  # Default to deny in non-interactive environments

    def get_description(self) -> str:
        return "Interactive approval" + (" (auto-approve safe)" if self.auto_approve_safe else "")


"""MCP tool approval strategies for Claude."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Union

from loguru import logger


class ApprovalStrategy(ABC):
    """
    Abstract base class for defining tool approval strategies.

    Concrete implementations of this class determine whether a given tool
    invocation should be approved or denied based on specific criteria.
    """

    @abstractmethod
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """
        Determines if a tool use should be approved.

        Args:
            tool_name: The name of the tool being invoked.
            tool_input: A dictionary containing the input arguments for the tool.

        Returns:
            True if the tool use is approved, False otherwise.
        """
        raise NotImplementedError

    def get_description(self) -> str:
        """
        Provides a human-readable description of the approval strategy.

        Returns:
            A string describing the strategy.
        """
        return self.__class__.__name__


class AllowAll(ApprovalStrategy):
    """
    An approval strategy that unconditionally approves all tool uses.
    """

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
        """
        Always returns True, approving any tool use.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy).

        Returns:
            True.
        """
        logger.debug(f"AllowAll: Approving {tool_name}")
        return True

    def get_description(self) -> str:
        """
        Returns a description for the AllowAll strategy.
        """
        return "Allow all tools"


class DenyAll(ApprovalStrategy):
    """
    An approval strategy that unconditionally denies all tool uses.
    """

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
        """
        Always returns False, denying any tool use.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy).

        Returns:
            False.
        """
        logger.debug(f"DenyAll: Denying {tool_name}")
        return False

    def get_description(self) -> str:
        """
        Returns a description for the DenyAll strategy.
        """
        return "Deny all tools"


class AllowList(ApprovalStrategy):
    """
    An approval strategy that approves only tools explicitly present in a predefined list.
    """

    def __init__(self, allowed_tools: List[str]) -> None:
        """
        Initializes the AllowList strategy.

        Args:
            allowed_tools: A list of tool names that are permitted.
        """
        self.allowed_tools: Set[str] = set(allowed_tools)

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
        """
        Approves the tool if its name is in the `allowed_tools` set.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy).

        Returns:
            True if the tool is in the allow list, False otherwise.
        """
        approved: bool = tool_name in self.allowed_tools
        logger.debug(f"AllowList: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        """
        Returns a description for the AllowList strategy, including the allowed tools.
        """
        return f"Allow only: {', '.join(sorted(self.allowed_tools))}"


class DenyList(ApprovalStrategy):
    """
    An approval strategy that denies tools explicitly present in a predefined list.
    All other tools are implicitly approved.
    """

    def __init__(self, denied_tools: List[str]) -> None:
        """
        Initializes the DenyList strategy.

        Args:
            denied_tools: A list of tool names that are not permitted.
        """
        self.denied_tools: Set[str] = set(denied_tools)

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
        """
        Denies the tool if its name is in the `denied_tools` set.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy).

        Returns:
            True if the tool is NOT in the deny list, False otherwise.
        """
        approved: bool = tool_name not in self.denied_tools
        logger.debug(f"DenyList: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        """
        Returns a description for the DenyList strategy, including the denied tools.
        """
        return f"Deny only: {', '.join(sorted(self.denied_tools))}"


class Pattern(ApprovalStrategy):
    """
    An approval strategy that approves or denies tools based on regular expression patterns.
    """

    def __init__(self, patterns: List[str], *, deny: bool = False) -> None:
        """
        Initializes the Pattern strategy.

        Args:
            patterns: A list of regular expression strings to match against tool names.
            deny: If True, tools matching the patterns are denied; otherwise, they are approved.
        """
        self.patterns: List[re.Pattern] = [re.compile(p) for p in patterns]
        self.deny: bool = deny

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
        """
        Determines approval based on whether the tool name matches any of the patterns.

        Args:
            tool_name: The name of the tool.
            _tool_input: The input arguments (ignored by this strategy).

        Returns:
            True if the tool is approved, False otherwise.
        """
        matches: bool = any(p.match(tool_name) for p in self.patterns)
        approved: bool = not matches if self.deny else matches
        logger.debug(f"Pattern: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        """
        Returns a description for the Pattern strategy, indicating the action and patterns.
        """
        action: str = "Deny" if self.deny else "Allow"
        return f"{action} patterns: {[p.pattern for p in self.patterns]}"


class Composite(ApprovalStrategy):
    """
    An approval strategy that combines multiple other strategies using logical AND or OR.
    """

    def __init__(self, strategies: List[ApprovalStrategy], *, require_all: bool = False) -> None:
        """
        Initializes the Composite strategy.

        Args:
            strategies: A list of `ApprovalStrategy` instances to combine.
            require_all: If True, all strategies must approve (AND logic). If False,
                         at least one strategy must approve (OR logic).
        """
        self.strategies: List[ApprovalStrategy] = strategies
        self.require_all: bool = require_all

    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """
        Determines approval based on the combined logic of its constituent strategies.

        Args:
            tool_name: The name of the tool.
            tool_input: The input arguments for the tool.

        Returns:
            True if the tool is approved based on the composite logic, False otherwise.
        """
        if self.require_all:
            # All strategies must approve for the composite to approve (AND logic).
            approved: bool = all(s.should_approve(tool_name, tool_input) for s in self.strategies)
        else:
            # At least one strategy must approve for the composite to approve (OR logic).
            approved: bool = any(s.should_approve(tool_name, tool_input) for s in self.strategies)
        logger.debug(f"Composite: {tool_name} {'approved' if approved else 'denied'}")
        return approved

    def get_description(self) -> str:
        """
        Returns a description for the Composite strategy, detailing its logic and sub-strategies.
        """
        op: str = "AND" if self.require_all else "OR"
        descriptions: List[str] = [s.get_description() for s in self.strategies]
        return f"({op.join(descriptions)})"


class Interactive(ApprovalStrategy):
    """
    An approval strategy that, in an interactive environment, would prompt the user for approval.

    In a non-interactive (backend) environment, this strategy will deny tool uses
    unless they are explicitly marked as "safe" and `auto_approve_safe` is True.
    """

    def __init__(self, *, auto_approve_safe: bool = True) -> None:
        """
        Initializes the Interactive strategy.

        Args:
            auto_approve_safe: If True, automatically approves a predefined set of safe tools.
        """
        self.auto_approve_safe: bool = auto_approve_safe
        self.safe_tools: Set[str] = {
            "ls",
            "cat",
            "search_code",
            "search_file",
            "view_file",
            "view_symbol",
        }

    def should_approve(self, tool_name: str, _tool_input: Dict[str, Any]) -> bool:
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


class ConditionalStrategy(ApprovalStrategy):
    """
    An approval strategy that approves or denies tool uses based on conditions
    applied to their input arguments.
    """

    def __init__(self, conditions: Dict[str, Any]) -> None:
        """
        Initializes the ConditionalStrategy.

        Args:
            conditions: A dictionary where keys are tool names and values are
                        dictionaries of parameter conditions.
                        Example: `{"read_file": {"path": {"allowed": ["/app/data"]}}}`
        """
        self.conditions: Dict[str, Any] = conditions

    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """
        Determines approval by checking if tool input parameters meet specified conditions.

        If a tool has no specific conditions defined, it is approved by default.

        Args:
            tool_name: The name of the tool.
            tool_input: The input arguments for the tool.

        Returns:
            True if the tool is approved based on its input conditions, False otherwise.
        """
        # If the tool has no specific conditions defined, it is approved by default.
        if tool_name not in self.conditions:
            logger.debug(f"Conditional: No specific conditions for {tool_name}, approving.")
            return True

        tool_conditions: Dict[str, Any] = self.conditions[tool_name]

        # Iterate through each parameter's conditions for the given tool.
        for param, condition in tool_conditions.items():
            # If the parameter is not present in the tool_input, it cannot violate the condition.
            if param not in tool_input:
                continue

            value: Any = tool_input[param]

            # Handle different types of conditions (e.g., range, allowed values).
            if isinstance(condition, dict):
                if "max" in condition and value > condition["max"]:
                    logger.debug(f"Conditional: {tool_name} denied - parameter '{param}' ({value}) exceeds max ({condition["max"]})")
                    return False
                if "min" in condition and value < condition["min"]:
                    logger.debug(f"Conditional: {tool_name} denied - parameter '{param}' ({value}) below min ({condition["min"]})")
                    return False
                if "allowed" in condition and value not in condition["allowed"]:
                    logger.debug(f"Conditional: {tool_name} denied - parameter '{param}' ({value}) not in allowed list ({condition["allowed"]})")
                    return False
            elif isinstance(condition, list) and value not in condition:
                logger.debug(f"Conditional: {tool_name} denied - parameter '{param}' ({value}) not in allowed values ({condition})")
                return False

        # If all conditions are met (or no conditions are violated), approve the tool.
        logger.debug(f"Conditional: {tool_name} approved based on conditions.")
        return True

    def get_description(self) -> str:
        """
        Returns a description for the ConditionalStrategy, summarizing its conditions.
        """
        return f"Conditional approval for {list(self.conditions.keys())}"


def create_approval_strategy(
    strategy_type: str,
    config: Optional[Dict[str, Any]] = None,
) -> ApprovalStrategy:
    """
    Factory function to create instances of `ApprovalStrategy` based on a type string and configuration.

    Args:
        strategy_type: A string representing the type of strategy to create (e.g.,
                       "allow_all", "deny_list", "composite").
        config: Optional. A dictionary containing configuration parameters specific
                to the chosen strategy type.

    Returns:
        An instance of a concrete `ApprovalStrategy` subclass.

    Raises:
        ValueError: If an unknown strategy type is provided.
    """
    config = config or {}

    if strategy_type == "allow_all":
        return AllowAll()

    if strategy_type == "deny_all":
        return DenyAll()

    if strategy_type == "allow_list":
        allowed: List[str] = config.get("allowed_tools", [])
        return AllowList(allowed)

    if strategy_type == "deny_list":
        denied: List[str] = config.get("denied_tools", [])
        return DenyList(denied)

    if strategy_type == "pattern":
        patterns: List[str] = config.get("patterns", [])
        deny: bool = config.get("deny", False)
        return Pattern(patterns, deny=deny)

    if strategy_type == "composite":
        strategies: List[ApprovalStrategy] = []
        for s_config in config.get("strategies", []):
            s_type: str = s_config.get("type")
            s_cfg: Dict[str, Any] = s_config.get("config", {})
            strategies.append(create_approval_strategy(s_type, s_cfg))
        require_all: bool = config.get("require_all", False)
        return Composite(strategies, require_all=require_all)

    if strategy_type == "interactive":
        auto_approve_safe: bool = config.get("auto_approve_safe", True)
        return Interactive(auto_approve_safe=auto_approve_safe)

    if strategy_type == "conditional":
        conditions: Dict[str, Any] = config.get("conditions", {})
        return ConditionalStrategy(conditions)

    msg = f"Unknown strategy type: {strategy_type}"
    logger.error(msg)
    raise ValueError(msg)


# Predefined strategy configurations for common use cases.
STRATEGY_PRESETS: Dict[str, Dict[str, Any]] = {
    "development": {
        "type": "composite",
        "config": {
            "strategies": [
                {"type": "deny_list", "config": {"denied_tools": ["delete_file", "execute_command"]}},
                {"type": "pattern", "config": {"patterns": [".*_prod.*"], "deny": True}},
            ],
            "require_all": True,
        },
    },
    "production": {
        "type": "composite",
        "config": {
            "strategies": [
                {"type": "allow_list", "config": {"allowed_tools": ["read_file", "list_files", "search"]}},
                {"type": "conditional", "config": {"conditions": {"read_file": {"path": {"allowed": ["/app/data"]}}}}},
            ],
            "require_all": True,
        },
    },
    "testing": {
        "type": "allow_all",
        "config": {},
    },
}


def create_approval_strategy(
    strategy_type: str,
    config: dict[str, Any] | None = None,
) -> ApprovalStrategy:
    """Factory function to create approval strategies."""
    config = config or {}

    if strategy_type == "allow_all":
        return AllowAll()

    if strategy_type == "deny_all":
        return DenyAll()

    if strategy_type == "allow_list":
        allowed = config.get("allowed_tools", [])
        return AllowList(allowed)

    if strategy_type == "deny_list":
        denied = config.get("denied_tools", [])
        return DenyList(denied)

    if strategy_type == "pattern":
        patterns = config.get("patterns", [])
        deny = config.get("deny", False)
        return Pattern(patterns, deny=deny)

    if strategy_type == "composite":
        strategies = []
        for s_config in config.get("strategies", []):
            s_type = s_config.get("type")
            s_cfg = s_config.get("config", {})
            strategies.append(create_approval_strategy(s_type, s_cfg))
        require_all = config.get("require_all", False)
        return Composite(strategies, require_all=require_all)

    if strategy_type == "interactive":
        auto_approve_safe = config.get("auto_approve_safe", True)
        return Interactive(auto_approve_safe=auto_approve_safe)

    if strategy_type == "conditional":
        conditions = config.get("conditions", {})
        return ConditionalStrategy(conditions)

    msg = f"Unknown strategy type: {strategy_type}"
    raise ValueError(msg)


# Predefined strategy configurations
STRATEGY_PRESETS = {
    "development": {
        "type": "composite",
        "config": {
            "strategies": [
                {"type": "deny_list", "config": {"denied_tools": ["delete_file", "execute_command"]}},
                {"type": "pattern", "config": {"patterns": [".*_prod.*"], "deny": True}},
            ],
            "require_all": True,
        },
    },
    "production": {
        "type": "composite",
        "config": {
            "strategies": [
                {"type": "allow_list", "config": {"allowed_tools": ["read_file", "list_files", "search"]}},
                {"type": "conditional", "config": {"conditions": {"read_file": {"path": {"allowed": ["/app/data"]}}}}},
            ],
            "require_all": True,
        },
    },
    "testing": {
        "type": "allow_all",
        "config": {},
    },
}
