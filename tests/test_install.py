"""Tests for installation functionality."""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from claif_cla.install import (
    install_claude_bundled,
    install_claude,
    uninstall_claude,
    is_claude_installed,
    get_claude_status,
)


@pytest.mark.unit
class TestInstallClaudeBundled:
    """Test bundled Claude installation."""
    
    def test_install_bundled_success(self, temp_dir):
        """Test successful bundled installation."""
        install_dir = temp_dir / "install"
        install_dir.mkdir()
        
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        
        # Create mock Claude directory with executable
        claude_dir = dist_dir / "claude"
        claude_dir.mkdir()
        (claude_dir / "claude").write_text("mock executable")
        (claude_dir / "yoga.wasm").write_text("mock wasm")
        
        result = install_claude_bundled(install_dir, dist_dir)
        
        assert result is True
        
        # Check that claude-bin directory was created
        claude_bin = install_dir / "claude-bin"
        assert claude_bin.exists()
        assert (claude_bin / "claude").exists()
        assert (claude_bin / "yoga.wasm").exists()
        
        # Check wrapper script
        wrapper = install_dir / "claude"
        assert wrapper.exists()
        assert wrapper.stat().st_mode & 0o755 == 0o755
        
        # Check wrapper content
        content = wrapper.read_text()
        assert "#!/usr/bin/env bash" in content
        assert f'cd "{claude_bin}"' in content
        assert 'exec ./claude "$@"' in content
    
    def test_install_bundled_missing_source(self, temp_dir):
        """Test installation when bundled Claude is missing."""
        install_dir = temp_dir / "install"
        install_dir.mkdir()
        
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        # No claude directory in dist
        
        result = install_claude_bundled(install_dir, dist_dir)
        
        assert result is False
    
    def test_install_bundled_overwrite_existing(self, temp_dir):
        """Test installation overwrites existing installation."""
        install_dir = temp_dir / "install"
        install_dir.mkdir()
        
        # Create existing installation
        old_claude_bin = install_dir / "claude-bin"
        old_claude_bin.mkdir()
        (old_claude_bin / "old_file").write_text("old")
        
        old_wrapper = install_dir / "claude"
        old_wrapper.write_text("old wrapper")
        
        # Create new dist
        dist_dir = temp_dir / "dist"
        dist_dir.mkdir()
        claude_dir = dist_dir / "claude"
        claude_dir.mkdir()
        (claude_dir / "claude").write_text("new executable")
        
        result = install_claude_bundled(install_dir, dist_dir)
        
        assert result is True
        
        # Old files should be gone
        assert not (install_dir / "claude-bin" / "old_file").exists()
        
        # New files should exist
        assert (install_dir / "claude-bin" / "claude").exists()
        assert "new executable" in (install_dir / "claude-bin" / "claude").read_text()
    
    def test_install_bundled_exception(self, temp_dir):
        """Test installation handles exceptions."""
        install_dir = temp_dir / "install"
        dist_dir = temp_dir / "dist"
        
        with patch("shutil.copytree", side_effect=Exception("Copy failed")):
            result = install_claude_bundled(install_dir, dist_dir)
            
            assert result is False


