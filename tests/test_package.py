"""Test suite for claif_cla package structure."""

import pytest
import claif_cla


@pytest.mark.unit
def test_version():
    """Verify package exposes version."""
    assert hasattr(claif_cla, "__version__")
    assert claif_cla.__version__
    # Version should be a string
    assert isinstance(claif_cla.__version__, str)


@pytest.mark.unit
def test_package_exports():
    """Test that package exports expected symbols."""
    # Core function
    assert hasattr(claif_cla, "query")
    assert callable(claif_cla.query)
    
    # Re-exported from claude-code-sdk
    assert hasattr(claif_cla, "ClaudeCodeOptions")
    assert hasattr(claif_cla, "Message")
    
    # Version
    assert hasattr(claif_cla, "__version__")
    
    # __all__ should be defined
    assert hasattr(claif_cla, "__all__")
    assert isinstance(claif_cla.__all__, list)
    assert len(claif_cla.__all__) > 0


@pytest.mark.unit
def test_submodules():
    """Test that submodules can be imported."""
    # These imports should not raise
    from claif_cla import session
    from claif_cla import approval
    from claif_cla import cli
    from claif_cla import install
    from claif_cla import wrapper
    
    # Verify they're modules
    import types
    assert isinstance(session, types.ModuleType)
    assert isinstance(approval, types.ModuleType)
    assert isinstance(cli, types.ModuleType)
    assert isinstance(install, types.ModuleType)
    assert isinstance(wrapper, types.ModuleType)


@pytest.mark.unit
def test_cli_entry_point():
    """Test that CLI entry point exists."""
    from claif_cla.cli import main
    assert callable(main)
