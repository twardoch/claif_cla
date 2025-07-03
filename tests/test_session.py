"""Tests for session management functionality."""

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import aiofiles
import pytest
from claif.common import Message, MessageRole

from claif_cla.session import Session, SessionManager


@pytest.mark.unit
class TestSession:
    """Test Session class functionality."""

    def test_session_creation(self):
        """Test creating a new session."""
        session_id = "test-123"
        session = Session(session_id)

        assert session.id == session_id
        assert isinstance(session.created_at, datetime)
        assert session.created_at.tzinfo == timezone.utc
        assert session.messages == []
        assert session.metadata == {}
        assert session.checkpoints == []

    def test_session_creation_with_timestamp(self):
        """Test creating session with specific timestamp."""
        session_id = "test-123"
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        session = Session(session_id, created_at=timestamp)

        assert session.created_at == timestamp

    def test_add_message(self):
        """Test adding messages to session."""
        session = Session("test-123")
        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there!")

        session.add_message(msg1)
        session.add_message(msg2)

        assert len(session.messages) == 2
        assert session.messages[0] == msg1
        assert session.messages[1] == msg2

    def test_create_checkpoint(self):
        """Test creating checkpoints."""
        session = Session("test-123")

        # Add some messages
        session.add_message(Message(role=MessageRole.USER, content="1"))
        session.add_message(Message(role=MessageRole.ASSISTANT, content="2"))

        checkpoint1 = session.create_checkpoint()
        assert checkpoint1 == 2
        assert checkpoint1 in session.checkpoints

        # Add more messages
        session.add_message(Message(role=MessageRole.USER, content="3"))

        checkpoint2 = session.create_checkpoint()
        assert checkpoint2 == 3
        assert len(session.checkpoints) == 2

    def test_restore_checkpoint(self):
        """Test restoring to a checkpoint."""
        session = Session("test-123")

        # Add messages and create checkpoint
        session.add_message(Message(role=MessageRole.USER, content="1"))
        session.add_message(Message(role=MessageRole.ASSISTANT, content="2"))
        checkpoint = session.create_checkpoint()

        # Add more messages after checkpoint
        session.add_message(Message(role=MessageRole.USER, content="3"))
        session.add_message(Message(role=MessageRole.ASSISTANT, content="4"))

        assert len(session.messages) == 4

        # Restore to checkpoint
        session.restore_checkpoint(checkpoint)
        assert len(session.messages) == 2
        assert len(session.messages[-1].content) == 1
        assert session.messages[-1].content[0].text == "2"

    def test_restore_invalid_checkpoint(self):
        """Test restoring to invalid checkpoint raises error."""
        session = Session("test-123")

        with pytest.raises(ValueError, match="Checkpoint 99 not found"):
            session.restore_checkpoint(99)

    def test_to_dict_simple_messages(self):
        """Test converting session to dict with simple string messages."""
        session = Session("test-123")
        session.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        session.add_message(Message(role=MessageRole.USER, content="Hello"))
        session.add_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))
        session.metadata["key"] = "value"
        session.checkpoints = [1, 2]

        data = session.to_dict()

        assert data["id"] == "test-123"
        assert data["created_at"] == "2024-01-01T12:00:00Z"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"][0]["text"] == "Hello"
        assert data["messages"][1]["content"][0]["text"] == "Hi!"
        assert data["metadata"] == {"key": "value"}
        assert data["checkpoints"] == [1, 2]

    def test_to_dict_text_block_messages(self):
        """Test converting session to dict with TextBlock messages."""
        session = Session("test-123")

        # Create message with text blocks
        block1 = Mock(text="Part 1")
        block2 = Mock(text="Part 2")
        msg = Message(role=MessageRole.ASSISTANT, content=[block1, block2])
        session.add_message(msg)

        data = session.to_dict()

        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "assistant"
        assert data["messages"][0]["content"] == [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]

    def test_from_dict(self):
        """Test creating session from dict."""
        data = {
            "id": "test-123",
            "created_at": "2024-01-01T12:00:00+00:00",
            "messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}],
            "metadata": {"key": "value"},
            "checkpoints": [1, 2],
        }

        session = Session.from_dict(data)

        assert session.id == "test-123"
        assert session.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert len(session.messages) == 2
        assert session.messages[0].role == MessageRole.USER
        assert len(session.messages[0].content) == 1
        assert session.messages[0].content[0].text == "Hello"
        assert session.metadata == {"key": "value"}
        assert session.checkpoints == [1, 2]

    def test_from_dict_with_text_blocks(self):
        """Test creating session from dict with text block content."""
        data = {
            "id": "test-123",
            "created_at": "2024-01-01T12:00:00+00:00",
            "messages": [
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Part 1"},
                        {"type": "text", "text": "Part 2"},
                    ],
                }
            ],
            "metadata": {},
            "checkpoints": [],
        }

        with patch("claif.common.types.TextBlock") as mock_text_block:
            Session.from_dict(data)

            # Verify TextBlock was created
            assert mock_text_block.call_count == 2
            mock_text_block.assert_any_call(text="Part 1")
            mock_text_block.assert_any_call(text="Part 2")


