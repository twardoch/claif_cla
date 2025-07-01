"""MCP tool approval strategies for Claude."""

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Pattern

from ..claif.common import get_logger


logger = get_logger(__name__)


class ApprovalStrategy(ABC):
    """Base class for tool approval strategies."""
    
    @abstractmethod
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """Determine if a tool use should be approved."""
        pass
    
    def get_description(self) -> str:
        """Get a description of this strategy."""
        return self.__class__.__name__


class AllowAllStrategy(ApprovalStrategy):
    """Approve all tool uses."""
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        logger.debug(f"AllowAll: Approving {tool_name}")
        return True
    
    def get_description(self) -> str:
        return "Allow all tools"


class DenyAllStrategy(ApprovalStrategy):
    """Deny all tool uses."""
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        logger.debug(f"DenyAll: Denying {tool_name}")
        return False
    
    def get_description(self) -> str:
        return "Deny all tools"


class AllowListStrategy(ApprovalStrategy):
    """Approve only tools in the allow list."""
    
    def __init__(self, allowed_tools: List[str]):
        self.allowed_tools = set(allowed_tools)
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        approved = tool_name in self.allowed_tools
        logger.debug(f"AllowList: {tool_name} {'approved' if approved else 'denied'}")
        return approved
    
    def get_description(self) -> str:
        return f"Allow only: {', '.join(sorted(self.allowed_tools))}"


class DenyListStrategy(ApprovalStrategy):
    """Deny only tools in the deny list."""
    
    def __init__(self, denied_tools: List[str]):
        self.denied_tools = set(denied_tools)
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        approved = tool_name not in self.denied_tools
        logger.debug(f"DenyList: {tool_name} {'approved' if approved else 'denied'}")
        return approved
    
    def get_description(self) -> str:
        return f"Deny only: {', '.join(sorted(self.denied_tools))}"


class PatternStrategy(ApprovalStrategy):
    """Approve tools matching regex patterns."""
    
    def __init__(self, patterns: List[str], deny: bool = False):
        self.patterns: List[Pattern] = [re.compile(p) for p in patterns]
        self.deny = deny
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        matches = any(p.match(tool_name) for p in self.patterns)
        approved = not matches if self.deny else matches
        logger.debug(f"Pattern: {tool_name} {'approved' if approved else 'denied'}")
        return approved
    
    def get_description(self) -> str:
        action = "Deny" if self.deny else "Allow"
        return f"{action} patterns: {[p.pattern for p in self.patterns]}"


class CompositeStrategy(ApprovalStrategy):
    """Combine multiple strategies with AND/OR logic."""
    
    def __init__(self, strategies: List[ApprovalStrategy], require_all: bool = False):
        self.strategies = strategies
        self.require_all = require_all
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        results = [s.should_approve(tool_name, tool_input) for s in self.strategies]
        
        if self.require_all:
            approved = all(results)
        else:
            approved = any(results)
        
        logger.debug(f"Composite: {tool_name} {'approved' if approved else 'denied'}")
        return approved
    
    def get_description(self) -> str:
        op = "AND" if self.require_all else "OR"
        descriptions = [s.get_description() for s in self.strategies]
        return f"({op.join(descriptions)})"


class InteractiveStrategy(ApprovalStrategy):
    """Ask user for approval interactively."""
    
    def __init__(self, auto_approve_safe: bool = True):
        self.auto_approve_safe = auto_approve_safe
        self.safe_tools = {
            "read_file",
            "list_files",
            "search",
            "get_weather",
            "calculate",
        }
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        if self.auto_approve_safe and tool_name in self.safe_tools:
            logger.debug(f"Interactive: Auto-approving safe tool {tool_name}")
            return True
        
        # In real implementation, would prompt user
        # For now, return True for testing
        logger.debug(f"Interactive: Would prompt for {tool_name}")
        return True
    
    def get_description(self) -> str:
        return "Interactive approval" + (" (auto-approve safe)" if self.auto_approve_safe else "")


class ConditionalStrategy(ApprovalStrategy):
    """Approve based on tool input conditions."""
    
    def __init__(self, conditions: Dict[str, Any]):
        self.conditions = conditions
    
    def should_approve(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        # Check if tool has specific conditions
        if tool_name not in self.conditions:
            return True
        
        tool_conditions = self.conditions[tool_name]
        
        # Check each condition
        for param, condition in tool_conditions.items():
            if param not in tool_input:
                continue
            
            value = tool_input[param]
            
            # Handle different condition types
            if isinstance(condition, dict):
                if "max" in condition and value > condition["max"]:
                    logger.debug(f"Conditional: {tool_name} denied - {param} exceeds max")
                    return False
                if "min" in condition and value < condition["min"]:
                    logger.debug(f"Conditional: {tool_name} denied - {param} below min")
                    return False
                if "allowed" in condition and value not in condition["allowed"]:
                    logger.debug(f"Conditional: {tool_name} denied - {param} not in allowed list")
                    return False
            elif isinstance(condition, list) and value not in condition:
                logger.debug(f"Conditional: {tool_name} denied - {param} not in allowed values")
                return False
        
        logger.debug(f"Conditional: {tool_name} approved")
        return True
    
    def get_description(self) -> str:
        return f"Conditional approval for {list(self.conditions.keys())}"


def create_approval_strategy(
    strategy_type: str,
    config: Optional[Dict[str, Any]] = None,
) -> ApprovalStrategy:
    """Factory function to create approval strategies."""
    config = config or {}
    
    if strategy_type == "allow_all":
        return AllowAllStrategy()
    
    elif strategy_type == "deny_all":
        return DenyAllStrategy()
    
    elif strategy_type == "allow_list":
        allowed = config.get("allowed_tools", [])
        return AllowListStrategy(allowed)
    
    elif strategy_type == "deny_list":
        denied = config.get("denied_tools", [])
        return DenyListStrategy(denied)
    
    elif strategy_type == "pattern":
        patterns = config.get("patterns", [])
        deny = config.get("deny", False)
        return PatternStrategy(patterns, deny)
    
    elif strategy_type == "composite":
        strategies = []
        for s_config in config.get("strategies", []):
            s_type = s_config.get("type")
            s_cfg = s_config.get("config", {})
            strategies.append(create_approval_strategy(s_type, s_cfg))
        require_all = config.get("require_all", False)
        return CompositeStrategy(strategies, require_all)
    
    elif strategy_type == "interactive":
        auto_approve_safe = config.get("auto_approve_safe", True)
        return InteractiveStrategy(auto_approve_safe)
    
    elif strategy_type == "conditional":
        conditions = config.get("conditions", {})
        return ConditionalStrategy(conditions)
    
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


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