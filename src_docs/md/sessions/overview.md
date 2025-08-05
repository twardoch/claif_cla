---
# this_file: src_docs/md/sessions/overview.md
title: Chapter 4 - Session Management
description: Persistent conversation handling, session lifecycle, and history management
---

# Chapter 4: Session Management

Session management in claif_cla provides powerful capabilities for maintaining persistent conversations, organizing chat history, and building stateful AI applications.

## Overview

Sessions allow you to:

- **Persist conversations** across multiple interactions
- **Organize chat history** with metadata and templates
- **Export conversations** in multiple formats
- **Resume interactions** from any point
- **Share and collaborate** on conversation threads

## Session Architecture

### Session Structure

```python
@dataclass
class Session:
    id: str                    # Unique session identifier
    messages: List[Message]    # Conversation history
    metadata: Dict[str, Any]   # Custom metadata
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last modification
    template: str | None       # Session template type
    title: str | None          # Human-readable title
```

### Message Format

```python
@dataclass
class Message:
    role: MessageRole          # system, user, assistant
    content: str              # Message content
    timestamp: datetime       # When message was created
    metadata: Dict[str, Any]  # Message-specific metadata
    tokens: int | None        # Token count (if available)
```

## Basic Session Usage

### Creating Sessions

```python
from claif_cla.session import SessionManager

# Initialize session manager
session_mgr = SessionManager()

# Create new session
session_id = session_mgr.create_session(
    title="Code Review Discussion",
    metadata={"project": "my-app", "language": "python"}
)

# Create with template
session_id = session_mgr.create_session(
    template="coding",
    metadata={"language": "python", "framework": "django"}
)
```

### Adding Messages

```python
from claif.common import Message, MessageRole

# Add user message
user_msg = Message(
    role=MessageRole.USER,
    content="Can you review this Python function?",
    metadata={"file": "utils.py"}
)
session_mgr.add_message(session_id, user_msg)

# Add system message
system_msg = Message(
    role=MessageRole.SYSTEM,
    content="You are an expert Python code reviewer."
)
session_mgr.add_message(session_id, system_msg)
```

### Retrieving Sessions

```python
# Get specific session
session = session_mgr.get_session(session_id)

# List all sessions
sessions = session_mgr.list_sessions()

# Filter sessions by metadata
coding_sessions = session_mgr.list_sessions(
    filter_metadata={"template": "coding"}
)

# Search sessions by content
search_results = session_mgr.search_sessions("code review")
```

## Session Templates

### Built-in Templates

claif_cla provides several pre-configured templates:

#### Coding Template
```python
session_id = session_mgr.create_session(
    template="coding",
    metadata={
        "language": "python",
        "framework": "django",
        "task": "debugging"
    }
)
```

#### Analysis Template
```python
session_id = session_mgr.create_session(
    template="analysis",
    metadata={
        "domain": "financial",
        "data_type": "time_series"
    }
)
```

#### Creative Template
```python
session_id = session_mgr.create_session(
    template="creative",
    metadata={
        "genre": "science_fiction",
        "length": "short_story"
    }
)
```

### Custom Templates

```python
# Define custom template
custom_template = {
    "name": "research",
    "system_message": "You are a research assistant specializing in academic literature.",
    "default_metadata": {
        "field": "computer_science",
        "output_format": "academic"
    },
    "suggested_parameters": {
        "temperature": 0.3,
        "max_tokens": 2000
    }
}

# Register template
session_mgr.register_template("research", custom_template)

# Use custom template
session_id = session_mgr.create_session(
    template="research",
    metadata={"topic": "machine_learning", "year": "2024"}
)
```

## Session Operations

### Session Persistence

```python
# Save session to disk
session_mgr.save_session(session_id)

# Load session from disk
session = session_mgr.load_session(session_id)

# Auto-save configuration
session_mgr.configure_autosave(
    enabled=True,
    interval=300  # Save every 5 minutes
)
```

### Session Modification

```python
# Update session metadata
session_mgr.update_metadata(session_id, {
    "status": "completed",
    "rating": 5
})

# Update session title
session_mgr.update_title(session_id, "Completed Code Review")

# Add message with context
session_mgr.add_message(session_id, Message(
    role=MessageRole.ASSISTANT,
    content="The code looks good!",
    metadata={"confidence": 0.95}
))
```

### Message Management

```python
# Get messages with filtering
recent_messages = session_mgr.get_messages(
    session_id,
    limit=10,
    role=MessageRole.USER
)

# Get messages by time range
from datetime import datetime, timedelta
yesterday = datetime.now() - timedelta(days=1)

recent = session_mgr.get_messages(
    session_id,
    since=yesterday
)

# Update message metadata
session_mgr.update_message_metadata(
    session_id, 
    message_index=5,
    metadata={"important": True}
)
```

## Exporting Sessions

### Export Formats

#### Markdown Export
```python
# Export as Markdown
markdown_content = session_mgr.export_session(
    session_id,
    export_format="markdown",
    include_metadata=True,
    include_timestamps=True
)

# Save to file
with open("conversation.md", "w") as f:
    f.write(markdown_content)
```

#### JSON Export
```python
# Export as JSON
json_content = session_mgr.export_session(
    session_id,
    export_format="json",
    pretty_print=True
)

# Save to file
import json
with open("conversation.json", "w") as f:
    json.dump(json.loads(json_content), f, indent=2)
```

#### HTML Export
```python
# Export as HTML
html_content = session_mgr.export_session(
    session_id,
    export_format="html",
    include_css=True,
    theme="default"
)
```

