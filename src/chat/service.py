import uuid
from datetime import datetime
from typing import List, Optional, Dict
from .models import Chat, Message
from .repository import ChatRepository
import time

from .util import get_iso8601_timestamp

class ChatService:
    def __init__(self, repository: ChatRepository):
        self.repository = repository

    def _generate_id(self) -> str:
        """Generate a unique chat ID"""
        return uuid.uuid4().hex[:6]

    def _create_timestamp(self) -> str:
        """Create an ISO format timestamp"""
        return get_iso8601_timestamp()

    def list_chats(self, keyword: Optional[str] = None, limit: int = 10) -> List[Chat]:
        """List chats with optional filtering
        
        Args:
            keyword: Optional text to filter messages by content
            limit: Maximum number of chats to return (default: 10)
            
        Returns:
            List of chats filtered by the given criteria, sorted by creation time descending
        """
        return self.repository.list_chats(keyword=keyword, limit=limit)

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a specific chat by ID"""
        return self.repository.get_chat(chat_id)

    def create_chat(self, messages: List[Dict]) -> Chat:
        """Create a new chat with messages"""
        timestamp = self._create_timestamp()
        chat = Chat(
            id=self._generate_id(),
            create_time=timestamp,
            update_time=timestamp,
            messages=[Message(
                role=msg['role'],
                content=msg['content'],
                timestamp=msg.get('timestamp', timestamp)
            ) for msg in messages]
        )
        return self.repository.add_chat(chat)

    def update_chat(self, chat_id: str, messages: List[Dict]) -> Chat:
        """Update an existing chat's messages"""
        chat = self.get_chat(chat_id)
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")
        
        timestamp = self._create_timestamp()
        new_messages = [Message(
            role=msg['role'],
            content=msg['content'],
            timestamp=msg.get('timestamp', timestamp)
        ) for msg in messages]
        
        chat.update_messages(new_messages)
        return self.repository.update_chat(chat)

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by ID"""
        return self.repository.delete_chat(chat_id)

    def add_message(self, chat_id: str, role: str, content: str) -> Chat:
        """Add a new message to an existing chat"""
        chat = self.get_chat(chat_id)
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")
        
        timestamp = self._create_timestamp()
        new_message = Message(role=role, content=content, timestamp=timestamp)
        chat.messages.append(new_message)
        chat.update_time = timestamp
        
        return self.repository.update_chat(chat)