@pytest.mark.asyncio
@pytest.mark.unit
class TestSessionManager:
    """Test SessionManager functionality."""

    async def test_session_manager_init(self, temp_dir):
        """Test SessionManager initialization."""
        session_dir = temp_dir / "sessions"
        manager = SessionManager(str(session_dir))
        await manager.initialize()

        assert manager.session_dir == session_dir
        assert session_dir.exists()
        assert manager.active_sessions == {}

    async def test_session_manager_default_dir(self, temp_dir):
        """Test SessionManager with default directory."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = temp_dir
            manager = SessionManager()
            await manager.initialize()

            assert manager.session_dir == temp_dir / ".claif" / "sessions"

    async def test_create_session(self, mock_session_dir):
        """Test creating a new session."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        session_id = await manager.create_session()

        assert session_id in manager.active_sessions
        assert (mock_session_dir / f"{session_id}.json").exists()

    async def test_create_session_with_id(self, mock_session_dir):
        """Test creating session with specific ID."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        session_id = await manager.create_session("custom-id")

        assert session_id == "custom-id"
        assert "custom-id" in manager.active_sessions

    async def test_load_session_from_disk(self, mock_session_file):
        """Test loading session from disk."""
        session_file, session_id = mock_session_file
        manager = SessionManager(str(session_file.parent))
        await manager.initialize()

        session = await manager.load_session(session_id)

        assert session.id == session_id
        assert len(session.messages) == 2
        assert session_id in manager.active_sessions

    async def test_load_active_session(self, mock_session_dir):
        """Test loading already active session."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        # Load same session again and assert it's the same object
        loaded_session = await manager.load_session(session_id)
        assert loaded_session is manager.active_sessions[session_id]

    async def test_load_nonexistent_session(self, mock_session_dir):
        """Test loading non-existent session raises error."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        with pytest.raises(ValueError, match="Session nonexistent not found"):
            await manager.load_session("nonexistent")

    async def test_save_session(self, mock_session_dir):
        """Test saving session to disk."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        # Add a message
        msg = Message(role=MessageRole.USER, content="Test")
        await manager.add_message(session_id, msg)

        # Verify file contains the message
        session_file = mock_session_dir / f"{session_id}.json"
        async with aiofiles.open(session_file) as f:
            data = json.loads(await f.read())

        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"][0]["text"] == "Test"

    async def test_save_inactive_session(self, mock_session_dir):
        """Test saving inactive session raises error."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        with pytest.raises(ValueError, match="Session inactive not active"):
            await manager.save_session("inactive")

    async def test_delete_session(self, mock_session_file):
        """Test deleting a session."""
        session_file, session_id = mock_session_file
        manager = SessionManager(str(session_file.parent))
        await manager.initialize()

        # Load then delete
        await manager.load_session(session_id)
        await manager.delete_session(session_id)

        assert not session_file.exists()
        assert session_id not in manager.active_sessions

    async def test_list_sessions(self, mock_session_dir):
        """Test listing all sessions."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        # Create multiple sessions
        ids = [await manager.create_session() for _ in range(3)]

        sessions = await manager.list_sessions()

        assert len(sessions) == 3
        assert all(sid in sessions for sid in ids)
        assert sessions == sorted(sessions)  # Should be sorted

    async def test_get_session_info(self, mock_session_file):
        """Test getting session information."""
        session_file, session_id = mock_session_file
        manager = SessionManager(str(session_file.parent))
        await manager.initialize()

        info = await manager.get_session_info(session_id)

        assert info["id"] == session_id
        assert info["created_at"] == "2024-01-01T00:00:00Z"
        assert info["message_count"] == 2
        assert info["has_checkpoints"] is False

    async def test_get_session_info_error(self, mock_session_dir):
        """Test getting info for non-existent session."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        info = await manager.get_session_info("nonexistent")

        assert info["id"] == "nonexistent"
        assert "error" in info

    async def test_add_and_get_messages(self, mock_session_dir):
        """Test adding and retrieving messages."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.ASSISTANT, content="Hi!")

        await manager.add_message(session_id, msg1)
        await manager.add_message(session_id, msg2)

        messages = await manager.get_messages(session_id)

        assert len(messages) == 2
        assert messages[0].content[0].text == "Hello"
        assert messages[1].content[0].text == "Hi!"

    async def test_branch_session(self, mock_session_dir):
        """Test branching a session."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        # Add messages
        for i in range(4):
            msg = Message(role=MessageRole.USER, content=f"Message {i}")
            await manager.add_message(session_id, msg)

        # Branch at message 2
        new_id = await manager.branch_session(session_id, at_point=2)

        assert new_id != session_id
        assert new_id in manager.active_sessions

        # Check branched session
        new_session = manager.active_sessions[new_id]
        assert len(new_session.messages) == 2
        assert new_session.metadata["branched_from"] == session_id
        assert new_session.metadata["branch_point"] == 2

    async def test_branch_session_negative_index(self, mock_session_dir):
        """Test branching with negative index."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        # Add 4 messages
        for i in range(4):
            msg = Message(role=MessageRole.USER, content=f"Message {i}")
            await manager.add_message(session_id, msg)

        # Branch at -1 (last message)
        new_id = await manager.branch_session(session_id, at_point=-1)

        new_session = manager.active_sessions[new_id]
        assert len(new_session.messages) == 4  # All messages

    async def test_merge_sessions_append(self, mock_session_dir):
        """Test merging sessions with append strategy."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        # Create two sessions with messages
        target_id = await manager.create_session()
        await manager.add_message(target_id, Message(role=MessageRole.USER, content="Target 1"))

        source_id = await manager.create_session()
        await manager.add_message(source_id, Message(role=MessageRole.USER, content="Source 1"))

        # Merge
        await manager.merge_sessions(target_id, source_id, strategy="append")

        messages = await manager.get_messages(target_id)
        assert len(messages) == 2
        assert messages[0].content[0].text == "Target 1"
        assert messages[1].content[0].text == "Source 1"

    async def test_merge_sessions_interleave(self, mock_session_dir):
        """Test merging sessions with interleave strategy."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()

        # Create two sessions
        target_id = await manager.create_session()
        await manager.add_message(target_id, Message(role=MessageRole.USER, content="T1"))
        await manager.add_message(target_id, Message(role=MessageRole.USER, content="T2"))

        source_id = await manager.create_session()
        await manager.add_message(source_id, Message(role=MessageRole.USER, content="S1"))
        await manager.add_message(source_id, Message(role=MessageRole.USER, content="S2"))

        # Merge with interleave
        await manager.merge_sessions(target_id, source_id, strategy="interleave")

        messages = await manager.get_messages(target_id)
        assert len(messages) == 4
        assert [m.content[0].text for m in messages] == ["T1", "S1", "T2", "S2"]

    async def test_merge_invalid_strategy(self, mock_session_dir):
        """Test merge with invalid strategy raises error."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        target_id = await manager.create_session()
        source_id = await manager.create_session()

        with pytest.raises(ValueError, match="Unknown merge strategy: invalid"):
            await manager.merge_sessions(target_id, source_id, strategy="invalid")

    async def test_export_session_markdown(self, mock_session_dir):
        """Test exporting session as markdown."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        await manager.add_message(session_id, Message(role=MessageRole.USER, content="Hello"))
        await manager.add_message(session_id, Message(role=MessageRole.ASSISTANT, content="Hi there!"))

        export = await manager.export_session(session_id, export_format="markdown")

        assert "**user**:" in export
        assert "Hello" in export
        assert "**assistant**:" in export
        assert "Hi there!" in export

    async def test_export_session_json(self, mock_session_dir):
        """Test exporting session as JSON."""
        manager = SessionManager(str(mock_session_dir))
        await manager.initialize()
        session_id = await manager.create_session()

        await manager.add_message(session_id, Message(role=MessageRole.USER, content="Hello"))

        export = await manager.export_session(session_id, export_format="json")

        data = json.loads(export)
        assert len(data) == 1
        assert data[0]["role"] == "user"
        assert data[0]["content"][0]["text"] == "Hello"

    async def test_from_template(self):
        """Test creating session from template."""
        manager = await SessionManager.from_template("test-id", "code_review")
        session = manager.active_sessions.get("test-id")

        assert session is not None
        assert session.id == "test-id"
        assert session.metadata["template"] == "code_review"
        assert session.metadata["system_prompt"] == SessionManager.TEMPLATES["code_review"]["system"]
        assert len(session.messages) == 1
        assert session.messages[0].role == MessageRole.SYSTEM

    async def test_from_template_invalid(self):
        """Test creating session from invalid template."""
        with pytest.raises(ValueError, match="Unknown template: invalid"):
            await SessionManager.from_template("test-id", "invalid")

    def test_templates_defined(self):
        """Test that templates are properly defined."""
        assert "code_review" in SessionManager.TEMPLATES
        assert "debugging" in SessionManager.TEMPLATES
        assert "architecture" in SessionManager.TEMPLATES
        assert "testing" in SessionManager.TEMPLATES

        # Each template should have required fields
        for _name, template in SessionManager.TEMPLATES.items():
            assert "system" in template
            assert "initial_messages" in template
