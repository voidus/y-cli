import uuid
from datetime import datetime
import sys
import os
from typing import List, Optional, Dict
from .models import Chat, Message
from .repository import ChatRepository
import time

from .util import get_iso8601_timestamp, get_unix_timestamp
from .config import TMP_DIR

IS_WINDOWS = sys.platform == 'win32'

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
                timestamp=msg.get('timestamp', timestamp),
                unix_timestamp=msg.get('unix_timestamp', get_unix_timestamp())
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
            timestamp=msg.get('timestamp', timestamp),
            unix_timestamp=msg.get('unix_timestamp', get_unix_timestamp())
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
        new_message = Message(
            role=role,
            content=content,
            timestamp=timestamp,
            unix_timestamp=get_unix_timestamp()
        )
        chat.messages.append(new_message)
        chat.update_time = timestamp
        
        return self.repository.update_chat(chat)

    def generate_share_html(self, chat_id: str) -> str:
        """Generate HTML file for sharing a chat using pandoc
        
        Args:
            chat_id: ID of the chat to share
            
        Returns:
            Path to the generated HTML file
        
        Raises:
            ValueError: If chat not found
        """
        chat = self.get_chat(chat_id)
        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")

        # Generate markdown content
        md_content = f"# Chat {chat_id}\n\n"
        for msg in chat.messages:
            if msg.role == 'system':
                continue
            md_content += f"## {msg.role.capitalize()}\n\n{msg.content}\n\n"
            md_content += f"*{msg.timestamp}*\n\n---\n\n"

        # Write markdown to temporary file
        md_file = os.path.join(TMP_DIR, f"{chat_id}.md")
        html_file = os.path.join(TMP_DIR, f"{chat_id}.html")
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Create CSS
        css = '''
<style>
body { max-width: 800px; margin: 0 auto; padding: 2rem; font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; }
h1 { border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
h2 { margin-top: 2rem; color: #2563eb; }
h3 { color: #4b5563; }
sup { color: #6b7280; }
hr { margin: 2rem 0; border: 0; border-top: 1px solid #eee; }
.references { background: #f9fafb; padding: 1rem; border-radius: 0.5rem; }
.images { margin: 1rem 0; }
</style>
'''
        
        # Create temporary CSS file
        css_file = os.path.join(TMP_DIR, f"{chat_id}.css")
        with open(css_file, "w", encoding="utf-8") as f:
            f.write(css)

        # Run pandoc
        pandoc_cmd = 'pandoc'
        if IS_WINDOWS:
            pandoc_cmd = os.path.expanduser('~/AppData/Local/Pandoc/pandoc')

        os.system(f'{pandoc_cmd} "{md_file}" -o "{html_file}" -s --metadata title="{chat_id}" --metadata charset="UTF-8" --include-in-header="{css_file}"')

        # Clean up temporary files
        os.remove(css_file)
        os.remove(md_file)

        return html_file
