"""Session management for Claude conversations."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..claif.common import Message, MessageRole, get_logger


logger = get_logger(__name__)


class Session:
    """A conversation session."""
    
    def __init__(self, session_id: str, created_at: Optional[datetime] = None):
        self.id = session_id
        self.created_at = created_at or datetime.now()
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {}
        self.checkpoints: List[int] = []
    
    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
    
    def create_checkpoint(self) -> int:
        """Create a checkpoint at current position."""
        checkpoint = len(self.messages)
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def restore_checkpoint(self, checkpoint: int) -> None:
        """Restore session to a checkpoint."""
        if checkpoint in self.checkpoints:
            self.messages = self.messages[:checkpoint]
        else:
            raise ValueError(f"Checkpoint {checkpoint} not found")
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content if isinstance(msg.content, str) else [
                        {"type": "text", "text": block.text}
                        for block in msg.content
                        if hasattr(block, "text")
                    ],
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
            "checkpoints": self.checkpoints,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create session from dictionary."""
        session = cls(
            session_id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
        
        for msg_data in data.get("messages", []):
            content = msg_data["content"]
            if isinstance(content, list):
                from ..claif.common import TextBlock
                content = [TextBlock(text=block["text"]) for block in content]
            
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=content,
            )
            session.messages.append(message)
        
        session.metadata = data.get("metadata", {})
        session.checkpoints = data.get("checkpoints", [])
        
        return session


class SessionManager:
    """Manage conversation sessions."""
    
    def __init__(self, session_dir: Optional[str] = None):
        if session_dir:
            self.session_dir = Path(session_dir)
        else:
            self.session_dir = Path.home() / ".claif" / "sessions"
        
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.active_sessions: Dict[str, Session] = {}
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(session_id)
        self.active_sessions[session_id] = session
        self.save_session(session_id)
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def load_session(self, session_id: str) -> Session:
        """Load a session from disk."""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        session_file = self.session_dir / f"{session_id}.json"
        if not session_file.exists():
            raise ValueError(f"Session {session_id} not found")
        
        with open(session_file) as f:
            data = json.load(f)
        
        session = Session.from_dict(data)
        self.active_sessions[session_id] = session
        return session
    
    def save_session(self, session_id: str) -> None:
        """Save a session to disk."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not active")
        
        session = self.active_sessions[session_id]
        session_file = self.session_dir / f"{session_id}.json"
        
        with open(session_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
        
        logger.debug(f"Saved session: {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        session_file = self.session_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Deleted session: {session_id}")
    
    def list_sessions(self) -> List[str]:
        """List all available sessions."""
        sessions = []
        for session_file in self.session_dir.glob("*.json"):
            session_id = session_file.stem
            sessions.append(session_id)
        return sorted(sessions)
    
    def get_session_info(self, session_id: str) -> dict:
        """Get session information."""
        try:
            session = self.load_session(session_id)
            return {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "message_count": len(session.messages),
                "has_checkpoints": len(session.checkpoints) > 0,
            }
        except Exception as e:
            logger.warning(f"Failed to load session {session_id}: {e}")
            return {"id": session_id, "error": str(e)}
    
    def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to a session."""
        session = self.load_session(session_id)
        session.add_message(message)
        self.save_session(session_id)
    
    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages from a session."""
        session = self.load_session(session_id)
        return session.messages
    
    def branch_session(self, session_id: str, at_point: int = -1) -> str:
        """Create a new session branching from an existing one."""
        parent = self.load_session(session_id)
        
        # Create new session
        new_id = str(uuid.uuid4())
        new_session = Session(new_id)
        
        # Copy messages up to branch point
        if at_point < 0:
            at_point = len(parent.messages) + at_point + 1
        
        new_session.messages = parent.messages[:at_point].copy()
        new_session.metadata["branched_from"] = session_id
        new_session.metadata["branch_point"] = at_point
        
        self.active_sessions[new_id] = new_session
        self.save_session(new_id)
        
        logger.info(f"Branched session {session_id} -> {new_id} at point {at_point}")
        return new_id
    
    def merge_sessions(self, target_id: str, source_id: str, strategy: str = "append") -> None:
        """Merge two sessions."""
        target = self.load_session(target_id)
        source = self.load_session(source_id)
        
        if strategy == "append":
            target.messages.extend(source.messages)
        elif strategy == "interleave":
            # Interleave messages by timestamp (simplified - just alternate)
            merged = []
            for i in range(max(len(target.messages), len(source.messages))):
                if i < len(target.messages):
                    merged.append(target.messages[i])
                if i < len(source.messages):
                    merged.append(source.messages[i])
            target.messages = merged
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")
        
        target.metadata[f"merged_from_{source_id}"] = datetime.now().isoformat()
        self.save_session(target_id)
        
        logger.info(f"Merged session {source_id} into {target_id} using {strategy}")
    
    def export_session(self, session_id: str, format: str = "markdown") -> str:
        """Export session in various formats."""
        session = self.load_session(session_id)
        
        if format == "json":
            return json.dumps(session.to_dict(), indent=2)
        
        elif format == "markdown":
            lines = [
                f"# Session: {session.id}",
                f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
            ]
            
            for msg in session.messages:
                role = msg.role.value.capitalize()
                lines.append(f"## {role}")
                
                if isinstance(msg.content, str):
                    lines.append(msg.content)
                else:
                    for block in msg.content:
                        if hasattr(block, "text"):
                            lines.append(block.text)
                
                lines.append("")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unknown export format: {format}")


class SessionTemplate:
    """Pre-configured session templates."""
    
    TEMPLATES = {
        "code_review": {
            "system": "You are a code reviewer. Analyze the provided code for bugs, performance issues, and best practices.",
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
    
    @classmethod
    def create_from_template(cls, template_name: str, session_id: Optional[str] = None) -> Session:
        """Create a session from a template."""
        if template_name not in cls.TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = cls.TEMPLATES[template_name]
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(session_id)
        session.metadata["template"] = template_name
        session.metadata["system_prompt"] = template["system"]
        
        for msg in template.get("initial_messages", []):
            session.add_message(msg)
        
        return session