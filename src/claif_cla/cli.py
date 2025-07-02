"""Fire-based CLI forClaif Claude wrapper."""

import asyncio
import os
import sys
import time

import fire
from claif.common import (
    ClaifOptions,
    Message,
    MessageRole,
    ResponseMetrics,
    format_metrics,
    format_response,
)
from claif.common.config import load_config
from loguru import logger

from claif_cla import query
from claif_cla.session import SessionManager

# from claif_cla.wrapper import ClaudeWrapper


def _print(message: str) -> None:
    """Simple print function for output."""


def _print_error(message: str) -> None:
    """Print error message."""


def _print_success(message: str) -> None:
    """Print success message."""


def _print_warning(message: str) -> None:
    """Print warning message."""


def _confirm(message: str) -> bool:
    """Simple confirmation prompt."""
    response = input(f"{message} (y/N): ").strip().lower()
    return response in ("y", "yes")


def _prompt(message: str) -> str:
    """Simple input prompt."""
    return input(f"{message}: ").strip()


class ClaudeCLI:
    """Claif Claude CLI with Fire interface."""

    def __init__(self, config_file: str | None = None, *, verbose: bool = False):
        """Initialize CLI with optional config file."""
        self.config = load_config(config_file)
        if verbose:
            self.config.verbose = True
        # self.wrapper = ClaudeWrapper(self.config)
        self.session_manager = SessionManager(self.config.session_dir)
        logger.debug("Initialized Claude CLI")

    def ask(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system: str | None = None,
        timeout: int | None = None,
        output_format: str = "text",
        *,
        show_metrics: bool = False,
        session: str | None = None,
        cache: bool = True,
    ) -> None:
        """Execute a single query to Claude.

        Args:
            prompt: The prompt to send
            model: Model to use (e.g., 'claude-3-opus-20240229')
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            system: System prompt
            timeout: Timeout in seconds
            output_format: Output format (text, json, markdown)
            show_metrics: Show response metrics
            session: Session ID to use/create
            cache: Enable response caching
        """
        options = ClaifOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system,
            timeout=timeout,
            output_format=output_format,
            session_id=session,
            cache=cache,
            verbose=self.config.verbose,
        )

        start_time = time.time()

        try:
            # Run async query
            messages = asyncio.run(self._ask_async(prompt, options))

            # Format and display response
            for message in messages:
                formatted = format_response(message, output_format)
                _print(formatted)

            # Show metrics if requested
            if show_metrics:
                duration = time.time() - start_time
                metrics = ResponseMetrics(
                    duration=duration,
                    provider="claude",
                    model=model or "default",
                )
                _print("\n" + format_metrics(metrics))

        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details")
            sys.exit(1)

    async def _ask_async(self, prompt: str, options: ClaifOptions) -> list[Message]:
        """Execute async query and collect messages."""
        messages = []

        async for claude_msg in query(prompt, options):
            # Convert Claude message toClaif message
            msg = Message(
                role=MessageRole(claude_msg.role),
                content=claude_msg.content,
            )
            messages.append(msg)

            # Save to session if enabled
            if options.session_id:
                self.session_manager.add_message(options.session_id, msg)

        return messages

    def stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system: str | None = None,
        timeout: int | None = None,
        session: str | None = None,
    ) -> None:
        """Stream responses from Claude with live display.

        Args:
            prompt: The prompt to send
            model: Model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            system: System prompt
            timeout: Timeout in seconds
            session: Session ID to use/create
        """
        options = ClaifOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system,
            timeout=timeout,
            session_id=session,
            verbose=self.config.verbose,
        )

        try:
            asyncio.run(self._stream_async(prompt, options))
        except KeyboardInterrupt:
            _print_warning("Stream interrupted")
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details")
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: ClaifOptions) -> None:
        """Stream responses with live display."""
        content_buffer = []

        async for claude_msg in query(prompt, options):
            # Collect content for streaming display
            if isinstance(claude_msg.content, str):
                content_buffer.append(claude_msg.content)
                # Print incrementally for streaming effect
            elif isinstance(claude_msg.content, list):
                for block in claude_msg.content:
                    if hasattr(block, "text"):
                        content_buffer.append(block.text)

            # Save to session if enabled
            if options.session_id:
                msg = Message(
                    role=MessageRole(claude_msg.role),
                    content=claude_msg.content,
                )
                self.session_manager.add_message(options.session_id, msg)

    def session(self, action: str = "list", session_id: str | None = None, **kwargs) -> None:
        """Manage conversation sessions.

        Args:
            action: Action to perform (list, create, delete, show, export,
                   branch, merge)
            session_id: Session ID for actions that require it
            **kwargs: Additional arguments for specific actions
        """
        if action == "list":
            sessions = self.session_manager.list_sessions()
            if not sessions:
                _print_warning("No sessions found")
            else:
                _print("Active Sessions:")
                for sid in sessions:
                    info = self.session_manager.get_session_info(sid)
                    count = info.get("message_count", 0)
                    _print(f"  • {sid}: {count} messages")

        elif action == "create":
            session_id = session_id or self.session_manager.create_session()
            _print_success(f"Created session: {session_id}")

        elif action == "delete":
            if not session_id:
                _print_error("Session ID required")
                return
            if _confirm(f"Delete session {session_id}?"):
                self.session_manager.delete_session(session_id)
                _print_success(f"Deleted session: {session_id}")

        elif action == "show":
            if not session_id:
                _print_error("Session ID required")
                return
            messages = self.session_manager.get_messages(session_id)
            for msg in messages:
                _print(f"{msg.role}:")
                _print(format_response(msg))
                _print("")

        elif action == "export":
            if not session_id:
                _print_error("Session ID required")
                return
            output_format_str = kwargs.get("format", "markdown")
            output = kwargs.get("output")
            content = self.session_manager.export_session(session_id, output_format_str)

            if output:
                with open(output, "w") as f:
                    f.write(content)
                _print_success(f"Exported to {output}")
            else:
                _print(content)

        elif action == "branch":
            if not session_id:
                _print_error("Session ID required")
                return
            point = kwargs.get("point", -1)
            new_id = self.session_manager.branch_session(session_id, point)
            _print_success(f"Branched to new session: {new_id}")

        elif action == "merge":
            if not session_id:
                _print_error("Session ID required")
                return
            other_id = kwargs.get("other")
            if not other_id:
                _print_error("Other session ID required (--other)")
                return
            strategy = kwargs.get("strategy", "append")
            self.session_manager.merge_sessions(session_id, other_id, strategy)
            _print_success(f"Merged {other_id} into {session_id}")

        else:
            _print_error(f"Unknown action: {action}")
            actions = "list, create, delete, show, export, branch, merge"
            _print(f"Available actions: {actions}")

    def health(self) -> None:
        """Check Claude service health."""
        try:
            _print("Checking Claude health...")

            # Simple health check - try a minimal query
            result = asyncio.run(self._health_check())

            if result:
                _print_success("Claude service is healthy")
            else:
                _print_error("Claude service is not responding")
                sys.exit(1)

        except Exception as e:
            _print_error(f"Health check failed: {e}")
            sys.exit(1)

    async def _health_check(self) -> bool:
        """Perform health check."""
        try:
            options = ClaifOptions(max_tokens=10, timeout=10)
            message_count = 0

            async for _ in query("Hello", options):
                message_count += 1
                if message_count > 0:
                    return True

            return message_count > 0
        except Exception:
            return False

    def benchmark(
        self,
        prompt: str = "What is 2+2?",
        iterations: int = 5,
        model: str | None = None,
    ) -> None:
        """Benchmark Claude performance.

        Args:
            prompt: Prompt to use for benchmarking
            iterations: Number of iterations
            model: Model to benchmark
        """
        _print("Benchmarking Claude")
        _print(f"Prompt: {prompt}")
        _print(f"Iterations: {iterations}")
        _print(f"Model: {model or 'default'}")
        _print("")

        times = []
        options = ClaifOptions(model=model, cache=False)

        for i in range(iterations):
            _print(f"Running iteration {i + 1}/{iterations}...")
            start = time.time()
            try:
                asyncio.run(self._benchmark_iteration(prompt, options))
                duration = time.time() - start
                times.append(duration)
                _print(f"  Completed in {duration:.3f}s")
            except Exception as e:
                _print_error(f"Iteration {i + 1} failed: {e}")

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            _print("\nResults:")
            _print(f"Average: {avg_time:.3f}s")
            _print(f"Min: {min_time:.3f}s")
            _print(f"Max: {max_time:.3f}s")
        else:
            _print_error("No successful iterations")

    async def _benchmark_iteration(self, prompt: str, options: ClaifOptions) -> None:
        """Run a single benchmark iteration."""
        message_count = 0
        async for _ in query(prompt, options):
            message_count += 1
        if message_count == 0:
            msg = "No response received"
            raise Exception(msg)

    def install(self) -> None:
        """Install Claude provider (npm package + bundling + installation).

        This will:
        1. Install bun if not available
        2. Install the latest @anthropic-ai/claude-code package
        3. Bundle it into a standalone executable
        4. Install the executable to ~/.local/bin (or equivalent)
        """
        from claif_cla.install import install_claude

        _print("Installing Claude provider...")
        result = install_claude()

        if result["installed"]:
            _print_success("Claude provider installed successfully!")
            _print_success("You can now use the 'claude' command from anywhere")
        else:
            error_msg = result.get("message", "Unknown error")
            _print_error(f"Failed to install Claude provider: {error_msg}")
            if result.get("failed"):
                failed_str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_str}")
            sys.exit(1)

    def uninstall(self) -> None:
        """Uninstall Claude provider (remove bundled executable).

        This will remove the bundled Claude executable from the install
        directory.
        """
        from claif_cla.install import uninstall_claude

        _print("Uninstalling Claude provider...")
        result = uninstall_claude()

        if result["uninstalled"]:
            _print_success("Claude provider uninstalled successfully!")
        else:
            error_msg = result.get("message", "Unknown error")
            _print_error(f"Failed to uninstall Claude provider: {error_msg}")
            if result.get("failed"):
                failed_str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_str}")
            sys.exit(1)

    def status(self) -> None:
        """Show Claude provider installation status."""
        import shutil

        from claif_cla.install import get_claude_status, get_install_location

        _print("Claude Provider Status")
        _print("")

        # Get installation status
        status = get_claude_status()
        install_dir = get_install_location()

        if status["installed"]:
            path_info = f"{status['path']} ({status['type']})"
            _print_success(f"Installed: {path_info}")
        else:
            _print_warning("Not installed")

        # Check if command is available in PATH
        try:
            if shutil.which("claude"):
                _print_success("'claude' command available in PATH")
            else:
                _print_warning("'claude' command not in PATH")
        except Exception:
            _print_error("Error checking command availability")

        # Show install directory in PATH status
        path_env = os.environ.get("PATH", "")
        if str(install_dir) in path_env:
            _print_success("Install directory in PATH")
        else:
            _print_warning(f"Install directory not in PATH: {install_dir}")
            path_cmd = 'export PATH="$HOME/.local/bin:$PATH"'
            _print(f"  Add to PATH with: {path_cmd}")

        _print("\nHelpful Commands:")
        _print("  claif_cla install - Install Claude provider")
        _print("  claif_cla uninstall - Uninstall Claude provider")
        _print("  claif_cla health - Check Claude service health")

    def interactive(self, session: str | None = None) -> None:
        """Start an interactive session with Claude.

        Args:
            session: Session ID to use/create
        """
        session_id = session or self.session_manager.create_session()
        _print("Interactive Claude Session")
        _print(f"Session ID: {session_id}")
        _print("Type 'exit' or 'quit' to end session")
        _print("Type '/help' for commands")
        _print("")

        while True:
            try:
                prompt = _prompt("You")

                if prompt.lower() in ("exit", "quit"):
                    break

                if prompt.startswith("/"):
                    self._handle_command(prompt, session_id)
                    continue

                _print("\nClaude:")
                self.stream(prompt, session=session_id)
                _print("")

            except KeyboardInterrupt:
                _print_warning("Use 'exit' or 'quit' to end session")
            except Exception as e:
                _print_error(str(e))

    def _handle_command(self, command: str, session_id: str) -> None:
        """Handle interactive session commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/help":
            _print("Commands:")
            _print("  /help - Show this help")
            _print("  /clear - Clear screen")
            _print("  /save - Save session")
            _print("  /history - Show session history")
            _print("  /model <name> - Change model")
            _print("  /system <prompt> - Set system prompt")

        elif cmd == "/clear":
            os.system("clear" if os.name != "nt" else "cls")

        elif cmd == "/save":
            self.session_manager.save_session(session_id)
            _print_success("Session saved")

        elif cmd == "/history":
            messages = self.session_manager.get_messages(session_id)
            for msg in messages:
                _print(f"{msg.role}: {msg.content}")

        elif cmd == "/model":
            if len(parts) > 1:
                # TODO: Implement model switching
                _print_warning("Model switching not yet implemented")
            else:
                _print_error("Model name required")

        elif cmd == "/system":
            if len(parts) > 1:
                # TODO: Implement system prompt setting
                _print_warning("System prompt setting not yet implemented")
            else:
                _print_error("System prompt required")

        else:
            _print_error(f"Unknown command: {cmd}")


def main():
    """Main CLI entry point."""
    fire.Fire(ClaudeCLI)
