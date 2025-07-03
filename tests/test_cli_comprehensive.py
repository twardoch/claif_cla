"""Comprehensive tests for claif_cla CLI module."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from claif.common import ClaifOptions, Message, MessageRole, Provider

from claif_cla.cli import ClaudeCLI, main


@pytest.mark.unit
class TestClaudeCLIInitialization:
    """Test CLI initialization scenarios."""

    def test_cli_init_with_defaults(self):
        """Test CLI initialization with default settings."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp/sessions"), approval_strategy="default")
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            assert cli.config == mock_config
            assert cli.session_manager is not None
            assert cli.approval_strategy is not None
            mock_load_config.assert_called_once_with(None)

    def test_cli_init_with_config_file(self):
        """Test CLI initialization with custom config file."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=True, session_dir=Path("/custom/sessions"), approval_strategy="allow_all")
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI(config_file="/path/to/config.json")

            assert cli.config == mock_config
            mock_load_config.assert_called_once_with("/path/to/config.json")

    def test_cli_init_verbose_override(self):
        """Test verbose flag overrides config."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False)
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI(verbose=True)

            assert cli.config.verbose is True


@pytest.mark.unit
class TestClaudeCLIAskCommand:
    """Test the ask command functionality."""

    @patch("claif_cla.cli.query")
    @patch("claif_cla.cli.print")
    def test_ask_simple_query(self, mock_print, mock_query):
        """Test simple ask query."""

        # Setup mock response
        async def mock_query_gen(*args, **kwargs):
            yield Message(role=MessageRole.ASSISTANT, content="Test response")

        mock_query.return_value = mock_query_gen()

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            # Run ask command
            cli.ask("What is Python?")

            # Verify query was called
            mock_query.assert_called_once()
            args, kwargs = mock_query.call_args
            assert args[0] == "What is Python?"

            # Verify output
            mock_print.assert_called()

    @patch("claif_cla.cli.query")
    @patch("claif_cla.cli.format_response")
    @patch("claif_cla.cli.print")
    def test_ask_with_options(self, mock_print, mock_format_response, mock_query):
        """Test ask with various options."""
        mock_format_response.return_value = "Formatted response"

        async def mock_query_gen(*args, **kwargs):
            yield Message(role=MessageRole.ASSISTANT, content="Response")

        mock_query.return_value = mock_query_gen()

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            # Run ask with options
            cli.ask(
                "Test query",
                model="claude-3-opus",
                temperature=0.5,
                max_tokens=1000,
                system="Be helpful",
                output_format="json",
            )

            # Verify options were passed correctly
            mock_query.assert_called_once()
            args, kwargs = mock_query.call_args
            options = args[1]

            assert isinstance(options, ClaifOptions)
            assert options.model == "claude-3-opus"
            assert options.temperature == 0.5
            assert options.max_tokens == 1000
            assert options.system_prompt == "Be helpful"
            assert options.output_format == "json"

    @patch("claif_cla.cli.query")
    @patch("claif_cla.cli.print")
    def test_ask_with_session_save(self, mock_print, mock_query):
        """Test ask saves to session."""

        async def mock_query_gen(*args, **kwargs):
            yield Message(role=MessageRole.USER, content="User input")
            yield Message(role=MessageRole.ASSISTANT, content="Assistant response")

        mock_query.return_value = mock_query_gen()

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            # Mock session manager
            with patch.object(cli.session_manager, "save_session") as mock_save:
                cli.ask("Test query", session_id="test-session")

                # Verify session was saved
                mock_save.assert_called_once()
                session = mock_save.call_args[0][0]
                assert session.id == "test-session"
                assert len(session.messages) == 2

    @patch("claif_cla.cli.query")
    @patch("claif_cla.cli.print")
    def test_ask_error_handling(self, mock_print, mock_query):
        """Test error handling in ask command."""

        async def mock_error_query(*args, **kwargs):
            msg = "Test error"
            raise ValueError(msg)
            yield  # Make it a generator

        mock_query.side_effect = mock_error_query

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            # Should handle error gracefully
            cli.ask("Test query")

            # Verify error was printed
            mock_print.assert_called()
            assert any("Error" in str(call) for call in mock_print.call_args_list)


