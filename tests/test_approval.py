"""Tests for MCP tool approval strategies."""

import pytest
from unittest.mock import Mock, patch

from claif_cla.approval import (
    AllowAll,
    DenyAll,
    AllowList,
    DenyList,
    Pattern,
    Composite,
    Interactive,
    ConditionalStrategy,
    create_approval_strategy,
    STRATEGY_PRESETS,
)


@pytest.mark.unit
class TestAllowAll:
    """Test AllowAll strategy."""
    
    def test_allows_everything(self):
        """Test that AllowAll approves all tools."""
        strategy = AllowAll()
        
        assert strategy.should_approve("any_tool", {})
        assert strategy.should_approve("dangerous_tool", {"param": "value"})
        assert strategy.should_approve("", {})
    
    def test_description(self):
        """Test description."""
        strategy = AllowAll()
        assert strategy.get_description() == "Allow all tools"


@pytest.mark.unit
class TestDenyAll:
    """Test DenyAll strategy."""
    
    def test_denies_everything(self):
        """Test that DenyAll denies all tools."""
        strategy = DenyAll()
        
        assert not strategy.should_approve("any_tool", {})
        assert not strategy.should_approve("safe_tool", {"param": "value"})
        assert not strategy.should_approve("", {})
    
    def test_description(self):
        """Test description."""
        strategy = DenyAll()
        assert strategy.get_description() == "Deny all tools"


@pytest.mark.unit
class TestAllowList:
    """Test AllowList strategy."""
    
    def test_allows_listed_tools(self):
        """Test that AllowList only approves listed tools."""
        strategy = AllowList(["read_file", "list_files", "search"])
        
        assert strategy.should_approve("read_file", {})
        assert strategy.should_approve("list_files", {"path": "/tmp"})
        assert strategy.should_approve("search", {"query": "test"})
        assert not strategy.should_approve("write_file", {})
        assert not strategy.should_approve("delete_file", {})
    
    def test_empty_list(self):
        """Test empty allow list denies everything."""
        strategy = AllowList([])
        
        assert not strategy.should_approve("any_tool", {})
    
    def test_description(self):
        """Test description shows allowed tools."""
        strategy = AllowList(["tool_b", "tool_a", "tool_c"])
        assert strategy.get_description() == "Allow only: tool_a, tool_b, tool_c"


@pytest.mark.unit
class TestDenyList:
    """Test DenyList strategy."""
    
    def test_denies_listed_tools(self):
        """Test that DenyList only denies listed tools."""
        strategy = DenyList(["delete_file", "execute_command"])
        
        assert not strategy.should_approve("delete_file", {})
        assert not strategy.should_approve("execute_command", {"cmd": "rm -rf /"})
        assert strategy.should_approve("read_file", {})
        assert strategy.should_approve("list_files", {})
    
    def test_empty_list(self):
        """Test empty deny list allows everything."""
        strategy = DenyList([])
        
        assert strategy.should_approve("any_tool", {})
    
    def test_description(self):
        """Test description shows denied tools."""
        strategy = DenyList(["tool_b", "tool_a"])
        assert strategy.get_description() == "Deny only: tool_a, tool_b"


@pytest.mark.unit
class TestPattern:
    """Test Pattern strategy."""
    
    def test_pattern_matching_allow(self):
        """Test pattern matching for allowing tools."""
        strategy = Pattern([r"read_.*", r"list_.*"])
        
        assert strategy.should_approve("read_file", {})
        assert strategy.should_approve("read_directory", {})
        assert strategy.should_approve("list_files", {})
        assert not strategy.should_approve("write_file", {})
        assert not strategy.should_approve("execute", {})
    
    def test_pattern_matching_deny(self):
        """Test pattern matching for denying tools."""
        strategy = Pattern([r".*_prod.*", r"delete_.*"], deny=True)
        
        assert not strategy.should_approve("read_prod_db", {})
        assert not strategy.should_approve("delete_file", {})
        assert not strategy.should_approve("delete_all", {})
        assert strategy.should_approve("read_file", {})
        assert strategy.should_approve("write_file", {})
    
    def test_complex_patterns(self):
        """Test complex regex patterns."""
        strategy = Pattern([r"^(read|write)_[a-z]+$"])
        
        assert strategy.should_approve("read_file", {})
        assert strategy.should_approve("write_data", {})
        assert not strategy.should_approve("read_", {})
        assert not strategy.should_approve("read_file2", {})  # Contains digit
        assert not strategy.should_approve("READ_FILE", {})  # Uppercase
    
    def test_description(self):
        """Test description shows patterns."""
        strategy = Pattern([r"test_.*", r".*_test"], deny=True)
        desc = strategy.get_description()
        assert "Deny patterns:" in desc
        assert "test_.*" in desc
        assert ".*_test" in desc


