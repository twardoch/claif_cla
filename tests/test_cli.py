"""Tests for CLI functionality."""

import asyncio
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, call, MagicMock

import pytest

from claif.common import ClaifOptions, Message, MessageRole, ResponseMetrics
from claif_cla.cli import ClaudeCLI, main


@pytest.fixture
def mock_print():
    """Mock print functions."""
    with patch("claif_cla.cli._print") as mock:
        yield mock


@pytest.fixture
def mock_print_error():
    """Mock error print function."""
    with patch("claif_cla.cli._print_error") as mock:
        yield mock


@pytest.fixture
def mock_print_success():
    """Mock success print function."""
    with patch("claif_cla.cli._print_success") as mock:
        yield mock


@pytest.fixture
def mock_print_warning():
    """Mock warning print function."""
    with patch("claif_cla.cli._print_warning") as mock:
        yield mock


@pytest.fixture
def mock_confirm():
    """Mock confirmation prompt."""
    with patch("claif_cla.cli._confirm", return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_prompt():
    """Mock input prompt."""
    with patch("claif_cla.cli._prompt", return_value="test input") as mock:
        yield mock


@pytest.fixture
def mock_query():
    """Mock the query function."""
    async def _mock_query(prompt, options):
        yield Message(role=MessageRole.USER, content=prompt)
        yield Message(role=MessageRole.ASSISTANT, content="Mock response")
    
    with patch("claif_cla.cli.query", side_effect=_mock_query) as mock:
        yield mock


@pytest.fixture
def cli_instance(temp_dir):
    """Create CLI instance with temp config."""
    with patch("claif_cla.cli.load_config") as mock_config:
        mock_config.return_value = Mock(verbose=False, session_dir=str(temp_dir / "sessions"))
        cli = ClaudeCLI()
        return cli


@pytest.mark.unit
class TestClaudeCLI:
    """Test ClaudeCLI class."""
    
    def test_init_default(self, temp_dir):
        """Test CLI initialization with defaults."""
        with patch("claif_cla.cli.load_config") as mock_config:
            mock_config.return_value = Mock(verbose=False, session_dir=str(temp_dir))
            
            cli = ClaudeCLI()
            
            mock_config.assert_called_once_with(None)
            assert cli.config.verbose is False
            assert cli.session_manager is not None
    
    def test_init_with_config_file(self, temp_dir):
        """Test CLI initialization with config file."""
        config_file = temp_dir / "config.yaml"
        
        with patch("claif_cla.cli.load_config") as mock_config:
            mock_config.return_value = Mock(verbose=False, session_dir=str(temp_dir))
            
            cli = ClaudeCLI(config_file=str(config_file))
            
            mock_config.assert_called_once_with(str(config_file))
    
    def test_init_verbose(self, temp_dir):
        """Test CLI initialization with verbose flag."""
        with patch("claif_cla.cli.load_config") as mock_config:
            mock_config.return_value = Mock(verbose=False, session_dir=str(temp_dir))
            
            cli = ClaudeCLI(verbose=True)
            
            assert cli.config.verbose is True


@pytest.mark.unit
class TestAskCommand:
    """Test ask command."""
    
    def test_ask_basic(self, cli_instance, mock_query, mock_print):
        """Test basic ask command."""
        cli_instance.ask("Hello, Claude!")
        
        # Verify query was called
        mock_query.assert_called_once()
        call_args = mock_query.call_args[0]
        assert call_args[0] == "Hello, Claude!"
        
        # Verify output
        assert mock_print.call_count >= 1
        mock_print.assert_any_call("Mock response")
    
    def test_ask_with_options(self, cli_instance, mock_query, mock_print):
        """Test ask with various options."""
        cli_instance.ask(
            "Test prompt",
            model="claude-3-opus",
            temperature=0.5,
            max_tokens=500,
            system="You are helpful",
            timeout=60,
            output_format="json",
            show_metrics=False,
            session="test-session",
            cache=False
        )
        
        # Verify options were passed
        call_args = mock_query.call_args[0]
        options = call_args[1]
        assert options.model == "claude-3-opus"
        assert options.temperature == 0.5
        assert options.max_tokens == 500
        assert options.system_prompt == "You are helpful"
        assert options.timeout == 60
        assert options.output_format == "json"
        assert options.session_id == "test-session"
        assert options.cache is False
    
    def test_ask_with_metrics(self, cli_instance, mock_query, mock_print):
        """Test ask with metrics display."""
        with patch("claif_cla.cli.format_metrics", return_value="Metrics: 1.23s") as mock_format:
            cli_instance.ask("Test", show_metrics=True)
            
            # Verify metrics were formatted and printed
            mock_format.assert_called_once()
            mock_print.assert_any_call("\nMetrics: 1.23s")
    
    def test_ask_saves_to_session(self, cli_instance, mock_query, mock_print):
        """Test ask saves messages to session."""
        mock_session_manager = Mock()
        cli_instance.session_manager = mock_session_manager
        
        cli_instance.ask("Test", session="test-session")
        
        # Verify messages were saved
        assert mock_session_manager.add_message.call_count == 2
        calls = mock_session_manager.add_message.call_args_list
        assert calls[0][0][0] == "test-session"
        assert calls[0][0][1].role == MessageRole.USER
        assert calls[1][0][0] == "test-session"
        assert calls[1][0][1].role == MessageRole.ASSISTANT
    
    def test_ask_error_handling(self, cli_instance, mock_print_error):
        """Test ask error handling."""
        with patch("claif_cla.cli.query", side_effect=Exception("Test error")):
            with pytest.raises(SystemExit) as exc_info:
                cli_instance.ask("Test")
            
            assert exc_info.value.code == 1
            mock_print_error.assert_called_with("Test error")


@pytest.mark.unit
class TestStreamCommand:
    """Test stream command."""
    
    def test_stream_basic(self, cli_instance, mock_query):
        """Test basic stream command."""
        cli_instance.stream("Stream this!")
        
        mock_query.assert_called_once()
        call_args = mock_query.call_args[0]
        assert call_args[0] == "Stream this!"
    
    def test_stream_with_options(self, cli_instance, mock_query):
        """Test stream with options."""
        cli_instance.stream(
            "Test",
            model="claude-3",
            temperature=0.7,
            max_tokens=1000,
            system="System prompt",
            timeout=30,
            session="stream-session"
        )
        
        call_args = mock_query.call_args[0]
        options = call_args[1]
        assert options.model == "claude-3"
        assert options.temperature == 0.7
        assert options.session_id == "stream-session"
    
    def test_stream_keyboard_interrupt(self, cli_instance, mock_print_warning):
        """Test stream handles keyboard interrupt."""
        with patch("claif_cla.cli.query", side_effect=KeyboardInterrupt()):
            cli_instance.stream("Test")
            
            mock_print_warning.assert_called_with("Stream interrupted")
    
    def test_stream_error_handling(self, cli_instance, mock_print_error):
        """Test stream error handling."""
        with patch("claif_cla.cli.query", side_effect=Exception("Stream error")):
            with pytest.raises(SystemExit) as exc_info:
                cli_instance.stream("Test")
            
            assert exc_info.value.code == 1
            mock_print_error.assert_called_with("Stream error")


@pytest.mark.unit
class TestSessionCommand:
    """Test session management commands."""
    
    def test_session_list_empty(self, cli_instance, mock_print_warning):
        """Test listing sessions when none exist."""
        cli_instance.session_manager.list_sessions = Mock(return_value=[])
        
        cli_instance.session(action="list")
        
        mock_print_warning.assert_called_with("No sessions found")
    
    def test_session_list_with_sessions(self, cli_instance, mock_print):
        """Test listing sessions."""
        cli_instance.session_manager.list_sessions = Mock(return_value=["session1", "session2"])
        cli_instance.session_manager.get_session_info = Mock(side_effect=[
            {"message_count": 5},
            {"message_count": 10}
        ])
        
        cli_instance.session(action="list")
        
        mock_print.assert_any_call("Active Sessions:")
        mock_print.assert_any_call("  • session1: 5 messages")
        mock_print.assert_any_call("  • session2: 10 messages")
    
    def test_session_create(self, cli_instance, mock_print_success):
        """Test creating a session."""
        cli_instance.session_manager.create_session = Mock(return_value="new-session-id")
        
        cli_instance.session(action="create")
        
        mock_print_success.assert_called_with("Created session: new-session-id")
    
    def test_session_create_with_id(self, cli_instance, mock_print_success):
        """Test creating session with specific ID."""
        cli_instance.session_manager.create_session = Mock(return_value="custom-id")
        
        cli_instance.session(action="create", session_id="custom-id")
        
        cli_instance.session_manager.create_session.assert_called_with()
        mock_print_success.assert_called_with("Created session: custom-id")
    
    def test_session_delete_no_id(self, cli_instance, mock_print_error):
        """Test deleting session without ID."""
        cli_instance.session(action="delete")
        
        mock_print_error.assert_called_with("Session ID required")
    
    def test_session_delete_confirmed(self, cli_instance, mock_confirm, mock_print_success):
        """Test deleting session with confirmation."""
        cli_instance.session_manager.delete_session = Mock()
        
        cli_instance.session(action="delete", session_id="test-session")
        
        mock_confirm.assert_called_with("Delete session test-session?")
        cli_instance.session_manager.delete_session.assert_called_with("test-session")
        mock_print_success.assert_called_with("Deleted session: test-session")
    
    def test_session_show(self, cli_instance, mock_print):
        """Test showing session messages."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi!")
        ]
        cli_instance.session_manager.get_messages = Mock(return_value=messages)
        
        with patch("claif_cla.cli.format_response", side_effect=lambda m, f=None: m.content):
            cli_instance.session(action="show", session_id="test-session")
        
        mock_print.assert_any_call("user:")
        mock_print.assert_any_call("Hello")
        mock_print.assert_any_call("assistant:")
        mock_print.assert_any_call("Hi!")
    
    def test_session_export_to_stdout(self, cli_instance, mock_print):
        """Test exporting session to stdout."""
        cli_instance.session_manager.export_session = Mock(return_value="Exported content")
        
        cli_instance.session(action="export", session_id="test-session")
        
        cli_instance.session_manager.export_session.assert_called_with("test-session", "markdown")
        mock_print.assert_called_with("Exported content")
    
    def test_session_export_to_file(self, cli_instance, temp_dir, mock_print_success):
        """Test exporting session to file."""
        output_file = temp_dir / "export.md"
        cli_instance.session_manager.export_session = Mock(return_value="Content")
        
        cli_instance.session(
            action="export",
            session_id="test-session",
            format="json",
            output=str(output_file)
        )
        
        assert output_file.read_text() == "Content"
        mock_print_success.assert_called_with(f"Exported to {output_file}")
    
    def test_session_branch(self, cli_instance, mock_print_success):
        """Test branching a session."""
        cli_instance.session_manager.branch_session = Mock(return_value="new-branch-id")
        
        cli_instance.session(action="branch", session_id="test-session", point=5)
        
        cli_instance.session_manager.branch_session.assert_called_with("test-session", 5)
        mock_print_success.assert_called_with("Branched to new session: new-branch-id")
    
    def test_session_merge(self, cli_instance, mock_print_success):
        """Test merging sessions."""
        cli_instance.session_manager.merge_sessions = Mock()
        
        cli_instance.session(
            action="merge",
            session_id="target",
            other="source",
            strategy="interleave"
        )
        
        cli_instance.session_manager.merge_sessions.assert_called_with("target", "source", "interleave")
        mock_print_success.assert_called_with("Merged source into target")
    
    def test_session_unknown_action(self, cli_instance, mock_print_error, mock_print):
        """Test unknown session action."""
        cli_instance.session(action="unknown")
        
        mock_print_error.assert_called_with("Unknown action: unknown")
        mock_print.assert_called_with("Available actions: list, create, delete, show, export, branch, merge")


@pytest.mark.unit
class TestHealthCommand:
    """Test health check command."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, cli_instance, mock_print, mock_print_success):
        """Test successful health check."""
        with patch.object(cli_instance, "_health_check", return_value=True):
            cli_instance.health()
            
            mock_print.assert_called_with("Checking Claude health...")
            mock_print_success.assert_called_with("Claude service is healthy")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, cli_instance, mock_print, mock_print_error):
        """Test failed health check."""
        with patch.object(cli_instance, "_health_check", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                cli_instance.health()
            
            assert exc_info.value.code == 1
            mock_print_error.assert_called_with("Claude service is not responding")
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, cli_instance, mock_print_error):
        """Test health check with exception."""
        with patch.object(cli_instance, "_health_check", side_effect=Exception("Connection failed")):
            with pytest.raises(SystemExit) as exc_info:
                cli_instance.health()
            
            assert exc_info.value.code == 1
            mock_print_error.assert_called_with("Health check failed: Connection failed")


