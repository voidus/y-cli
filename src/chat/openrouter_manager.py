from typing import List, Dict, Optional, AsyncGenerator, Union
import json
from types import SimpleNamespace
import httpx
from .display_manager import DisplayManager
from .util import get_iso8601_timestamp, get_unix_timestamp
from .config import OPENROUTER_CONFIG_FILE, DEFAULT_MODEL

class OpenRouterManager:
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = DEFAULT_MODEL):
        """Initialize OpenRouter settings.

        Args:
            api_key: OpenRouter API key
            base_url: Optional custom base URL for API
            model: Model to use for chat completions
        """
        self.api_key = api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model
        self.display_manager = None

    def load_openrouter_config(self, config_file: str) -> dict:
        """Load openrouter server config from json file"""
        try:
            with open(config_file, 'r', encoding="utf-8") as f:
                config = json.load(f)
            return config.get('config', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.console.print(f"[red]Error loading openrouter config: {str(e)}[/red]")
            return {}

    def set_display_manager(self, display_manager: DisplayManager):
        """Set the display manager for streaming responses"""
        self.display_manager = display_manager

    def create_message(self, role: str, content: str, reasoning_content: Optional[str] = None, include_timestamp: bool = True, provider: Optional[str] = None, model: Optional[str] = None) -> Dict:
        """Create a message dictionary with optional timestamps, provider, and model.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            include_timestamp: Whether to include timestamps
            provider: Optional provider of the message
            model: Optional model used to generate the message

        Returns:
            Dict: Message dictionary with role, content, and optional fields
        """
        message = {
            "role": role,
            "content": content
        }

        if reasoning_content is not None:
            message["reasoning_content"] = reasoning_content
        
        if include_timestamp:
            message.update({
                "timestamp": get_iso8601_timestamp(),
                "unix_timestamp": get_unix_timestamp()
            })
            
        if provider is not None:
            message["provider"] = provider
            
        if model is not None:
            message["model"] = model
            
        return message

    def prepare_messages_for_completion(self, messages: List[Dict], system_message: Optional[str] = None) -> List[Dict]:
        """Prepare messages for completion by adding system message and cache_control.
        
        Args:
            messages: Original list of message dictionaries
            system_message: Optional system message to add at the start
            
        Returns:
            List[Dict]: New message list with system message and cache_control added
        """
        # Create new list starting with system message if provided
        prepared_messages = []
        if system_message:
            sys_msg = self.create_message("system", system_message, include_timestamp=False)
            if isinstance(sys_msg["content"], str):
                sys_msg["content"] = [{"type": "text", "text": sys_msg["content"]}]
            # add cache_control only to claude-3.5-sonnet model
            if "claude-3.5-sonnet" in self.model:
                for part in sys_msg["content"]:
                    if part.get("type") == "text":
                        part["cache_control"] = {"type": "ephemeral"}
            prepared_messages.append(sys_msg)
            
        # Add original messages
        for msg in messages:
            msg_copy = dict(msg)
            if isinstance(msg["content"], list):
                msg_copy["content"] = [dict(part) for part in msg["content"]]
            prepared_messages.append(msg_copy)
        
        # Find last user message
        if "claude-3.5-sonnet" in self.model:     
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

    async def get_chat_response(self, messages: List[Dict], system_message: Optional[str] = None) -> Union[SimpleNamespace, AsyncGenerator[SimpleNamespace, None]]:
        """Get a streaming chat response from OpenRouter.

        Args:
            messages: List of message dictionaries
            system_message: Optional system message to add at the start

        Returns:
            Union[str, AsyncGenerator[SimpleNamespace, None]]: Either complete response text or async generator of response chunks

        Raises:
            Exception: If API call fails
        """
        # Prepare messages with cache_control and system message
        prepared_messages = self.prepare_messages_for_completion(messages, system_message)
        openrouter_config = self.load_openrouter_config(OPENROUTER_CONFIG_FILE)
        provider_config = openrouter_config.get('provider', {})
        body = {
            "model": self.model,
            "messages": prepared_messages,
            "stream": True,
            "provider": provider_config
        }
        if "deepseek-r1" in self.model:
            body["include_reasoning"] = True
        try:
            async with httpx.AsyncClient(base_url=self.base_url) as client:
                async with client.stream(
                    "POST",
                    "/chat/completions",
                    headers={
                        "HTTP-Referer": "https://luohy15.com",
                        'X-Title': 'y-cli',
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    if self.display_manager:
                        # Store provider and model info from first response chunk
                        provider = None
                        model = None
                        
                        async def generate_chunks():
                            nonlocal provider, model
                            async for chunk in response.aiter_lines():
                                if chunk.startswith("data: "):
                                    try:
                                        data = json.loads(chunk[6:])
                                        # Extract provider and model from first chunk that has them
                                        if provider is None and data.get("provider"):
                                            provider = data["provider"]
                                        if model is None and data.get("model"):
                                            model = data["model"]
                                            
                                        if data.get("choices"):
                                            delta = data["choices"][0].get("delta", {})
                                            content = delta.get("content")
                                            reasoning_content = delta.get("reasoning")
                                            if content is not None or reasoning_content is not None:
                                                chunk_data = SimpleNamespace(
                                                    choices=[SimpleNamespace(
                                                        delta=SimpleNamespace(content=content, reasoning_content=reasoning_content)
                                                    )],
                                                    model=model,
                                                    provider=provider
                                                )
                                                yield chunk_data
                                    except json.JSONDecodeError:
                                        continue
                        content_full, reasoning_content_full = await self.display_manager.stream_response(generate_chunks())
                        return SimpleNamespace(
                            content=content_full,
                            reasoning_content=reasoning_content_full,
                            provider=provider,
                            model=model
                        )
                    else:
                        # Fallback for when display manager isn't set
                        collected_content = []
                        collected_reasoning_content = []
                        provider = None
                        model = None
                        async for chunk in response.aiter_lines():
                            if chunk.startswith("data: "):
                                try:
                                    data = json.loads(chunk[6:])
                                    # Extract provider and model from first chunk that has them
                                    if provider is None and data.get("provider"):
                                        provider = data["provider"]
                                    if model is None and data.get("model"):
                                        model = data["model"]
                                    if data.get("choices"):
                                        delta = data["choices"][0].get("delta", {})
                                        content = delta.get("content")
                                        reasoning_content = delta.get("reasoning")
                                        if content is not None:
                                            collected_content.append(content)
                                        if reasoning_content is not None:
                                            collected_reasoning_content.append(reasoning_content)
                                except json.JSONDecodeError:
                                    continue
                        return SimpleNamespace(
                            content="".join(collected_content),
                            reasoning_content="".join(collected_reasoning_content),
                            provider=provider,
                            model=model
                        )
                    
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error getting chat response: {str(e)}")
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