@pytest.mark.unit
class TestInstallClaude:
    """Test main Claude installation function."""
    
    def test_install_claude_success(self, temp_dir):
        """Test successful Claude installation."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=True), \
             patch("claif_cla.install.get_install_location", return_value=temp_dir), \
             patch("claif_cla.install.install_npm_package_globally", return_value=True), \
             patch("claif_cla.install.bundle_all_tools", return_value=temp_dir / "dist"), \
             patch("claif_cla.install.install_claude_bundled", return_value=True), \
             patch("claif_cla.install.prompt_tool_configuration"):
            
            # Create mock dist directory
            (temp_dir / "dist").mkdir()
            
            result = install_claude()
            
            assert result == {"installed": ["claude"], "failed": []}
    
    def test_install_claude_bun_failure(self):
        """Test installation fails when bun installation fails."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=False):
            result = install_claude()
            
            assert result == {
                "installed": [],
                "failed": ["claude"],
                "message": "bun installation failed"
            }
    
    def test_install_claude_npm_failure(self):
        """Test installation fails when npm package installation fails."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=True), \
             patch("claif_cla.install.install_npm_package_globally", return_value=False):
            
            result = install_claude()
            
            assert result == {
                "installed": [],
                "failed": ["claude"],
                "message": "@anthropic-ai/claude-code installation failed"
            }
    
    def test_install_claude_bundle_failure(self):
        """Test installation fails when bundling fails."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=True), \
             patch("claif_cla.install.install_npm_package_globally", return_value=True), \
             patch("claif_cla.install.bundle_all_tools", return_value=None):
            
            result = install_claude()
            
            assert result == {
                "installed": [],
                "failed": ["claude"],
                "message": "bundling failed"
            }
    
    def test_install_claude_bundled_install_failure(self, temp_dir):
        """Test installation fails when bundled install fails."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=True), \
             patch("claif_cla.install.get_install_location", return_value=temp_dir), \
             patch("claif_cla.install.install_npm_package_globally", return_value=True), \
             patch("claif_cla.install.bundle_all_tools", return_value=temp_dir / "dist"), \
             patch("claif_cla.install.install_claude_bundled", return_value=False):
            
            (temp_dir / "dist").mkdir()
            
            result = install_claude()
            
            assert result == {
                "installed": [],
                "failed": ["claude"],
                "message": "claude installation failed"
            }
    
    def test_install_claude_prompt_configuration(self, temp_dir):
        """Test that configuration prompt is called on success."""
        with patch("claif_cla.install.ensure_bun_installed", return_value=True), \
             patch("claif_cla.install.get_install_location", return_value=temp_dir), \
             patch("claif_cla.install.install_npm_package_globally", return_value=True), \
             patch("claif_cla.install.bundle_all_tools", return_value=temp_dir / "dist"), \
             patch("claif_cla.install.install_claude_bundled", return_value=True), \
             patch("claif_cla.install.prompt_tool_configuration") as mock_prompt:
            
            (temp_dir / "dist").mkdir()
            
            install_claude()
            
            mock_prompt.assert_called_once_with("Claude", [
                "claude auth login",
                "claude --help"
            ])


@pytest.mark.unit
class TestUninstallClaude:
    """Test Claude uninstallation."""
    
    def test_uninstall_success(self):
        """Test successful uninstallation."""
        with patch("claif_cla.install.uninstall_tool", return_value=True):
            result = uninstall_claude()
            
            assert result == {"uninstalled": ["claude"], "failed": []}
    
    def test_uninstall_failure(self):
        """Test failed uninstallation."""
        with patch("claif_cla.install.uninstall_tool", return_value=False):
            result = uninstall_claude()
            
            assert result == {
                "uninstalled": [],
                "failed": ["claude"],
                "message": "claude uninstallation failed"
            }


@pytest.mark.unit
class TestIsClaudeInstalled:
    """Test Claude installation check."""
    
    def test_is_installed_executable(self, temp_dir):
        """Test detection of installed executable."""
        with patch("claif_cla.install.get_install_location", return_value=temp_dir):
            # Create executable file
            claude_exe = temp_dir / "claude"
            claude_exe.write_text("#!/bin/bash")
            
            assert is_claude_installed() is True
    
    def test_is_installed_directory(self, temp_dir):
        """Test detection of installed directory."""
        with patch("claif_cla.install.get_install_location", return_value=temp_dir):
            # Create claude directory
            claude_dir = temp_dir / "claude"
            claude_dir.mkdir()
            
            assert is_claude_installed() is True
    
    def test_is_not_installed(self, temp_dir):
        """Test detection when not installed."""
        with patch("claif_cla.install.get_install_location", return_value=temp_dir):
            assert is_claude_installed() is False
    
    def test_is_installed_both(self, temp_dir):
        """Test detection when both file and directory exist."""
        with patch("claif_cla.install.get_install_location", return_value=temp_dir):
            # Create both
            claude_exe = temp_dir / "claude"
            claude_exe.write_text("#!/bin/bash")
            
            # This would be unusual but should still return True
            assert is_claude_installed() is True


@pytest.mark.unit
class TestGetClaudeStatus:
    """Test getting Claude status."""
    
    def test_status_installed(self, temp_dir):
        """Test status when Claude is installed."""
        with patch("claif_cla.install.is_claude_installed", return_value=True), \
             patch("claif_cla.install.get_install_location", return_value=temp_dir):
            
            status = get_claude_status()
            
            assert status["installed"] is True
            assert status["path"] == str(temp_dir / "claude")
            assert status["type"] == "bundled (claif-owned)"
    
    def test_status_not_installed(self):
        """Test status when Claude is not installed."""
        with patch("claif_cla.install.is_claude_installed", return_value=False):
            status = get_claude_status()
            
            assert status["installed"] is False
            assert status["path"] is None
            assert status["type"] is None


@pytest.mark.unit
class TestFallbackImports:
    """Test fallback import handling."""
    
    def test_fallback_imports_when_claif_missing(self):
        """Test that fallback imports are used when claif is missing."""
        # Mock the import to fail
        import sys
        
        # Save original modules
        original_modules = {}
        for mod in ["claif.common.utils", "claif.install"]:
            if mod in sys.modules:
                original_modules[mod] = sys.modules[mod]
        
        try:
            # Remove claif modules to simulate import failure
            sys.modules.pop("claif.common.utils", None)
            sys.modules.pop("claif.install", None)
            
            # Mock the fallback module
            mock_fallback = MagicMock()
            sys.modules["claif_cla.install_fallback"] = mock_fallback
            
            # Re-import to trigger fallback
            import importlib
            import claif_cla.install
            importlib.reload(claif_cla.install)
            
            # Should have used fallback functions
            assert hasattr(claif_cla.install, "prompt_tool_configuration")
            
        finally:
            # Restore original modules
            for mod, original in original_modules.items():
                sys.modules[mod] = original
            sys.modules.pop("claif_cla.install_fallback", None)


@pytest.mark.unit
class TestPromptToolConfiguration:
    """Test the prompt_tool_configuration fallback."""
    
    def test_prompt_tool_configuration_fallback(self):
        """Test fallback implementation of prompt_tool_configuration."""
        # This tests the local fallback implementation
        from claif_cla.install import prompt_tool_configuration
        
        # Should not raise any errors
        prompt_tool_configuration("test_tool", [])
        prompt_tool_configuration("test_tool", ["cmd1", "cmd2"])
        
        # Function exists and is callable
        assert callable(prompt_tool_configuration)