@pytest.mark.unit
class TestBenchmarkCommand:
    """Test benchmark command."""
    
    def test_benchmark_success(self, cli_instance, mock_query, mock_print):
        """Test successful benchmark."""
        cli_instance.benchmark(prompt="Test", iterations=3)
        
        # Should print header info
        mock_print.assert_any_call("Benchmarking Claude")
        mock_print.assert_any_call("Prompt: Test")
        mock_print.assert_any_call("Iterations: 3")
        
        # Should run 3 iterations
        assert mock_query.call_count == 3
        
        # Should print results
        assert any("Results:" in str(call) for call in mock_print.call_args_list)
        assert any("Average:" in str(call) for call in mock_print.call_args_list)
    
    def test_benchmark_with_failures(self, cli_instance, mock_print_error):
        """Test benchmark with some failed iterations."""
        # Mock query to fail on second iteration
        call_count = 0
        async def failing_query(prompt, options):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Iteration failed")
            yield Message(role=MessageRole.ASSISTANT, content="Response")
        
        with patch("claif_cla.cli.query", side_effect=failing_query):
            cli_instance.benchmark(iterations=3)
            
            mock_print_error.assert_any_call("Iteration 2 failed: Iteration failed")
    
    def test_benchmark_all_fail(self, cli_instance, mock_print_error):
        """Test benchmark when all iterations fail."""
        with patch("claif_cla.cli.query", side_effect=Exception("Always fails")):
            cli_instance.benchmark(iterations=2)
            
            mock_print_error.assert_any_call("No successful iterations")