### Custom Export Templates

```python
# Define custom export template
export_template = """
# {{ session.title }}

**Created:** {{ session.created_at }}
**Updated:** {{ session.updated_at }}
**Messages:** {{ session.messages|length }}

{% for message in session.messages %}
## {{ message.role|title }} ({{ message.timestamp }})
{{ message.content }}
{% endfor %}
"""

# Register template
session_mgr.register_export_template("custom", export_template)

# Use custom template
output = session_mgr.export_session(
    session_id,
    export_format="custom"
)
```

## Advanced Session Features

### Session Branching

```python
# Create branch from specific message
branch_id = session_mgr.branch_session(
    session_id,
    from_message_index=10,
    title="Alternative Discussion Path"
)

# Continue in branch
session_mgr.add_message(branch_id, Message(
    role=MessageRole.USER,
    content="Let's try a different approach..."
))
```

### Session Merging

```python
# Merge two sessions
merged_id = session_mgr.merge_sessions(
    primary_session_id=session_id,
    secondary_session_id=branch_id,
    strategy="chronological"  # or "manual", "smart"
)
```

### Session Analytics

```python
# Get session statistics
stats = session_mgr.get_session_stats(session_id)
print(f"Total messages: {stats['message_count']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Average response time: {stats['avg_response_time']}")
print(f"User/Assistant ratio: {stats['user_assistant_ratio']}")

# Get conversation flow analysis
flow = session_mgr.analyze_conversation_flow(session_id)
print(f"Topics discussed: {flow['topics']}")
print(f"Sentiment progression: {flow['sentiment_over_time']}")
```

## CLI Session Management

### Command Overview

```bash
# List sessions
claif-cla session list

# Create session
claif-cla session create --title "My Session" --template coding

# Show session details
claif-cla session show SESSION_ID

# Export session
claif-cla session export SESSION_ID --format markdown --output chat.md

# Delete session
claif-cla session delete SESSION_ID
```

### Advanced CLI Operations

```bash
# Create session with metadata
claif-cla session create \
    --title "Bug Investigation" \
    --template coding \
    --metadata '{"project": "webapp", "priority": "high"}'

# Continue existing session
claif-cla ask "What's the next step?" --session SESSION_ID

# Export with custom options
claif-cla session export SESSION_ID \
    --format json \
    --include-metadata \
    --include-tokens \
    --output detailed_session.json

# Search sessions
claif-cla session search "code review" --limit 10

# Session statistics
claif-cla session stats SESSION_ID
```

## Integration Patterns

### With ClaudeClient

```python
from claif_cla import ClaudeClient
from claif_cla.session import SessionManager

class SessionAwareClient:
    def __init__(self):
        self.client = ClaudeClient()
        self.session_mgr = SessionManager()
    
    def chat_with_session(self, content: str, session_id: str = None):
        # Create session if not provided
        if not session_id:
            session_id = self.session_mgr.create_session()
        
        # Get conversation history
        session = self.session_mgr.get_session(session_id)
        messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in session.messages
        ]
        
        # Add current message
        messages.append({"role": "user", "content": content})
        
        # Get response
        response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages
        )
        
        # Save to session
        self.session_mgr.add_message(session_id, Message(
            role=MessageRole.USER,
            content=content
        ))
        
        assistant_content = response.choices[0].message.content
        self.session_mgr.add_message(session_id, Message(
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            metadata={"tokens": response.usage.total_tokens}
        ))
        
        return assistant_content, session_id

# Usage
client = SessionAwareClient()
response, session_id = client.chat_with_session("Hello!")
response2, _ = client.chat_with_session("How are you?", session_id)
```

### Multi-User Sessions

```python
class MultiUserSessionManager:
    def __init__(self):
        self.session_mgr = SessionManager()
    
    def create_shared_session(self, participants: List[str], title: str):
        """Create session shared among multiple users"""
        session_id = self.session_mgr.create_session(
            title=title,
            metadata={
                "type": "shared",
                "participants": participants,
                "permissions": {user: "read_write" for user in participants}
            }
        )
        return session_id
    
    def add_user_message(self, session_id: str, user: str, content: str):
        """Add message with user attribution"""
        # Check permissions
        session = self.session_mgr.get_session(session_id)
        if user not in session.metadata.get("participants", []):
            raise PermissionError(f"User {user} not authorized")
        
        message = Message(
            role=MessageRole.USER,
            content=content,
            metadata={"user": user}
        )
        self.session_mgr.add_message(session_id, message)
```

## Best Practices

### 1. Session Organization

```python
# Use meaningful titles and metadata
session_id = session_mgr.create_session(
    title=f"Code Review: {filename} - {date}",
    metadata={
        "project": project_name,
        "file": filename,
        "reviewer": reviewer_name,
        "status": "in_progress"
    }
)
```

### 2. Memory Management

```python
# Limit session size for performance
def trim_session_if_needed(session_mgr, session_id, max_messages=100):
    session = session_mgr.get_session(session_id)
    if len(session.messages) > max_messages:
        # Keep recent messages
        recent_messages = session.messages[-max_messages:]
        session_mgr.update_session_messages(session_id, recent_messages)
```

### 3. Error Handling

```python
def safe_session_operation(session_mgr, operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except FileNotFoundError:
        print("Session not found - may have been deleted")
    except PermissionError:
        print("Insufficient permissions for session operation")
    except Exception as e:
        print(f"Session operation failed: {e}")
        return None
```

Sessions provide the foundation for building sophisticated, stateful AI applications with claif_cla! 🗃️