"""Fire-based CLI for CLAIF Claude wrapper."""

import asyncio
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
from claif.common.config import get_config
from loguru import logger
from rich.console import Console
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from claif_cla import query
from claif_cla.session import SessionManager
from claif_cla.wrapper import ClaudeWrapper

console = Console()


class ClaudeCLI:
    """CLAIF Claude CLI with Fire interface."""

    def __init__(self, config_file: str | None = None, *, verbose: bool = False):
        """Initialize CLI with optional config file."""
        self.config = get_config(config_file)
        if verbose:
            self.config.verbose = True
        self.wrapper = ClaudeWrapper(self.config)
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
                console.print(formatted)

            # Show metrics if requested
            if show_metrics:
                duration = time.time() - start_time
                metrics = ResponseMetrics(
                    duration=duration,
                    provider="claude",
                    model=model or "default",
                )
                console.print("\n" + format_metrics(metrics))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if self.config.verbose:
                console.print_exception()
            sys.exit(1)

    async def _ask_async(self, prompt: str, options: ClaifOptions) -> list[Message]:
        """Execute async query and collect messages."""
        messages = []

        async for claude_msg in query(prompt, options):
            # Convert Claude message to CLAIF message
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
            console.print("\n[yellow]Stream interrupted[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            if self.config.verbose:
                console.print_exception()
            sys.exit(1)

    async def _stream_async(self, prompt: str, options: ClaifOptions) -> None:
        """Stream responses with live display."""
        content_buffer = []

        with Live(console=console, refresh_per_second=10) as live:
            async for claude_msg in query(prompt, options):
                # Update live display
                if isinstance(claude_msg.content, str):
                    content_buffer.append(claude_msg.content)
                elif isinstance(claude_msg.content, list):
                    for block in claude_msg.content:
                        if hasattr(block, "text"):
                            content_buffer.append(block.text)

                live.update("".join(content_buffer))

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
            action: Action to perform (list, create, delete, show, export, branch, merge)
            session_id: Session ID for actions that require it
            **kwargs: Additional arguments for specific actions
        """
        if action == "list":
            sessions = self.session_manager.list_sessions()
            if not sessions:
                console.print("[yellow]No sessions found[/yellow]")
            else:
                console.print("[bold]Active Sessions:[/bold]")
                for sid in sessions:
                    info = self.session_manager.get_session_info(sid)
                    console.print(f"  • {sid}: {info.get('message_count', 0)} messages")

        elif action == "create":
            session_id = session_id or self.session_manager.create_session()
            console.print(f"[green]Created session: {session_id}[/green]")

        elif action == "delete":
            if not session_id:
                console.print("[red]Session ID required[/red]")
                return
            if Confirm.ask(f"Delete session {session_id}?"):
                self.session_manager.delete_session(session_id)
                console.print(f"[green]Deleted session: {session_id}[/green]")

        elif action == "show":
            if not session_id:
                console.print("[red]Session ID required[/red]")
                return
            messages = self.session_manager.get_messages(session_id)
            for msg in messages:
                console.print(f"[bold]{msg.role}:[/bold]")
                console.print(format_response(msg))
                console.print()

        elif action == "export":
            if not session_id:
                console.print("[red]Session ID required[/red]")
                return
            output_format_str = kwargs.get("format", "markdown")
            output = kwargs.get("output")
            content = self.session_manager.export_session(session_id, output_format_str)

            if output:
                with open(output, "w") as f:
                    f.write(content)
                console.print(f"[green]Exported to {output}[/green]")
            else:
                console.print(content)

        elif action == "branch":
            if not session_id:
                console.print("[red]Session ID required[/red]")
                return
            point = kwargs.get("point", -1)
            new_id = self.session_manager.branch_session(session_id, point)
            console.print(f"[green]Branched to new session: {new_id}[/green]")

        elif action == "merge":
            if not session_id:
                console.print("[red]Session ID required[/red]")
                return
            other_id = kwargs.get("other")
            if not other_id:
                console.print("[red]Other session ID required (--other)[/red]")
                return
            strategy = kwargs.get("strategy", "append")
            self.session_manager.merge_sessions(session_id, other_id, strategy)
            console.print(f"[green]Merged {other_id} into {session_id}[/green]")

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Available actions: list, create, delete, show, export, branch, merge")

    def health(self) -> None:
        """Check Claude service health."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Checking Claude health...", total=None)

                # Simple health check - try a minimal query
                result = asyncio.run(self._health_check())
                progress.update(task, completed=True)

            if result:
                console.print("[green]✓ Claude service is healthy[/green]")
            else:
                console.print("[red]✗ Claude service is not responding[/red]")
                sys.exit(1)

        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")
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
        console.print("[bold]Benchmarking Claude[/bold]")
        console.print(f"Prompt: {prompt}")
        console.print(f"Iterations: {iterations}")
        console.print(f"Model: {model or 'default'}\n")

        times = []
        options = ClaifOptions(model=model, cache=False)

        with Progress() as progress:
            task = progress.add_task("Running benchmark...", total=iterations)

            for i in range(iterations):
                start = time.time()
                try:
                    asyncio.run(self._benchmark_iteration(prompt, options))
                    duration = time.time() - start
                    times.append(duration)
                except Exception as e:
                    console.print(f"[red]Iteration {i + 1} failed: {e}[/red]")

                progress.update(task, advance=1)

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            console.print("\n[bold]Results:[/bold]")
            console.print(f"Average: {avg_time:.3f}s")
            console.print(f"Min: {min_time:.3f}s")
            console.print(f"Max: {max_time:.3f}s")
        else:
            console.print("[red]No successful iterations[/red]")

    async def _benchmark_iteration(self, prompt: str, options: ClaifOptions) -> None:
        """Run a single benchmark iteration."""
        message_count = 0
        async for _ in query(prompt, options):
            message_count += 1
        if message_count == 0:
            msg = "No response received"
            raise Exception(msg)

    def interactive(self, session: str | None = None) -> None:
        """Start an interactive session with Claude.

        Args:
            session: Session ID to use/create
        """
        session_id = session or self.session_manager.create_session()
        console.print("[bold]Interactive Claude Session[/bold]")
        console.print(f"Session ID: {session_id}")
        console.print("Type 'exit' or 'quit' to end session")
        console.print("Type '/help' for commands\n")

        while True:
            try:
                prompt = Prompt.ask("[bold blue]You[/bold blue]")

                if prompt.lower() in ("exit", "quit"):
                    break

                if prompt.startswith("/"):
                    self._handle_command(prompt, session_id)
                    continue

                console.print("\n[bold green]Claude[/bold green]:")
                self.stream(prompt, session=session_id)
                console.print()

            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'exit' or 'quit' to end session[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def _handle_command(self, command: str, session_id: str) -> None:
        """Handle interactive session commands."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/help":
            console.print("[bold]Commands:[/bold]")
            console.print("  /help - Show this help")
            console.print("  /clear - Clear screen")
            console.print("  /save - Save session")
            console.print("  /history - Show session history")
            console.print("  /model <name> - Change model")
            console.print("  /system <prompt> - Set system prompt")

        elif cmd == "/clear":
            console.clear()

        elif cmd == "/save":
            self.session_manager.save_session(session_id)
            console.print("[green]Session saved[/green]")

        elif cmd == "/history":
            messages = self.session_manager.get_messages(session_id)
            for msg in messages[-10:]:  # Show last 10
                role_color = "blue" if msg.role == MessageRole.USER else "green"
                console.print(f"[bold {role_color}]{msg.role}:[/bold {role_color}]")
                console.print(format_response(msg))
                console.print()

        elif cmd == "/model" and len(parts) > 1:
            model = parts[1]
            console.print(f"[green]Model changed to: {model}[/green]")

        elif cmd == "/system" and len(parts) > 1:
            " ".join(parts[1:])
            console.print("[green]System prompt set[/green]")

        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")


def main():
    """Main entry point for Fire CLI."""
    fire.Fire(ClaudeCLI)