@pytest.mark.unit
class TestClaudeCLIStreamCommand:
    """Test the stream command functionality."""

    @patch("claif_cla.cli.query")
    @patch("claif_cla.cli.Console")
    def test_stream_basic(self, mock_console_class, mock_query):
        """Test basic streaming functionality."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        mock_live = MagicMock()

        with patch("claif_cla.cli.Live") as mock_live_class:
            mock_live_class.return_value.__enter__.return_value = mock_live

            async def mock_stream_gen(*args, **kwargs):
                yield Message(role=MessageRole.ASSISTANT, content="Part 1")
                yield Message(role=MessageRole.ASSISTANT, content="Part 2")

            mock_query.return_value = mock_stream_gen()

            with patch("claif_cla.cli.load_config") as mock_load_config:
                mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
                mock_load_config.return_value = mock_config

                cli = ClaudeCLI()
                cli.stream("Test query")

                # Verify live updates
                assert mock_live.update.call_count >= 2


@pytest.mark.unit
class TestClaudeCLISessionCommands:
    """Test session management commands."""

    def test_session_list(self):
        """Test listing sessions."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            # Mock session manager
            mock_sessions = [
                Mock(id="session-1", created_at="2024-01-01", message_count=5),
                Mock(id="session-2", created_at="2024-01-02", message_count=10),
            ]

            with patch.object(cli.session_manager, "list_sessions", return_value=mock_sessions):
                with patch("claif_cla.cli.print") as mock_print:
                    cli.session(list=True)

                    # Verify sessions were printed
                    assert mock_print.call_count >= 2

    def test_session_create(self):
        """Test creating a new session."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            with patch.object(cli.session_manager, "create_session") as mock_create:
                mock_session = Mock(id="new-session-123")
                mock_create.return_value = mock_session

                with patch("claif_cla.cli.print") as mock_print:
                    cli.session(create=True)

                    mock_create.assert_called_once()
                    mock_print.assert_called()

    def test_session_delete(self):
        """Test deleting a session."""
        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()

            with patch("claif_cla.cli.prompt") as mock_prompt:
                mock_prompt.return_value = True  # Confirm deletion

                with patch.object(cli.session_manager, "delete_session") as mock_delete:
                    with patch("claif_cla.cli.print") as mock_print:
                        cli.session(delete="test-session")

                        mock_delete.assert_called_once_with("test-session")
                        mock_print.assert_called()


@pytest.mark.unit
class TestClaudeCLIHealthCommand:
    """Test health check command."""

    @patch("claif_cla.cli.claude_query")
    @patch("claif_cla.cli.print")
    def test_health_check_success(self, mock_print, mock_claude_query):
        """Test successful health check."""

        async def mock_health_query(*args, **kwargs):
            yield Mock()  # Any response indicates success

        mock_claude_query.return_value = mock_health_query()

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()
            cli.health()

            # Verify success message
            assert any("healthy" in str(call).lower() for call in mock_print.call_args_list)

    @patch("claif_cla.cli.claude_query")
    @patch("claif_cla.cli.print")
    def test_health_check_failure(self, mock_print, mock_claude_query):
        """Test failed health check."""

        async def mock_health_error(*args, **kwargs):
            msg = "Cannot connect"
            raise ConnectionError(msg)
            yield

        mock_claude_query.side_effect = mock_health_error

        with patch("claif_cla.cli.load_config") as mock_load_config:
            mock_config = Mock(verbose=False, session_dir=Path("/tmp"))
            mock_load_config.return_value = mock_config

            cli = ClaudeCLI()
            cli.health()

            # Verify error message
            assert any("error" in str(call).lower() for call in mock_print.call_args_list)


@pytest.mark.unit
class TestClaudeCLIMain:
    """Test main entry point."""

    @patch("claif_cla.cli.fire.Fire")
    def test_main_function(self, mock_fire):
        """Test main function launches Fire."""
        main()

        mock_fire.assert_called_once_with(ClaudeCLI)

    @patch("claif_cla.cli.fire.Fire")
    @patch("claif_cla.cli.prompt_tool_configuration")
    def test_main_with_tool_config(self, mock_prompt_config, mock_fire):
        """Test main with tool configuration prompt."""
        mock_prompt_config.return_value = True

        main()

        mock_fire.assert_called_once_with(ClaudeCLI)