@pytest.mark.unit
class TestInstallCommands:
    """Test install/uninstall/status commands."""
    
    def test_install_success(self, cli_instance, mock_print, mock_print_success):
        """Test successful installation."""
        with patch("claif_cla.install.install_claude") as mock_install:
            mock_install.return_value = {"installed": True, "failed": []}
            
            cli_instance.install()
            
            mock_print.assert_called_with("Installing Claude provider...")
            mock_print_success.assert_any_call("Claude provider installed successfully!")
    
    def test_install_failure(self, cli_instance, mock_print_error):
        """Test failed installation."""
        with patch("claif_cla.install.install_claude") as mock_install:
            mock_install.return_value = {
                "installed": False,
                "failed": ["claude"],
                "message": "Network error"
            }
            
            with pytest.raises(SystemExit) as exc_info:
                cli_instance.install()
            
            assert exc_info.value.code == 1
            mock_print_error.assert_any_call("Failed to install Claude provider: Network error")
            mock_print_error.assert_any_call("Failed components: claude")
    
    def test_uninstall_success(self, cli_instance, mock_print_success):
        """Test successful uninstallation."""
        with patch("claif_cla.install.uninstall_claude") as mock_uninstall:
            mock_uninstall.return_value = {"uninstalled": True, "failed": []}
            
            cli_instance.uninstall()
            
            mock_print_success.assert_called_with("Claude provider uninstalled successfully!")
    
    def test_status(self, cli_instance, mock_print, mock_print_success, mock_print_warning):
        """Test status command."""
        with patch("claif_cla.install.get_claude_status") as mock_status, \
             patch("claif_cla.install.get_install_location") as mock_location, \
             patch("shutil.which", return_value="/usr/local/bin/claude"), \
             patch.dict("os.environ", {"PATH": "/usr/local/bin:/usr/bin"}):
            
            mock_status.return_value = {
                "installed": True,
                "path": "/usr/local/bin/claude",
                "type": "bundled"
            }
            mock_location.return_value = Path("/usr/local/bin")
            
            cli_instance.status()
            
            mock_print.assert_any_call("Claude Provider Status")
            mock_print_success.assert_any_call("Installed: /usr/local/bin/claude (bundled)")
            mock_print_success.assert_any_call("'claude' command available in PATH")
            mock_print_success.assert_any_call("Install directory in PATH")


