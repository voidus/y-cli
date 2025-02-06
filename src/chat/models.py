from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from datetime import datetime
import time

from .util import get_iso8601_timestamp, get_unix_timestamp

@dataclass
class Message:
    role: str
    content: str
    timestamp: str
    unix_timestamp: int
    source: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    model: Optional[str] = None
    id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        # Get or generate unix_timestamp
        unix_timestamp = data.get('unix_timestamp')
        if unix_timestamp is None:
            # Convert ISO timestamp to unix timestamp
            dt = datetime.strptime(data['timestamp'].split('+')[0], "%Y-%m-%dT%H:%M:%S")
            unix_timestamp = int(dt.timestamp() * 1000)
        
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data['timestamp'],
            unix_timestamp=unix_timestamp,
            source=data.get('source'),
            links=data.get('links'),
            images=data.get('images'),
            model=data.get('model'),
            id=data.get('id')
        )
    
    def to_dict(self) -> Dict:
        result = {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp,
            'unix_timestamp': self.unix_timestamp
        }
        if self.id is not None:
            result['id'] = self.id
        if self.source is not None:
            result['source'] = self.source
        if self.links is not None:
            result['links'] = self.links
        if self.images is not None:
            result['images'] = self.images
        if self.model is not None:
            result['model'] = self.model
        return result

@dataclass
class Chat:
    id: str
    create_time: str
    update_time: str
    messages: List[Message]

    @classmethod
    def from_dict(cls, data: Dict) -> 'Chat':
        return cls(
            id=data['id'],
            create_time=data['create_time'],
            update_time=data['update_time'],
            messages=sorted(
                [Message.from_dict(m) for m in data['messages'] if m['role'] != "system"],
                key=lambda x: (x.unix_timestamp)
            )
        )
    
    def to_dict(self) -> Dict:
        return {
            'create_time': self.create_time,
            'id': self.id,
            'update_time': self.update_time,
            'messages': [m.to_dict() for m in self.messages]
        }
    
    def update_messages(self, messages: List[Message]) -> None:
        # Filter out system messages and sort the remaining ones by timestamp
        self.messages = sorted(
            [msg for msg in messages if msg.role != "system"],
            key=lambda x: (x.unix_timestamp)
        )
        self.update_time = get_iso8601_timestamp()