@pytest.mark.unit
class TestComposite:
    """Test Composite strategy."""
    
    def test_composite_or_logic(self):
        """Test composite with OR logic (any strategy approves)."""
        allow_list = AllowList(["safe_tool"])
        pattern = Pattern([r"read_.*"])
        
        strategy = Composite([allow_list, pattern], require_all=False)
        
        assert strategy.should_approve("safe_tool", {})  # Allowed by list
        assert strategy.should_approve("read_file", {})  # Allowed by pattern
        assert not strategy.should_approve("write_file", {})  # Denied by both
    
    def test_composite_and_logic(self):
        """Test composite with AND logic (all strategies must approve)."""
        deny_list = DenyList(["dangerous_tool"])
        pattern = Pattern([r".*_prod.*"], deny=True)
        
        strategy = Composite([deny_list, pattern], require_all=True)
        
        assert strategy.should_approve("safe_tool", {})  # Approved by both
        assert not strategy.should_approve("dangerous_tool", {})  # Denied by list
        assert not strategy.should_approve("read_prod_db", {})  # Denied by pattern
        assert not strategy.should_approve("dangerous_prod_tool", {})  # Denied by both
    
    def test_empty_composite(self):
        """Test empty composite strategies."""
        # OR with no strategies denies (no strategy approves)
        strategy_or = Composite([], require_all=False)
        assert not strategy_or.should_approve("any_tool", {})
        
        # AND with no strategies approves (all zero strategies approve)
        strategy_and = Composite([], require_all=True)
        assert strategy_and.should_approve("any_tool", {})
    
    def test_description(self):
        """Test composite description."""
        allow = AllowAll()
        deny = DenyAll()
        
        strategy_or = Composite([allow, deny], require_all=False)
        assert "(Allow all toolsORDeny all tools)" in strategy_or.get_description()
        
        strategy_and = Composite([allow, deny], require_all=True)
        assert "(Allow all toolsANDDeny all tools)" in strategy_and.get_description()


@pytest.mark.unit
class TestInteractive:
    """Test Interactive strategy."""
    
    def test_auto_approve_safe_tools(self):
        """Test auto-approval of safe tools."""
        strategy = Interactive(auto_approve_safe=True)
        
        # Safe tools should be auto-approved
        assert strategy.should_approve("ls", {})
        assert strategy.should_approve("cat", {})
        assert strategy.should_approve("search_code", {})
        assert strategy.should_approve("view_file", {})
        
        # Unsafe tools should be denied (no interactive prompt in tests)
        assert not strategy.should_approve("rm", {})
        assert not strategy.should_approve("execute_command", {})
    
    def test_no_auto_approve(self):
        """Test without auto-approval."""
        strategy = Interactive(auto_approve_safe=False)
        
        # All tools denied without interactive prompt
        assert not strategy.should_approve("ls", {})
        assert not strategy.should_approve("rm", {})
    
    def test_description(self):
        """Test description."""
        strategy1 = Interactive(auto_approve_safe=True)
        assert strategy1.get_description() == "Interactive approval (auto-approve safe)"
        
        strategy2 = Interactive(auto_approve_safe=False)
        assert strategy2.get_description() == "Interactive approval"


@pytest.mark.unit
class TestConditionalStrategy:
    """Test ConditionalStrategy."""
    
    def test_no_conditions_allows_all(self):
        """Test that tools without conditions are allowed."""
        strategy = ConditionalStrategy({})
        
        assert strategy.should_approve("any_tool", {})
        assert strategy.should_approve("another_tool", {"param": "value"})
    
    def test_max_condition(self):
        """Test max value condition."""
        conditions = {
            "read_file": {
                "size": {"max": 1000}
            }
        }
        strategy = ConditionalStrategy(conditions)
        
        assert strategy.should_approve("read_file", {"size": 500})
        assert strategy.should_approve("read_file", {"size": 1000})
        assert not strategy.should_approve("read_file", {"size": 1001})
        assert strategy.should_approve("read_file", {})  # No size param
    
    def test_min_condition(self):
        """Test min value condition."""
        conditions = {
            "wait": {
                "seconds": {"min": 1}
            }
        }
        strategy = ConditionalStrategy(conditions)
        
        assert strategy.should_approve("wait", {"seconds": 5})
        assert strategy.should_approve("wait", {"seconds": 1})
        assert not strategy.should_approve("wait", {"seconds": 0})
    
    def test_allowed_values_dict(self):
        """Test allowed values in dict format."""
        conditions = {
            "set_mode": {
                "mode": {"allowed": ["safe", "normal"]}
            }
        }
        strategy = ConditionalStrategy(conditions)
        
        assert strategy.should_approve("set_mode", {"mode": "safe"})
        assert strategy.should_approve("set_mode", {"mode": "normal"})
        assert not strategy.should_approve("set_mode", {"mode": "dangerous"})
    
    def test_allowed_values_list(self):
        """Test allowed values in list format."""
        conditions = {
            "set_env": {
                "env": ["dev", "staging"]
            }
        }
        strategy = ConditionalStrategy(conditions)
        
        assert strategy.should_approve("set_env", {"env": "dev"})
        assert strategy.should_approve("set_env", {"env": "staging"})
        assert not strategy.should_approve("set_env", {"env": "prod"})
    
    def test_multiple_conditions(self):
        """Test multiple conditions on same tool."""
        conditions = {
            "process_data": {
                "size": {"max": 1000, "min": 10},
                "format": ["json", "csv"]
            }
        }
        strategy = ConditionalStrategy(conditions)
        
        # All conditions must pass
        assert strategy.should_approve("process_data", {"size": 100, "format": "json"})
        assert not strategy.should_approve("process_data", {"size": 5, "format": "json"})  # Too small
        assert not strategy.should_approve("process_data", {"size": 100, "format": "xml"})  # Wrong format
    
    def test_description(self):
        """Test description."""
        conditions = {"tool1": {}, "tool2": {}}
        strategy = ConditionalStrategy(conditions)
        assert strategy.get_description() == "Conditional approval for ['tool1', 'tool2']"


