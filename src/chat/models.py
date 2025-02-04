from dataclasses import dataclass
from typing import List, Dict, Optional, Union

from .util import get_iso8601_timestamp

@dataclass
class Message:
    role: str
    content: str
    timestamp: str
    source: Optional[str] = None
    links: Optional[List[str]] = None
    images: Optional[List[str]] = None
    model: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=data['timestamp'],
            source=data.get('source'),
            links=data.get('links'),
            images=data.get('images'),
            model=data.get('model')
        )
    
    def to_dict(self) -> Dict:
        result = {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }
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
            messages=[Message.from_dict(m) for m in data['messages']]
        )
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'create_time': self.create_time,
            'update_time': self.update_time,
            'messages': [m.to_dict() for m in self.messages]
        }
    
    def update_messages(self, messages: List[Message]) -> None:
        self.messages = messages
        self.update_time = get_iso8601_timestamp()
