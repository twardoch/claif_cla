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
                {"type": "allow_list", "config": {"allowed_tools": ["read_file", "list_files"]}},
                {"type": "conditional", "config": {"conditions": {"read_file": {"path": {"allowed": ["/app/data"]}}}}},
            ],
            "require_all": True,
        },
    },
    "testing": {"type": "allow_all"},
}


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
        logger.debug(
            f"Interactive: Tool {tool_name} would require user prompt, denying in non-interactive environment."
        )
        return False

    def get_description(self) -> str:
        """
        Returns a description for the Interactive strategy.
        """
        return "Interactive approval" + (" (auto-approve safe)" if self.auto_approve_safe else "")


class ConditionalStrategy(ApprovalStrategy):
    """Approve tools based on conditional logic on tool inputs."""

    def __init__(self, conditions: dict[str, dict[str, Any]]):
        """
        Initialize conditional strategy.

        Args:
            conditions: Tool conditions mapping tool names to parameter constraints.
                       Format: {"tool_name": {"param": {"max": 10, "allowed": ["value1", "value2"]}}}
        """
        self.conditions = conditions

    def should_approve(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """
        Check if tool approval meets conditions.

        Args:
            tool_name: Name of the tool.
            tool_input: Input parameters for the tool.

        Returns:
            True if all conditions are met or no conditions defined for tool.
        """
        if tool_name not in self.conditions:
            # No conditions defined, allow by default
            logger.debug(f"ConditionalStrategy: No conditions for {tool_name}, approving")
            return True

        tool_conditions = self.conditions[tool_name]
        for param_name, constraints in tool_conditions.items():
            if param_name not in tool_input:
                # If parameter is missing and has conditions, approve only if no required constraints
                # Check if this parameter has required constraints (min, max, allowed)
                if isinstance(constraints, dict) and any(key in constraints for key in ["min", "max", "allowed"]):
                    # Missing parameter with constraints, but allow if it's just a max constraint
                    if "max" in constraints and len(constraints) == 1:
                        logger.debug(f"ConditionalStrategy: Missing optional param {param_name} for {tool_name}, allowing")
                        continue
                    logger.debug(f"ConditionalStrategy: Missing required param {param_name} for {tool_name}")
                    return False
                elif isinstance(constraints, list):
                    # Missing parameter with allowed list
                    logger.debug(f"ConditionalStrategy: Missing required param {param_name} for {tool_name}")
                    return False
                continue

            param_value = tool_input[param_name]
            
            # Handle constraints as either dict or list
            if isinstance(constraints, list):
                # Allowed values as list format
                if param_value not in constraints:
                    logger.debug(f"ConditionalStrategy: {param_name}={param_value} not in allowed list for {tool_name}")
                    return False
            elif isinstance(constraints, dict):
                # Check allowed values
                if "allowed" in constraints:
                    if param_value not in constraints["allowed"]:
                        logger.debug(f"ConditionalStrategy: {param_name}={param_value} not in allowed list for {tool_name}")
                        return False

                # Check max value
                if "max" in constraints:
                    try:
                        if float(param_value) > constraints["max"]:
                            logger.debug(f"ConditionalStrategy: {param_name}={param_value} exceeds max {constraints['max']} for {tool_name}")
                            return False
                    except (ValueError, TypeError):
                        logger.debug(f"ConditionalStrategy: Cannot compare {param_name}={param_value} to max for {tool_name}")
                        return False

                # Check min value
                if "min" in constraints:
                    try:
                        if float(param_value) < constraints["min"]:
                            logger.debug(f"ConditionalStrategy: {param_name}={param_value} below min {constraints['min']} for {tool_name}")
                            return False
                    except (ValueError, TypeError):
                        logger.debug(f"ConditionalStrategy: Cannot compare {param_name}={param_value} to min for {tool_name}")
                        return False

        logger.debug(f"ConditionalStrategy: All conditions met for {tool_name}")
        return True

    def get_description(self) -> str:
        """Get description of conditional strategy."""
        tool_names = sorted(self.conditions.keys())
        return f"Conditional approval for {tool_names}"


def create_approval_strategy(strategy_type: str, config: dict[str, Any] | None = None) -> ApprovalStrategy:
    """
    Factory function to create approval strategies.

    Args:
        strategy_type: Type of strategy to create.
        config: Configuration parameters for the strategy.

    Returns:
        Configured approval strategy instance.

    Raises:
        ValueError: If strategy_type is unknown.
    """
    config = config or {}

    match strategy_type:
        case "allow_all":
            return AllowAll()
        
        case "deny_all":
            return DenyAll()
        
        case "allow_list":
            allowed_tools = config.get("allowed_tools", [])
            return AllowList(allowed_tools)
        
        case "deny_list":
            denied_tools = config.get("denied_tools", [])
            return DenyList(denied_tools)
        
        case "pattern":
            patterns = config.get("patterns", [])
            deny = config.get("deny", False)
            return Pattern(patterns, deny=deny)
        
        case "interactive":
            auto_approve_safe = config.get("auto_approve_safe", True)
            return Interactive(auto_approve_safe=auto_approve_safe)
        
        case "conditional":
            conditions = config.get("conditions", {})
            return ConditionalStrategy(conditions)
        
        case "composite":
            strategies_config = config.get("strategies", [])
            require_all = config.get("require_all", False)
            
            # Recursively create sub-strategies
            strategies = []
            for strategy_config in strategies_config:
                strategy_type_inner = strategy_config.get("type")
                strategy_config_inner = strategy_config.get("config", {})
                if strategy_type_inner:
                    strategies.append(create_approval_strategy(strategy_type_inner, strategy_config_inner))
            
            return Composite(strategies, require_all=require_all)
        
        case _:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
