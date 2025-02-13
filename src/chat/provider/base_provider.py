from abc import ABC, abstractmethod
from typing import List, Optional
from chat.models import Message

class BaseProvider(ABC):
    @abstractmethod
    async def call_chat_completions(self, messages: List[Message], system_prompt: Optional[str] = None) -> Message:
        """Get a chat response from the provider.
        
        Args:
            messages: List of Message objects
            system_prompt: Optional system prompt to add at the start
            
        Returns:
            Message: The assistant's response message
            
        Raises:
            Exception: If API call fails
        """
        pass
