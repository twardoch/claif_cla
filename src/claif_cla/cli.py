"""Fire-based CLI for Claif Claude wrapper."""

import asyncio
import os
import sys
import time
from typing import Any, Dict, List, Optional

import fire
from claif.common import (
    ClaifOptions,
    Message,
    MessageRole,
    Provider,
    ResponseMetrics,
    TextBlock,
    format_metrics,
    format_response,
)
from claif.common.config import load_config

# from claif_cla.wrapper import ClaudeWrapper
from claif.common.utils import _confirm, _print, _print_error, _print_success, _print_warning, _prompt
from loguru import logger

from claif_cla.client import query
from claif_cla.session import SessionManager


def main():
    """Main entry point for Fire CLI."""
    fire.Fire(ClaudeCLI)


# from claif_cla.wrapper import ClaudeWrapper


class ClaudeCLI:
    """Claif Claude CLI with Fire interface."""

    def __init__(self, config_file: str | None = None, *, verbose: bool = False):
        """Initialize CLI with optional config file."""
        self.config = load_config(config_file)
        if verbose:
            self.config.verbose = True
        # self.wrapper = ClaudeWrapper(self.config)
        self.session_manager: SessionManager | None = None
        logger.debug("Initialized Claude CLI")

    async def _get_session_manager(self) -> SessionManager:
        """Get or create the session manager."""
        if self.session_manager is None:
            self.session_manager = SessionManager(self.config.session_dir)
            await self.session_manager.initialize()
        return self.session_manager

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
        no_retry: bool = False,
    ) -> None:
        """
        Executes a single query to the Claude LLM and displays the response.

        This method orchestrates the entire query process, including option parsing,
        asynchronous execution, and result formatting. It also supports session
        management and caching.

        Args:
            prompt: The textual prompt to send to the Claude model.
            model: Optional. The specific Claude model to use (e.g., 'claude-3-opus-20240229').
            temperature: Optional. Controls the randomness of the output (0.0 to 1.0).
            max_tokens: Optional. Maximum number of tokens in the generated response.
            system: Optional. A system-level prompt to guide the model's behavior.
            timeout: Optional. Maximum time in seconds to wait for a response.
            output_format: The desired format for the output ('text', 'json', or 'markdown').
            show_metrics: If True, displays performance metrics of the query.
            session: Optional. The ID of the session to use or create for this conversation.
            cache: If True, enables response caching for this query.
            no_retry: If True, disables all retry attempts for the query.
        """
        options: ClaifOptions = ClaifOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system,
            timeout=timeout,
            output_format=output_format,
            session_id=session,
            cache=cache,
            verbose=self.config.verbose,
            no_retry=no_retry,
        )

        start_time: float = time.time()  # Record the start time for metrics calculation.

        try:
            # Run the asynchronous query and collect all messages.
            messages: list[Message] = asyncio.run(self._ask_async(prompt, options))

            # Format and display response.
            for message in messages:
                formatted_output: str = format_response(message, output_format)
                _print(formatted_output)

            # If requested, calculate and display response metrics.
            if show_metrics:
                duration: float = time.time() - start_time
                metrics: ResponseMetrics = ResponseMetrics(
                    duration=duration,
                    provider=Provider.CLAUDE,
                    model=model or "default",  # Use "default" if no specific model was provided.
                )
                _print(f"\n{format_metrics(metrics)}")

        except Exception as e:
            # Catch any exceptions during the query process, print an error message,
            # and exit with a non-zero status code to indicate failure.
            _print_error(str(e))
            if self.config.verbose:
                # If verbose mode is enabled, print the full traceback for debugging.
                logger.exception("Full error details for Claude query failure:")
            sys.exit(1)

    async def _ask_async(self, prompt: str, options: ClaifOptions) -> list[Message]:
        """
        Asynchronously executes a Claude query and collects all messages.

        This method interacts with the underlying Claude query function and
        integrates with the session manager to store conversation history.

        Args:
            prompt: The prompt to send to the Claude model.
            options: Configuration options for the Claude query, including session ID.

        Returns:
            A list of `Message` objects received from the Claude API.
        """
        messages: list[Message] = []
        manager: SessionManager = await self._get_session_manager()

        async for claude_msg in query(prompt, options):
            # Convert the Claude-specific message format to the generic Claif Message format.
            msg: Message = Message(
                role=MessageRole(claude_msg.role),
                content=claude_msg.content,
            )
            messages.append(msg)

            # If a session ID is provided in the options, add the message to the session history.
            if options.session_id:
                await manager.add_message(options.session_id, msg)

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
        no_retry: bool = False,
    ) -> None:
        """
        Streams responses from the Claude LLM and displays them live.

        This method is suitable for long-running queries where incremental
        updates are desired. It also integrates with session management.

        Args:
            prompt: The textual prompt to send to the Claude model.
            model: Optional. The specific Claude model to use.
            temperature: Optional. Controls the randomness of the output (0.0 to 1.0).
            max_tokens: Optional. Maximum number of tokens in the generated response.
            system: Optional. A system-level prompt to guide the model's behavior.
            timeout: Optional. Maximum time in seconds to wait for a response.
            session: Optional. The ID of the session to use or create for this conversation.
            no_retry: If True, disables all retry attempts for the query.
        """
        options: ClaifOptions = ClaifOptions(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system,
            timeout=timeout,
            session_id=session,
            verbose=self.config.verbose,
            no_retry=no_retry,
        )

        try:
            asyncio.run(self._stream_async(prompt, options))
        except KeyboardInterrupt:
            _print_warning("Stream interrupted by user.")
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details for Claude stream failure:")
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: ClaifOptions) -> None:
        """
        Asynchronously streams responses from the Claude CLI and prints them.

        Args:
            prompt: The prompt to send to the Claude model.
            options: Configuration options for the Claude query.
        """
        manager: SessionManager = await self._get_session_manager()

        async for claude_msg in query(prompt, options):
            # Convert the Claude-specific message format to the generic Claif Message format.
            msg: Message = Message(
                role=MessageRole(claude_msg.role),
                content=claude_msg.content,
            )

            # Print content for streaming display
            if isinstance(msg.content, str):
                _print(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        _print(block.text)
                    # Add handling for other block types if needed for streaming display

            # Save to session if enabled
            if options.session_id:
                await manager.add_message(options.session_id, msg)

            # Add a newline after each message for better readability in stream mode
            _print("")

    def session(self, action: str = "list", session_id: str | None = None, **kwargs: Any) -> None:
        """
        Manages conversation sessions, allowing users to list, create, delete, show,
        export, branch, and merge sessions.

        Args:
            action: The action to perform on sessions. Supported actions include:
                    'list': List all available sessions.
                    'create': Create a new session. Can specify `session_id` or `template`.
                    'delete': Delete a session. Requires `session_id`.
                    'show': Display messages within a session. Requires `session_id`.
                    'export': Export session messages to a file or stdout. Requires `session_id`.
                              Can specify `format` (markdown, json) and `output` file path.
                    'branch': Create a new session from a point in an existing session.
                              Requires `session_id` and optional `point`.
                    'merge': Merge two sessions. Requires `session_id` (target) and `other` (source).
                             Can specify `strategy` (append, interleave).
            session_id: Optional. The ID of the session to operate on.
            **kwargs: Additional arguments specific to each action (e.g., `template`, `format`, `output`, `point`, `other`, `strategy`).
        """
        try:
            asyncio.run(self._session_async(action, session_id, **kwargs))
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details for session command failure:")
            sys.exit(1)

    async def _session_async(self, action: str, session_id: str | None, **kwargs: Any) -> None:
        """
        Asynchronous implementation for session management commands.

        Args:
            action: The action to perform.
            session_id: The ID of the session to operate on.
            **kwargs: Additional arguments for specific actions.
        """
        manager: SessionManager = await self._get_session_manager()

        if action == "list":
            sessions: list[str] = await manager.list_sessions()
            if not sessions:
                _print_warning("No sessions found.")
            else:
                _print("\n[bold underline]Active Sessions:[/bold underline]")
                for sid in sessions:
                    info: dict[str, Any] = await manager.get_session_info(sid)
                    count: int = info.get("message_count", 0)
                    _print(f"  • [cyan]{sid}[/cyan]: {count} messages")

        elif action == "create":
            template_name: str | None = kwargs.get("template")
            try:
                new_session_id: str = await manager.create_session(session_id, template_name=template_name)
                _print_success(f"Created session: [cyan]{new_session_id}[/cyan]")
            except ValueError as e:
                _print_error(str(e))

        elif action == "delete":
            if not session_id:
                _print_error("Session ID is required for 'delete' action.")
                return
            if _confirm(
                f"Are you sure you want to delete session [cyan]{session_id}[/cyan]? This action cannot be undone."
            ):
                await manager.delete_session(session_id)
                _print_success(f"Deleted session: [cyan]{session_id}[/cyan]")
            else:
                _print("Session deletion cancelled.")

        elif action == "show":
            if not session_id:
                _print_error("Session ID is required for 'show' action.")
                return
            messages: list[Message] = await manager.get_messages(session_id)
            if not messages:
                _print_warning(f"Session [cyan]{session_id}[/cyan] has no messages.")
            else:
                _print(f"\n[bold underline]Messages for Session [cyan]{session_id}[/cyan]:[/bold underline]")
                for msg in messages:
                    _print(f"[bold]{msg.role.value.upper()}:[/bold]")
                    _print(format_response(msg))
                    _print("")

        elif action == "export":
            if not session_id:
                _print_error("Session ID is required for 'export' action.")
                return
            output_format_str: str = kwargs.get("format", "markdown")
            output_file: str | None = kwargs.get("output")

            try:
                content: str = await manager.export_session(session_id, output_format_str)

                if output_file:
                    with open(output_file, "w") as f:
                        f.write(content)
                    _print_success(
                        f"Session [cyan]{session_id}[/cyan] exported to [green]{output_file}[/green] in {output_format_str} format."
                    )
                else:
                    _print(content)
            except ValueError as e:
                _print_error(str(e))

        elif action == "branch":
            if not session_id:
                _print_error("Session ID is required for 'branch' action.")
                return
            point: int = int(kwargs.get("point", -1))
            try:
                new_id: str = await manager.branch_session(session_id, point)
                _print_success(
                    f"Branched session [cyan]{session_id}[/cyan] to new session: [cyan]{new_id}[/cyan] at message point {point}."
                )
            except ValueError as e:
                _print_error(str(e))

        elif action == "merge":
            if not session_id:
                _print_error("Target session ID is required for 'merge' action.")
                return
            other_id: str | None = kwargs.get("other")
            if not other_id:
                _print_error("Source session ID (--other) is required for 'merge' action.")
                return
            strategy: str = kwargs.get("strategy", "append")
            try:
                await manager.merge_sessions(session_id, other_id, strategy)
                _print_success(
                    f"Merged session [cyan]{other_id}[/cyan] into [cyan]{session_id}[/cyan] using '{strategy}' strategy."
                )
            except ValueError as e:
                _print_error(str(e))

        else:
            _print_error(f"Unknown session action: {action}")
            actions: str = "list, create, delete, show, export, branch, merge"
            _print(f"Available actions: {actions}")

    def health(self) -> None:
        """
        Checks the health and responsiveness of the Claude service.

        This performs a simple query to the Claude CLI to verify that it is
        properly installed, configured, and able to return a response.
        """
        try:
            _print("Checking Claude service health...")

            # Execute a simple asynchronous health check query.
            is_healthy: bool = asyncio.run(self._health_check())

            if is_healthy:
                _print_success("Claude service is healthy and responding.")
            else:
                _print_error("Claude service is not responding or health check failed.")
                sys.exit(1)

        except Exception as e:
            _print_error(f"Health check failed due to an unexpected error: {e}")
            if self.config.verbose:
                logger.exception("Full error details for health check failure:")
            sys.exit(1)

    async def _health_check(self) -> bool:
        """
        Performs the actual asynchronous health check query.

        Sends a minimal query to the Claude CLI with a short timeout.

        Returns:
            True if a response is received, False otherwise.
        """
        try:
            # Set a short timeout for the health check query.
            options: ClaifOptions = ClaifOptions(max_tokens=10, timeout=10)
            message_count: int = 0

            # Iterate through messages from a simple query. If any message is received,
            # the service is considered healthy.
            async for _ in query("Hello", options):
                message_count += 1
                # If at least one message is received, consider it a success and return.
                if message_count > 0:
                    return True

            # If the loop completes without receiving any messages, return False.
            return message_count > 0
        except Exception:
            # Catch any exceptions during the health check and return False, indicating failure.
            return False

    def benchmark(
        self,
        prompt: str = "What is 2+2?",
        iterations: int = 5,
        model: str | None = None,
        no_retry: bool = False,
    ) -> None:
        """
        Benchmarks Claude performance by running a query multiple times.

        Args:
            prompt: The prompt to use for benchmarking.
            iterations: The number of times to run the query. Defaults to 5.
            model: Optional. The specific Claude model to benchmark.
            no_retry: If True, disables retry attempts during benchmarking.
        """
        _print("\n[bold underline]Benchmarking Claude Performance[/bold underline]")
        _print(f"Prompt: [cyan]{prompt}[/cyan]")
        _print(f"Iterations: [cyan]{iterations}[/cyan]")
        _print(f"Model: [cyan]{model or 'default'}[/cyan]")
        _print("")

        times: list[float] = []
        options: ClaifOptions = ClaifOptions(model=model, cache=False, no_retry=no_retry)

        for i in range(iterations):
            _print(f"Running iteration [yellow]{i + 1}/{iterations}[/yellow]...")
            start_time: float = time.time()
            try:
                asyncio.run(self._benchmark_iteration(prompt, options))
                duration: float = time.time() - start_time
                times.append(duration)
                _print(f"  Completed in [green]{duration:.3f}s[/green]")
            except Exception as e:
                _print_error(f"Iteration [red]{i + 1}[/red] failed: {e}")

        if times:
            avg_time: float = sum(times) / len(times)
            min_time: float = min(times)
            max_time: float = max(times)

            _print("\n[bold underline]Benchmark Results:[/bold underline]")
            _print(f"Average time: [green]{avg_time:.3f}s[/green]")
            _print(f"Min time: [green]{min_time:.3f}s[/green]")
            _print(f"Max time: [green]{max_time:.3f}s[/green]")
        else:
            _print_error("No successful iterations to report benchmark results.")

    async def _benchmark_iteration(self, prompt: str, options: ClaifOptions) -> None:
        """
        Runs a single iteration of the benchmark query.

        Args:
            prompt: The prompt for the current iteration.
            options: The `ClaifOptions` for the current iteration.

        Raises:
            Exception: If no response is received from the query.
        """
        message_count: int = 0
        async for _ in query(prompt, options):
            message_count += 1
        if message_count == 0:
            msg = "No response received from Claude during benchmark iteration."
            logger.error(msg)
            raise Exception(msg)

    def install(self) -> None:
        """
        Installs the Claude provider, including its npm package and bundling.

        This method performs the following steps:
        1. Ensures 'bun' is installed, as it's required for bundling.
        2. Installs the latest `@anthropic-ai/claude-code` npm package globally.
        3. Bundles the installed package into a standalone executable.
        4. Installs the executable to a well-known local binary directory (e.g., `~/.local/bin`).

        Upon successful installation, it provides instructions on how to add the
        installation directory to the system's PATH for easy access.

        Raises:
            SystemExit: If the installation fails at any step.
        """
        from claif_cla.install import install_claude

        _print("Attempting to install Claude provider...")
        result: dict[str, Any] = install_claude()

        if result.get("installed"):
            _print_success("Claude provider installed successfully!")
            _print_success("You can now use the 'claude' command from anywhere.")
            _print(
                "\nTo ensure the 'claude' command is always available, add the installation directory to your system's PATH. For most Unix-like systems, you can add the following line to your shell's profile file (e.g., ~/.bashrc, ~/.zshrc, or ~/.profile):\n"
            )
            _print(f'  export PATH="{result.get("install_dir", "~/.local/bin")}:$PATH"')
            _print("\nAfter adding, run 'source ~/.bashrc' (or your respective profile file) to apply the changes.")
        else:
            error_msg: str = result.get("message", "Unknown installation error.")
            _print_error(f"Failed to install Claude provider: {error_msg}")
            if result.get("failed"):
                failed_components: str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_components}")
            sys.exit(1)

    def uninstall(self) -> None:
        """
        Uninstalls the Claude provider by removing its bundled executable and associated directory.

        This method attempts to remove the Claude CLI executable from the
        installation directory. It also removes the `claude-bin` directory
        where the actual executable resides.

        Raises:
            SystemExit: If the uninstallation fails.
        """
        from claif_cla.install import uninstall_claude

        _print("Attempting to uninstall Claude provider...")
        result: dict[str, Any] = uninstall_claude()

        if result.get("uninstalled"):
            _print_success("Claude provider uninstalled successfully!")
        else:
            error_msg: str = result.get("message", "Unknown uninstallation error.")
            _print_error(f"Failed to uninstall Claude provider: {error_msg}")
            if result.get("failed"):
                failed_components: str = ", ".join(result["failed"])
                _print_error(f"Failed components: {failed_components}")
            sys.exit(1)

    def status(self) -> None:
        """
        Displays the installation status of the Claude provider.

        This method checks for the presence of the main 'claude' wrapper script,
        the 'claude-bin' installation directory, and verifies if the installation
        directory is included in the system's PATH.
        """
        import shutil

        from claif.common.install import find_executable, get_install_location

        from claif_cla.install import get_claude_status

        _print("\n[bold underline]Claude Provider Status[/bold underline]")

        # Get installation status from claif_cla.install
        status_info: dict[str, Any] = get_claude_status()
        install_dir: Path = get_install_location()

        if status_info.get("installed"):
            path_info: str = f"{status_info['path']} ({status_info['type']})"
            _print_success(f"Installed: [green]{path_info}[/green]")
        else:
            _print_warning("Not installed: [yellow]Claude CLI not found in expected locations.[/yellow]")

        # Check if 'claude' command is available in system PATH
        try:
            if shutil.which("claude"):
                _print_success("'claude' command available in system PATH.")
            else:
                _print_warning("'claude' command not found in system PATH. You might need to add it manually.")
        except Exception as e:
            _print_error(f"Error checking 'claude' command availability: {e}")

        # Show install directory in PATH status
        path_env: str = os.environ.get("PATH", "")
        if str(install_dir) in path_env:
            _print_success("Installation directory is in system PATH.")
        else:
            _print_warning(f"Installation directory [yellow]{install_dir}[/yellow] is NOT in system PATH.")
            path_cmd: str = f'export PATH="{install_dir}:$PATH"'
            _print(f"  To add it, run: [cyan]{path_cmd}[/cyan]")
            _print("  (Remember to source your shell's profile file afterwards, e.g., ~/.bashrc or ~/.zshrc)")

        _print("\n[bold underline]Helpful Commands:[/bold underline]")
        _print("  [cyan]claif_cla install[/cyan] - Install Claude provider")
        _print("  [cyan]claif_cla uninstall[/cyan] - Uninstall Claude provider")
        _print("  [cyan]claif_cla health[/cyan] - Check Claude service health")

    def interactive(self, session: str | None = None) -> None:
        """
        Starts an interactive conversational session with Claude.

        Users can type prompts, and the CLI will send them to Claude,
        displaying responses in real-time. Session history is maintained.
        Special commands (prefixed with '/') allow session management.

        Args:
            session: Optional. The ID of an existing session to resume, or a new
                     session will be created if not provided.
        """
        try:
            asyncio.run(self._interactive_async(session))
        except KeyboardInterrupt:
            _print_warning("\nExiting interactive session. Type 'exit' or 'quit' to end gracefully.")
        except Exception as e:
            _print_error(str(e))
            if self.config.verbose:
                logger.exception("Full error details for interactive session failure:")

    async def _interactive_async(self, session_id: str | None) -> None:
        """
        Asynchronous implementation for the interactive session.

        Handles user input, sends queries to Claude, displays responses,
        and processes special commands.

        Args:
            session_id: The ID of the session to use or create.
        """
        manager: SessionManager = await self._get_session_manager()
        if session_id is None:
            session_id = await manager.create_session()

        _print("\n[bold underline]Interactive Claude Session[/bold underline]")
        _print(f"Session ID: [cyan]{session_id}[/cyan]")
        _print("Type 'exit' or 'quit' to end session.")
        _print("Type '/help' for a list of commands.")
        _print("")

        while True:
            try:
                prompt: str = _prompt("You")

                if prompt.lower() in ("exit", "quit"):
                    _print("Ending interactive session.")
                    break

                if prompt.startswith("/"):
                    await self._handle_command(prompt, session_id)
                    continue

                _print("\n[bold]Claude:[/bold]")
                options: ClaifOptions = ClaifOptions(session_id=session_id, verbose=self.config.verbose)
                await self._stream_async(prompt, options)
                _print("")

            except KeyboardInterrupt:
                _print_warning("\nUse 'exit' or 'quit' to end session. Press Ctrl+C again to force exit.")
            except Exception as e:
                _print_error(str(e))
                if self.config.verbose:
                    logger.exception("Error during interactive session:")

    async def _handle_command(self, command: str, session_id: str) -> None:
        """
        Handles special commands entered during an interactive session.

        Args:
            command: The command string (e.g., '/help', '/clear').
            session_id: The ID of the current session.
        """
        parts: list[str] = command.split(maxsplit=1)
        cmd: str = parts[0].lower()
        args: str = parts[1] if len(parts) > 1 else ""
        manager: SessionManager = await self._get_session_manager()

        if cmd == "/help":
            _print("\n[bold underline]Interactive Session Commands:[/bold underline]")
            _print("  [cyan]/help[/cyan] - Show this help message.")
            _print("  [cyan]/clear[/cyan] - Clear the terminal screen.")
            _print("  [cyan]/save[/cyan] - Save the current session to disk.")
            _print("  [cyan]/history[/cyan] - Show the full message history of the current session.")
            _print(
                "  [cyan]/model <name>[/cyan] - Change the model for the current session (e.g., /model claude-3-opus-20240229). (Not yet fully implemented)"
            )
            _print(
                "  [cyan]/system <prompt>[/cyan] - Set a new system prompt for the current session. (Not yet fully implemented)"
            )
            _print(
                "  [cyan]/branch [point][/cyan] - Create a new session branched from the current one at a specific message point."
            )
            _print("  [cyan]/merge <other_session_id> [strategy][/cyan] - Merge another session into the current one.")

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")

        elif cmd == "/save":
            try:
                await manager.save_session(session_id)
                _print_success(f"Session [cyan]{session_id}[/cyan] saved successfully.")
            except ValueError as e:
                _print_error(str(e))

        elif cmd == "/history":
            messages: list[Message] = await manager.get_messages(session_id)
            if not messages:
                _print_warning(f"Session [cyan]{session_id}[/cyan] has no history.")
            else:
                _print(f"\n[bold underline]Session History for [cyan]{session_id}[/cyan]:[/bold underline]")
                for msg in messages:
                    _print(f"[bold]{msg.role.value.upper()}: {msg.content}[/bold]")
                    _print("")

        elif cmd == "/model":
            if args:
                # TODO: Implement actual model switching logic within the session manager or options.
                _print_warning(
                    f"Model switching to '{args}' not yet fully implemented. This will only affect the current query options."
                )
                # Example of how you might update options for subsequent queries:
                # self.config.set_provider_option(Provider.CLAUDE, "model", args)
            else:
                _print_error("Model name required. Usage: /model <name>")

        elif cmd == "/system":
            if args:
                # TODO: Implement actual system prompt setting logic within the session manager or options.
                _print_warning(
                    f"Setting system prompt to '{args}' not yet fully implemented. This will only affect the current query options."
                )
                # Example of how you might update options for subsequent queries:
                # self.config.set_provider_option(Provider.CLAUDE, "system_prompt", args)
            else:
                _print_error("System prompt required. Usage: /system <prompt>")

        elif cmd == "/branch":
            try:
                point: int = int(args) if args else -1
                new_session_id: str = await manager.branch_session(session_id, point)
                _print_success(f"Branched to new session: [cyan]{new_session_id}[/cyan] at message point {point}.")
            except ValueError as e:
                _print_error(f"Invalid branch point: {e}. Usage: /branch [point]")
            except Exception as e:
                _print_error(f"Failed to branch session: {e}")

        elif cmd == "/merge":
            args_parts = args.split(maxsplit=1)
            if len(args_parts) < 1:
                _print_error("Source session ID required. Usage: /merge <other_session_id> [strategy]")
                return

            other_session_id: str = args_parts[0]
            strategy: str = args_parts[1] if len(args_parts) > 1 else "append"

            try:
                await manager.merge_sessions(session_id, other_session_id, strategy)
                _print_success(
                    f"Merged session [cyan]{other_session_id}[/cyan] into [cyan]{session_id}[/cyan] using '{strategy}' strategy."
                )
            except ValueError as e:
                _print_error(f"Merge failed: {e}. Usage: /merge <other_session_id> [strategy]")
            except Exception as e:
                _print_error(f"Failed to merge sessions: {e}")

        else:
            _print_error(f"Unknown command: [red]{cmd}[/red]")
            _print("Type '/help' for available commands.")