@pytest.mark.unit
class TestInteractiveCommand:
    """Test interactive session."""
    
    def test_interactive_basic_flow(self, cli_instance, mock_print, mock_prompt):
        """Test basic interactive flow."""
        # Mock prompt to return different values
        prompts = ["Hello", "exit"]
        mock_prompt.side_effect = prompts
        
        with patch.object(cli_instance, "stream") as mock_stream:
            cli_instance.interactive()
            
            # Should create session and show intro
            mock_print.assert_any_call("Interactive Claude Session")
            
            # Should process first prompt
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0]
            assert call_args[0] == "Hello"
    
    def test_interactive_commands(self, cli_instance, mock_prompt, mock_print):
        """Test interactive commands."""
        prompts = ["/help", "exit"]
        mock_prompt.side_effect = prompts
        
        cli_instance.interactive()
        
        # Should show help
        mock_print.assert_any_call("Commands:")
        mock_print.assert_any_call("  /help - Show this help")
    
    def test_interactive_keyboard_interrupt(self, cli_instance, mock_prompt, mock_print_warning):
        """Test handling keyboard interrupt."""
        mock_prompt.side_effect = [KeyboardInterrupt(), "exit"]
        
        cli_instance.interactive()
        
        mock_print_warning.assert_called_with("Use 'exit' or 'quit' to end session")


@pytest.mark.unit
def test_main_entry_point():
    """Test main entry point."""
    with patch("fire.Fire") as mock_fire:
        main()
        
        mock_fire.assert_called_once_with(ClaudeCLI)