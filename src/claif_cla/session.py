# this_file: claif_cla/src/claif_cla/session.py
"""Session management for Claude conversations."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Union
import copy

import aiofiles
from claif.common import Message, MessageRole, TextBlock, ToolUseBlock, ToolResultBlock
from loguru import logger


class Session:
    """
    Represents a single conversation session with Claude.

    A session stores a history of messages, metadata, and optional checkpoints
    for branching or restoring conversation states.
    """

    def __init__(self, session_id: str, created_at: Optional[datetime] = None) -> None:
        """
        Initializes a new conversation session.

        Args:
            session_id: A unique identifier for the session.
            created_at: Optional. The datetime when the session was created. Defaults to now (UTC).
        """
        self.id: str = session_id
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {}
        self.checkpoints: List[int] = []

    def add_message(self, message: Message) -> None:
        """
        Adds a new message to the session's conversation history.

        Args:
            message: The `Message` object to add.
        """
        self.messages.append(message)

    def create_checkpoint(self) -> int:
        """
        Creates a checkpoint at the current message count.

        A checkpoint allows restoring the session to this specific point later.

        Returns:
            The index (message count) at which the checkpoint was created.
        """
        checkpoint: int = len(self.messages)
        self.checkpoints.append(checkpoint)
        logger.debug(f"Checkpoint created at message {checkpoint} for session {self.id}")
        return checkpoint

    def restore_checkpoint(self, checkpoint: int) -> None:
        """
        Restores the session to a previously saved checkpoint.

        This truncates the message history to the state at the specified checkpoint.

        Args:
            checkpoint: The message index of the checkpoint to restore to.

        Raises:
            ValueError: If the specified checkpoint does not exist.
        """
        if checkpoint in self.checkpoints:
            self.messages = self.messages[:checkpoint]
            logger.info(f"Session {self.id} restored to checkpoint {checkpoint}")
        else:
            msg = f"Checkpoint {checkpoint} not found in session {self.id}"
            logger.error(msg)
            raise ValueError(msg)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Session object to a dictionary for serialization.

        This method serializes the session's data, including its messages,
        metadata, and checkpoints, into a dictionary format suitable for JSON
        storage. It specifically handles the serialization of `Message` objects,
        converting their `content` attribute (which can be a string or a list
        of `ContentBlock` instances) into a serializable representation.
        Nested `ContentBlock` types like `ToolUseBlock` and `ToolResultBlock`
        are also converted to their dictionary representations.

        Returns:
            A dictionary representation of the session.
        """
        serialized_messages: List[Dict[str, Any]] = []
        for msg in self.messages:
            serialized_content: Union[str, List[Dict[str, Any]]]
            if isinstance(msg.content, str):
                serialized_content = msg.content
            else:
                # Handle list of ContentBlock types
                blocks_data: List[Dict[str, Any]] = []
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        blocks_data.append({"type": "text", "text": block.text})
                    elif isinstance(block, ToolUseBlock):
                        blocks_data.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                    elif isinstance(block, ToolResultBlock):
                        # Recursively serialize content within ToolResultBlock
                        tool_result_content_data: Union[str, List[Dict[str, Any]]]
                        if isinstance(block.content, list):
                            nested_blocks_data: List[Dict[str, Any]] = []
                            for nested_block in block.content:
                                if isinstance(nested_block, TextBlock):
                                    nested_blocks_data.append({"type": "text", "text": nested_block.text})
                                else:
                                    # Fallback for other unexpected nested block types
                                    nested_blocks_data.append({"type": "unknown", "data": str(nested_block)})
                            tool_result_content_data = nested_blocks_data
                        else:
                            tool_result_content_data = str(block.content)

                        blocks_data.append({"type": "tool_result", "tool_use_id": block.tool_use_id, "content": tool_result_content_data, "is_error": block.is_error})
                    else:
                        # Fallback for any other unexpected ContentBlock types
                        blocks_data.append({"type": "unknown", "data": str(block)})
                serialized_content = blocks_data

            serialized_messages.append({"role": msg.role.value, "content": serialized_content})

        return {
            "id": self.id,
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
            "messages": serialized_messages,
            "metadata": self.metadata,
            "checkpoints": self.checkpoints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """
        Creates a Session object from a dictionary representation.

        This class method deserializes a dictionary (typically loaded from JSON)
        back into a `Session` object. It reconstructs `Message` objects and their
        `content` (including nested `ContentBlock` types like `TextBlock`,
        `ToolUseBlock`, and `ToolResultBlock`) from their dictionary representations.

        Args:
            data: A dictionary containing the serialized session data.

        Returns:
            A `Session` object reconstructed from the provided dictionary.
        """
        created_at_str: str = data["created_at"]
        # Handle 'Z' suffix for UTC timezone
        if created_at_str.endswith("Z"):
            created_at_str = created_at_str[:-1] + "+00:00"
        session = cls(
            session_id=data["id"],
            created_at=datetime.fromisoformat(created_at_str),
        )

        for msg_data in data.get("messages", []):
            deserialized_content: Union[str, List[Union[TextBlock, ToolUseBlock, ToolResultBlock]]]
            content_data = msg_data["content"]

            if isinstance(content_data, str):
                deserialized_content = content_data
            else:
                # Handle list of content blocks
                deserialized_blocks: List[Union[TextBlock, ToolUseBlock, ToolResultBlock]] = []
                for block_data in content_data:
                    block_type = block_data.get("type")
                    if block_type == "text":
                        deserialized_blocks.append(TextBlock(text=block_data.get("text", "")))
                    elif block_type == "tool_use":
                        deserialized_blocks.append(ToolUseBlock(id=block_data.get("id", ""), name=block_data.get("name", ""), input=block_data.get("input", {})))
                    elif block_type == "tool_result":
                        # Recursively deserialize content within ToolResultBlock
                        tr_content_data = block_data.get("content")
                        deserialized_tr_content: Union[str, List[TextBlock]]
                        if isinstance(tr_content_data, list):
                            nested_deserialized_blocks: List[TextBlock] = []
                            for nested_block_data in tr_content_data:
                                if nested_block_data.get("type") == "text":
                                    nested_deserialized_blocks.append(TextBlock(text=nested_block_data.get("text", "")))
                                else:
                                    # Fallback for other unexpected nested block types
                                    nested_deserialized_blocks.append(TextBlock(text=str(nested_block_data)))
                            deserialized_tr_content = nested_deserialized_blocks
                        else:
                            deserialized_tr_content = str(tr_content_data)

                        deserialized_blocks.append(ToolResultBlock(tool_use_id=block_data.get("tool_use_id", ""), content=deserialized_tr_content, is_error=block_data.get("is_error", False)))
                    else:
                        # Fallback for any other unexpected ContentBlock types
                        deserialized_blocks.append(TextBlock(text=str(block_data)))
                deserialized_content = deserialized_blocks

            message = Message(
                role=MessageRole(msg_data["role"]),
                content=deserialized_content,
            )
            session.messages.append(message)

        session.metadata = data.get("metadata", {})
        session.checkpoints = data.get("checkpoints", [])

        return session


class SessionManager:
    """
    Manages the lifecycle and persistence of conversation sessions.

    This class handles creating, loading, saving, deleting, listing, and
    manipulating sessions (branching, merging) to/from disk.
    """

    TEMPLATES: ClassVar[Dict[str, Any]] = {
        "code_review": {
            "system": (
                "You are a code reviewer. Analyze the provided code for bugs, performance issues, and best practices."
            ),
            "initial_messages": [
                Message(
                    role=MessageRole.SYSTEM,
                    content="Ready to review code. Please provide the code you'd like me to analyze.",
                ),
            ],
        },
        "debugging": {
            "system": "You are a debugging assistant. Help identify and fix issues in the provided code.",
            "initial_messages": [
                Message(
                    role=MessageRole.SYSTEM,
                    content="Ready to help debug. Please describe the issue and provide relevant code.",
                ),
            ],
        },
        "architecture": {
            "system": "You are a software architect. Help design and improve system architectures.",
            "initial_messages": [
                Message(
                    role=MessageRole.SYSTEM,
                    content="Ready to discuss architecture. What system would you like to design or improve?",
                ),
            ],
        },
        "testing": {
            "system": "You are a testing expert. Help write comprehensive tests and improve test coverage.",
            "initial_messages": [
                Message(
                    role=MessageRole.SYSTEM,
                    content="Ready to help with testing. What code would you like to test?",
                ),
            ],
        },
    }

    def __init__(self, session_dir: Optional[str] = None) -> None:
        """
        Initializes the SessionManager.

        Args:
            session_dir: Optional. The directory where session files will be stored.
                         Defaults to `~/.claif/sessions`.
        """
        if session_dir:
            self.session_dir: Path = Path(session_dir)
        else:
            self.session_dir = Path.home() / ".claif" / "sessions"
        self.active_sessions: Dict[str, Session] = {}

    async def initialize(self) -> None:
        """
        Ensures the session directory exists.

        Creates the directory and any necessary parent directories if they don't exist.
        """
        if not await asyncio.to_thread(self.session_dir.exists):
            await asyncio.to_thread(self.session_dir.mkdir, parents=True, exist_ok=True)

    async def create_session(self, session_id: Optional[str] = None, template_name: Optional[str] = None) -> str:
        """
        Creates a new conversation session.

        If `session_id` is not provided, a new UUID is generated. If `template_name`
        is provided, the session is initialized with messages from the specified template.

        Args:
            session_id: Optional. A unique identifier for the new session.
            template_name: Optional. The name of a predefined template to use for the session.

        Returns:
            The ID of the newly created session.

        Raises:
            ValueError: If an unknown template name is provided.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        session = Session(session_id)

        if template_name:
            if template_name not in self.TEMPLATES:
                msg = f"Unknown template: {template_name}"
                logger.error(msg)
                raise ValueError(msg)
            
            template = self.TEMPLATES[template_name]
            session.metadata["template"] = template_name
            session.metadata["system_prompt"] = template.get("system", "")

            import copy
            for msg_data in template.get("initial_messages", []):
                # Deepcopy the message data to ensure that modifications to the session's messages
                # do not affect the original template messages.
                msg_data_copy = copy.deepcopy(msg_data)
                
                if isinstance(msg_data_copy, Message):
                    session.add_message(msg_data_copy)
                else:
                    # Attempt to convert dict to Message, assuming basic structure
                    try:
                        role = MessageRole(msg_data_copy.get("role", "user"))
                        content = msg_data_copy.get("content", "")
                        if isinstance(content, list):
                            # Assuming content list contains dicts that can be converted to TextBlock
                            content = [TextBlock(text=b.get("text", "")) for b in content if isinstance(b, dict)]
                        session.add_message(Message(role=role, content=content))
                    except Exception as e:
                        logger.warning(f"Could not convert template message {msg_data_copy} to Message object: {e}")

        self.active_sessions[session_id] = session
        await self.save_session(session_id)

        logger.info(f"Created session: {session_id}" + (f" from template {template_name}" if template_name else ""))
        return session_id

    async def load_session(self, session_id: str) -> Session:
        """
        Loads a session from disk into the active sessions cache.

        Args:
            session_id: The ID of the session to load.

        Returns:
            The loaded `Session` object.

        Raises:
            ValueError: If the session file does not exist.
        """
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        session_file: Path = self.session_dir / f"{session_id}.json"
        if not await asyncio.to_thread(session_file.exists):
            msg = f"Session file for {session_id} not found at {session_file}"
            logger.error(msg)
            raise ValueError(msg)

        async with aiofiles.open(session_file, "r") as f:
            data: Dict[str, Any] = json.loads(await f.read())

        session: Session = Session.from_dict(data)
        self.active_sessions[session_id] = session
        logger.debug(f"Loaded session: {session_id}")
        return session

    async def save_session(self, session_id: str) -> None:
        """
        Saves an active session to disk.

        Args:
            session_id: The ID of the session to save.

        Raises:
            ValueError: If the session is not currently active.
        """
        if session_id not in self.active_sessions:
            msg = f"Session {session_id} is not active and cannot be saved."
            logger.error(msg)
            raise ValueError(msg)

        session: Session = self.active_sessions[session_id]
        session_file: Path = self.session_dir / f"{session_id}.json"

        async with aiofiles.open(session_file, "w") as f:
            await f.write(json.dumps(session.to_dict(), indent=2))

        logger.debug(f"Saved session: {session_id} to {session_file}")

    async def delete_session(self, session_id: str) -> None:
        """
        Deletes a session from disk and removes it from active sessions.

        Args:
            session_id: The ID of the session to delete.
        """
        session_file: Path = self.session_dir / f"{session_id}.json"
        if await asyncio.to_thread(session_file.exists):
            await asyncio.to_thread(session_file.unlink)
            logger.debug(f"Deleted session file: {session_file}")

        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Removed session {session_id} from active sessions.")

        logger.info(f"Session {session_id} deleted.")

    async def list_sessions(self) -> List[str]:
        """
        Lists the IDs of all available sessions on disk.

        Returns:
            A sorted list of session IDs.
        """
        sessions: List[str] = []
        # Use asyncio.to_thread for blocking I/O operations like glob.
        session_files: List[Path] = await asyncio.to_thread(list, self.session_dir.glob("*.json"))
        for session_file in session_files:
            session_id: str = session_file.stem
            sessions.append(session_id)
        return sorted(sessions)

    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves summary information about a specific session.

        Args:
            session_id: The ID of the session to get information for.

        Returns:
            A dictionary containing session ID, creation timestamp, message count,
            and checkpoint status. Includes an 'error' key if the session cannot be loaded.
        """
        try:
            session: Session = await self.load_session(session_id)
            return {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "message_count": len(session.messages),
                "has_checkpoints": len(session.checkpoints) > 0,
            }
        except Exception as e:
            logger.warning(f"Failed to get info for session {session_id}: {e}")
            return {"id": session_id, "error": str(e)}

    async def add_message(self, session_id: str, message: Message) -> None:
        """
        Adds a message to a specified session and saves the session.

        Args:
            session_id: The ID of the session to add the message to.
            message: The `Message` object to add.
        """
        session: Session = await self.load_session(session_id)
        session.add_message(message)
        await self.save_session(session_id)
        logger.debug(f"Added message to session {session_id}")

    async def get_messages(self, session_id: str) -> List[Message]:
        """
        Retrieves all messages from a specified session.

        Args:
            session_id: The ID of the session to retrieve messages from.

        Returns:
            A list of `Message` objects from the session.
        """
        session: Session = await self.load_session(session_id)
        return session.messages

    async def branch_session(self, session_id: str, at_point: int = -1) -> str:
        """
        Creates a new session by branching from an existing session's history.

        The new session will contain messages from the parent session up to
        the specified `at_point`.

        Args:
            session_id: The ID of the parent session to branch from.
            at_point: The message index (exclusive) at which to branch. Defaults to -1
                      (the entire history of the parent session).

        Returns:
            The ID of the newly created branched session.
        """
        parent_session: Session = await self.load_session(session_id)

        new_id: str = str(uuid.uuid4())
        new_session: Session = Session(new_id)

        # Determine the actual branch point.
        effective_at_point: int = at_point if at_point >= 0 else len(parent_session.messages) + at_point + 1
        effective_at_point = max(0, min(effective_at_point, len(parent_session.messages)))

        # Copy messages up to the branch point.
        new_session.messages = parent_session.messages[:effective_at_point].copy()
        new_session.metadata["branched_from"] = session_id
        new_session.metadata["branch_point"] = effective_at_point

        self.active_sessions[new_id] = new_session
        await self.save_session(new_id)

        logger.info(f"Branched session {session_id} -> {new_id} at point {effective_at_point}")
        return new_id

    async def merge_sessions(self, target_id: str, source_id: str, strategy: str = "append") -> None:
        """
        Merges messages from a source session into a target session.

        Args:
            target_id: The ID of the session to merge into.
            source_id: The ID of the session to merge from.
            strategy: The merge strategy. Currently supports "append" (default)
                      and "interleave".

        Raises:
            ValueError: If an unknown merge strategy is provided.
        """
        target_session: Session = await self.load_session(target_id)
        source_session: Session = await self.load_session(source_id)

        if strategy == "append":
            target_session.messages.extend(source_session.messages)
            logger.debug(f"Appended session {source_id} messages to {target_id}")
        elif strategy == "interleave":
            # Interleave messages by alternating from source and target.
            # This is a simplified interleave and doesn't consider timestamps.
            merged_messages: List[Message] = []
            max_len = max(len(target_session.messages), len(source_session.messages))
            for i in range(max_len):
                if i < len(target_session.messages):
                    merged_messages.append(target_session.messages[i])
                if i < len(source_session.messages):
                    merged_messages.append(source_session.messages[i])
            target_session.messages = merged_messages
            logger.debug(f"Interleaved session {source_id} messages into {target_id}")
        else:
            msg = f"Unknown merge strategy: {strategy}"
            logger.error(msg)
            raise ValueError(msg)

        target_session.metadata[f"merged_from_{source_id}"] = datetime.now(timezone.utc).isoformat()
        await self.save_session(target_id)

        logger.info(f"Merged session {source_id} into {target_id} using {strategy} strategy.")

    async def export_session(self, session_id: str, export_format: str = "markdown") -> str:
        """
        Exports a session's conversation history in a specified format.

        Args:
            session_id: The ID of the session to export.
            export_format: The desired output format ('markdown' or 'json').
                           Defaults to 'markdown'.

        Returns:
            A string containing the exported session content.

        Raises:
            ValueError: If an unknown export format is requested.
        """
        session: Session = await self.load_session(session_id)

        if export_format == "json":
            # Export as JSON, converting messages to a serializable dictionary format.
            return json.dumps([self._message_to_dict(m) for m in session.messages], indent=2)
        elif export_format == "markdown":
            # Export as Markdown, formatting each message.
            lines: List[str] = []
            for msg in session.messages:
                lines.append(f"**{msg.role.value.upper()}**:")
                lines.append(self._message_to_str(msg))
                lines.append("") # Add an empty line for separation
            return "\n".join(lines)
        else:
            msg = f"Unknown export format: {export_format}. Supported formats are 'markdown' and 'json'."
            logger.error(msg)
            raise ValueError(msg)

    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
        """
        Converts a `Message` object to a dictionary for serialization.

        Handles serialization of `Message` objects, including their potentially
        complex `content` structure (string or list of `ContentBlock`s).

        Args:
            message: The `Message` object to convert.

        Returns:
            A dictionary representation of the message.
        """
        serialized_content: Union[str, List[Dict[str, Any]]]

        if isinstance(message.content, str):
            serialized_content = message.content
        else:
            # Handle list of ContentBlock types
            blocks_data: List[Dict[str, Any]] = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    blocks_data.append({"type": "text", "text": block.text})
                elif isinstance(block, ToolUseBlock):
                    blocks_data.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
                elif isinstance(block, ToolResultBlock):
                    # Recursively serialize content within ToolResultBlock
                    tool_result_content_data: Union[str, List[Dict[str, Any]]]
                    if isinstance(block.content, list):
                        nested_blocks_data: List[Dict[str, Any]] = []
                        for nested_block in block.content:
                            if isinstance(nested_block, TextBlock):
                                nested_blocks_data.append({"type": "text", "text": nested_block.text})
                            else:
                                # Fallback for other unexpected nested block types
                                nested_blocks_data.append({"type": "unknown", "data": str(nested_block)})
                        tool_result_content_data = nested_blocks_data
                    else:
                        tool_result_content_data = str(block.content)

                    blocks_data.append({"type": "tool_result", "tool_use_id": block.tool_use_id, "content": tool_result_content_data, "is_error": block.is_error})
                else:
                    # Fallback for any other unexpected ContentBlock types
                    blocks_data.append({"type": "unknown", "data": str(block)})
            serialized_content = blocks_data

        return {"role": message.role.value, "content": serialized_content}

    def _message_to_str(self, message: Message) -> str:
        """
        Converts a `Message` object's content to a string representation.

        Handles both string content and lists of `ContentBlock`s.

        Args:
            message: The `Message` object to convert.

        Returns:
            A string representation of the message content.
        """
        if isinstance(message.content, str):
            return message.content
        
        # If content is a list of blocks, join their textual representations.
        text_parts: List[str] = []
        for block in message.content:
            if isinstance(block, TextBlock):
                text_parts.append(block.text)
            elif isinstance(block, ToolUseBlock):
                text_parts.append(f"Tool Use: {block.name}({block.input})")
            elif isinstance(block, ToolResultBlock):
                # Handle nested content within ToolResultBlock
                if isinstance(block.content, list):
                    nested_text = ", ".join([b.text for b in block.content if isinstance(b, TextBlock)])
                    text_parts.append(f"Tool Result (ID: {block.tool_use_id}, Error: {block.is_error}): {nested_text}")
                else:
                    text_parts.append(f"Tool Result (ID: {block.tool_use_id}, Error: {block.is_error}): {block.content}")
            else:
                text_parts.append(str(block)) # Fallback for unknown block types
        return "\n".join(text_parts)

    @classmethod
    async def from_template(cls, session_id: str, template_name: str) -> "SessionManager":
        """
        Creates a new `SessionManager` instance and initializes a session from a predefined template.

        This is a class method that acts as a factory for creating a manager
        with a pre-populated session based on a template.

        Args:
            session_id: The ID for the new session.
            template_name: The name of the template to use.

        Returns:
            A new `SessionManager` instance with the template-based session loaded.

        Raises:
            ValueError: If the template name is not found.
        """
        # Create a temporary manager instance to handle session creation and saving.
        # This is a bit awkward as noted in the original code, but necessary if
        # SessionManager is not a singleton and needs to manage its own files.
        manager = cls(session_dir=None) # Use default session_dir
        await manager.initialize()

        # Delegate to the instance method for session creation with template.
        await manager.create_session(session_id=session_id, template_name=template_name)

        return manager