@pytest.mark.unit
class TestCreateApprovalStrategy:
    """Test factory function."""
    
    def test_create_basic_strategies(self):
        """Test creating basic strategies."""
        allow_all = create_approval_strategy("allow_all")
        assert isinstance(allow_all, AllowAll)
        
        deny_all = create_approval_strategy("deny_all")
        assert isinstance(deny_all, DenyAll)
    
    def test_create_list_strategies(self):
        """Test creating list strategies."""
        allow_list = create_approval_strategy("allow_list", {
            "allowed_tools": ["read", "write"]
        })
        assert isinstance(allow_list, AllowList)
        assert allow_list.should_approve("read", {})
        
        deny_list = create_approval_strategy("deny_list", {
            "denied_tools": ["delete", "execute"]
        })
        assert isinstance(deny_list, DenyList)
        assert not deny_list.should_approve("delete", {})
    
    def test_create_pattern_strategy(self):
        """Test creating pattern strategy."""
        pattern = create_approval_strategy("pattern", {
            "patterns": [r"test_.*"],
            "deny": True
        })
        assert isinstance(pattern, Pattern)
        assert not pattern.should_approve("test_tool", {})
    
    def test_create_composite_strategy(self):
        """Test creating composite strategy."""
        composite = create_approval_strategy("composite", {
            "strategies": [
                {"type": "allow_all"},
                {"type": "deny_all"}
            ],
            "require_all": False
        })
        assert isinstance(composite, Composite)
        assert len(composite.strategies) == 2
    
    def test_create_interactive_strategy(self):
        """Test creating interactive strategy."""
        interactive = create_approval_strategy("interactive", {
            "auto_approve_safe": False
        })
        assert isinstance(interactive, Interactive)
        assert not interactive.auto_approve_safe
    
    def test_create_conditional_strategy(self):
        """Test creating conditional strategy."""
        conditional = create_approval_strategy("conditional", {
            "conditions": {
                "tool": {"param": {"max": 10}}
            }
        })
        assert isinstance(conditional, ConditionalStrategy)
        assert "tool" in conditional.conditions
    
    def test_create_unknown_strategy(self):
        """Test creating unknown strategy raises error."""
        with pytest.raises(ValueError, match="Unknown strategy type: unknown"):
            create_approval_strategy("unknown")
    
    def test_create_with_defaults(self):
        """Test creating strategies with default configs."""
        # Should use empty config if not provided
        allow_list = create_approval_strategy("allow_list")
        assert isinstance(allow_list, AllowList)
        assert len(allow_list.allowed_tools) == 0


@pytest.mark.unit
class TestStrategyPresets:
    """Test predefined strategy configurations."""
    
    def test_development_preset(self):
        """Test development preset configuration."""
        config = STRATEGY_PRESETS["development"]
        strategy = create_approval_strategy(config["type"], config["config"])
        
        assert isinstance(strategy, Composite)
        assert strategy.require_all
        
        # Should deny dangerous tools and production patterns
        assert not strategy.should_approve("delete_file", {})
        assert not strategy.should_approve("read_prod_db", {})
        assert strategy.should_approve("read_file", {})
    
    def test_production_preset(self):
        """Test production preset configuration."""
        config = STRATEGY_PRESETS["production"]
        strategy = create_approval_strategy(config["type"], config["config"])
        
        assert isinstance(strategy, Composite)
        
        # Should only allow safe read operations
        assert strategy.should_approve("read_file", {"path": {"allowed": ["/app/data"]}})
        assert not strategy.should_approve("write_file", {})
        assert not strategy.should_approve("execute_command", {})
    
    def test_testing_preset(self):
        """Test testing preset configuration."""
        config = STRATEGY_PRESETS["testing"]
        strategy = create_approval_strategy(config["type"], config["config"])
        
        assert isinstance(strategy, AllowAll)
        assert strategy.should_approve("any_tool", {})
    
    def test_all_presets_valid(self):
        """Test that all presets can be created successfully."""
        for name, config in STRATEGY_PRESETS.items():
            strategy = create_approval_strategy(config["type"], config["config"])
            assert strategy is not None
            assert hasattr(strategy, "should_approve")