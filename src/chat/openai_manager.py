from typing import List, Dict, Optional
from openai import OpenAI
from .display_manager import DisplayManager
from .util import get_iso8601_timestamp, get_unix_timestamp

class OpenAIManager:
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """Initialize OpenAI client and settings.

        Args:
            api_key: OpenAI API key
            base_url: Optional custom base URL for API
            model: Model to use for chat completions
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.display_manager = None

    def set_display_manager(self, display_manager: DisplayManager):
        """Set the display manager for streaming responses"""
        self.display_manager = display_manager

    def create_message(self, role: str, content: str, include_timestamp: bool = True) -> Dict:
        """Create a message dictionary with optional timestamps.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            include_timestamp: Whether to include timestamps

        Returns:
            Dict: Message dictionary with role, content, and optional timestamps
        """
        message = {
            "role": role,
            "content": content
        }
        
        if include_timestamp:
            message.update({
                "timestamp": get_iso8601_timestamp(),
                "unix_timestamp": get_unix_timestamp()
            })
            
        return message

    def prepare_messages_for_completion(self, messages: List[Dict]) -> List[Dict]:
        """Prepare messages for completion by adding cache_control to last user message.
        
        Args:
            messages: Original list of message dictionaries
            
        Returns:
            List[Dict]: Copy of messages with cache_control added to last user message
        """
        # Create a deep copy of messages
        prepared_messages = []
        for msg in messages:
            msg_copy = dict(msg)
            if isinstance(msg["content"], list):
                msg_copy["content"] = [dict(part) for part in msg["content"]]
            prepared_messages.append(msg_copy)
        
        # add cache_control to system messages
        for msg in prepared_messages:
            if msg["role"] == "system":
                if isinstance(msg["content"], str):
                    msg["content"] = [{"type": "text", "text": msg["content"]}]
                
                # Add cache_control to all text parts
                for part in msg["content"]:
                    if part.get("type") == "text":
                        part["cache_control"] = {"type": "ephemeral"}
        
        # Find last user message
        for msg in reversed(prepared_messages):
            if msg["role"] == "user":
                if isinstance(msg["content"], str):
                    msg["content"] = [{"type": "text", "text": msg["content"]}]
                
                # Add cache_control to last text part
                text_parts = [part for part in msg["content"] if part.get("type") == "text"]
                if text_parts:
                    last_text_part = text_parts[-1]
                else:
                    last_text_part = {"type": "text", "text": "..."}
                    msg["content"].append(last_text_part)
                last_text_part["cache_control"] = {"type": "ephemeral"}
                break
        
        return prepared_messages

    async def get_chat_response(self, messages: List[Dict]) -> str:
        """Get a streaming chat response from OpenAI.

        Args:
            messages: List of message dictionaries

        Returns:
            str: Complete response text

        Raises:
            Exception: If API call fails
        """
        # Prepare messages with cache_control
        prepared_messages = self.prepare_messages_for_completion(messages)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prepared_messages,
                stream=True
            )
            
            if self.display_manager:
                return self.display_manager.stream_response(response)
            else:
                # Fallback for when display manager isn't set
                collected_messages = []
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        collected_messages.append(chunk.choices[0].delta.content)
                return "".join(collected_messages)
                
        except Exception as e:
            raise Exception(f"Error getting chat response: {str(e)}")

    def contains_tool_use(self, content: str) -> bool:
        """Check if content contains tool use XML tags"""
        tool_tags = [
            "use_mcp_tool",
            "access_mcp_resource"
        ]

        for tag in tool_tags:
            if f"<{tag}>" in content and f"</{tag}>" in content:
                return True
        return False

    def split_content(self, content: str) -> tuple[str, Optional[str]]:
        """Split content into plain text and tool definition parts.

        Args:
            content: The content to split

        Returns:
            Tuple of (plain content, tool content)
        """
        tool_tags = [
            "use_mcp_tool",
            "access_mcp_resource"
        ]

        # Find the first tool tag
        first_tag_index = len(content)
        first_tag = None
        for tag in tool_tags:
            tag_start = content.find(f"<{tag}>")
            if tag_start != -1 and tag_start < first_tag_index:
                first_tag_index = tag_start
                first_tag = tag

        if first_tag_index < len(content) and first_tag:
            # Find the end of the tool block
            end_tag = f"</{first_tag}>"
            end_index = content.find(end_tag, first_tag_index)
            if end_index != -1:
                end_index += len(end_tag)

                # Extract tool content
                tool_content = content[first_tag_index:end_index].strip()

                # Combine content before and after tool block
                plain_content = (content[:first_tag_index] + content[end_index:]).strip()

                return plain_content, tool_content

        return content.strip(), None
