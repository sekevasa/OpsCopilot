"""Conversation memory for copilot."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
import logging

logger = logging.getLogger(__name__)


class Message:
    """A single message in the conversation."""

    def __init__(
        self,
        role: str,  # "user" or "assistant"
        content: str,
        message_id: Optional[UUID] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.message_id = message_id or uuid4()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": str(self.message_id),
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ConversationMemory:
    """In-memory conversation history."""

    def __init__(self, max_history: int = 100):
        """Initialize memory.

        Args:
            max_history: Maximum number of messages to keep
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a message to memory.

        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata

        Returns:
            The added message
        """
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)

        # Trim history if needed
        if len(self.messages) > self.max_history:
            removed = self.messages.pop(0)
            logger.debug(f"Removed oldest message: {removed.message_id}")

        logger.info(f"Added {role} message: {message.message_id}")
        return message

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get message history.

        Args:
            limit: Maximum number of recent messages

        Returns:
            List of message dictionaries
        """
        messages = self.messages
        if limit:
            messages = messages[-limit:]

        return [msg.to_dict() for msg in messages]

    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get last N messages (for context window)."""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

    def set_context(self, key: str, value: Any) -> None:
        """Set context variable.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        logger.debug(f"Set context {key}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context variable.

        Args:
            key: Context key
            default: Default value if not found

        Returns:
            Context value or default
        """
        return self.context.get(key, default)

    def get_all_context(self) -> Dict[str, Any]:
        """Get all context variables."""
        return self.context.copy()

    def clear(self) -> None:
        """Clear all history and context."""
        self.messages.clear()
        self.context.clear()
        logger.info("Conversation memory cleared")

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary."""
        user_messages = sum(1 for m in self.messages if m.role == "user")
        assistant_messages = sum(
            1 for m in self.messages if m.role == "assistant")

        return {
            "total_messages": len(self.messages),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "duration_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
            "context_keys": list(self.context.keys()),
        }


class ConversationStore:
    """Store for multiple conversations (in-memory for now)."""

    def __init__(self):
        """Initialize store."""
        self.conversations: Dict[str, ConversationMemory] = {}

    def create_conversation(self, conversation_id: Optional[str] = None) -> ConversationMemory:
        """Create a new conversation.

        Args:
            conversation_id: Optional conversation ID (defaults to UUID)

        Returns:
            New conversation memory
        """
        if not conversation_id:
            conversation_id = str(uuid4())

        memory = ConversationMemory()
        self.conversations[conversation_id] = memory
        logger.info(f"Created conversation: {conversation_id}")
        return memory

    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation memory or None
        """
        return self.conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False

    def get_all_conversations(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries of all conversations."""
        return {
            cid: memory.get_summary()
            for cid, memory in self.conversations.items()
        }

    def cleanup_old_conversations(self, max_age_seconds: int = 3600) -> int:
        """Clean up conversations older than max age.

        Args:
            max_age_seconds: Maximum age in seconds

        Returns:
            Number of conversations deleted
        """
        now = datetime.utcnow()
        to_delete = [
            cid for cid, memory in self.conversations.items()
            if (now - memory.created_at).total_seconds() > max_age_seconds
        ]

        for cid in to_delete:
            del self.conversations[cid]

        logger.info(f"Cleaned up {len(to_delete)} old conversations")
        return len(to_delete)
