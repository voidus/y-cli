import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from .models import Chat, Message

class ChatRepository:
    def __init__(self, data_file: str):
        self.data_file = os.path.expanduser(data_file)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the data file exists"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'a', encoding="utf-8") as f:
                pass

    def _read_chats(self) -> List[Chat]:
        """Read all chats from the JSONL file"""
        chats = []
        if os.path.getsize(self.data_file) > 0:
            with open(self.data_file, 'r', encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        chat_dict = json.loads(line)
                        chats.append(Chat.from_dict(chat_dict))
        return chats

    def _write_chats(self, chats: List[Chat]) -> None:
        """Write all chats to the JSONL file"""
        with open(self.data_file, 'w', encoding="utf-8") as f:
            for chat in chats:
                json.dump(chat.to_dict(), f, ensure_ascii=False)
                f.write('\n')

    def list_chats(self, keyword: Optional[str] = None, model: Optional[str] = None,
                   provider: Optional[str] = None, limit: int = 10) -> List[Chat]:
        """List chats with optional filtering

        Args:
            keyword: Optional text to filter messages by content
            model: Optional model name to filter by
            provider: Optional provider name to filter by
            limit: Maximum number of chats to return (default: 10)
        """
        chats = self._read_chats()

        # Sort by create_time in descending order
        chats.sort(key=lambda x: x.create_time, reverse=True)

        # Apply filters if any are specified
        if any([keyword, model, provider]):
            filtered_chats = []
            for chat in chats:
                # Check each message in the chat
                for msg in chat.messages:
                    matches = True
                    
                    # Apply keyword filter if specified
                    if keyword:
                        keyword_lower = keyword.lower()
                        content_matches = False
                        if isinstance(msg.content, str):
                            if keyword_lower in msg.content.lower():
                                content_matches = True
                        else:  # content is a list of parts
                            for part in msg.content:
                                if isinstance(part, dict) and 'text' in part:
                                    if keyword_lower in part['text'].lower():
                                        content_matches = True
                                        break
                        if not content_matches:
                            matches = False
                            continue
                    
                    # Apply model filter if specified
                    if model and (not msg.model or model.lower() not in msg.model.lower()):
                        matches = False
                        continue
                    
                    # Apply provider filter if specified
                    if provider and (not msg.provider or provider.lower() not in msg.provider.lower()):
                        matches = False
                        continue
                    
                    # If all specified filters match, add the chat and break
                    if matches:
                        filtered_chats.append(chat)
                        break
                
                if len(filtered_chats) >= limit:
                    break
            
            chats = filtered_chats

        return chats[:limit]

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a specific chat by ID"""
        chats = self._read_chats()
        return next((chat for chat in chats if chat.id == chat_id), None)

    def add_chat(self, chat: Chat) -> Chat:
        """Add a new chat"""
        chats = self._read_chats()
        chats.append(chat)
        self._write_chats(chats)
        return chat

    def update_chat(self, chat: Chat) -> Chat:
        """Update an existing chat"""
        chats = self._read_chats()
        for i, existing_chat in enumerate(chats):
            if existing_chat.id == chat.id:
                chats[i] = chat
                self._write_chats(chats)
                return chat
        raise ValueError(f"Chat with id {chat.id} not found")

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by ID"""
        chats = self._read_chats()
        initial_length = len(chats)
        chats = [chat for chat in chats if chat.id != chat_id]
        if len(chats) < initial_length:
            self._write_chats(chats)
            return True
        return False
