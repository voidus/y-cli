import os
import sys
import re
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from contextlib import AsyncExitStack
import pyperclip
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.live import Live
from rich.text import Text
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

from .models import Chat, Message
from .repository import ChatRepository
from .service import ChatService
from .config import DATA_FILE, OPENAI_API_KEY, OPENAI_API_BASE, DEFAULT_MODEL, MCP_SETTINGS_FILE
from .util import get_iso8601_timestamp, get_unix_timestamp
from .system import get_system_prompt

# Load environment variables
load_dotenv()

# Initialize OpenAI client with custom base URL support
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)

# Custom theme for role-based colors
custom_theme = Theme({
    "user": "green",
    "assistant": "cyan",
    "system": "yellow",
    "timestamp": "dim white",
})

class ChatApp:
    def __init__(self, chat_id: Optional[str] = None, verbose: bool = False):
        self.repository = ChatRepository(DATA_FILE)
        self.service = ChatService(self.repository)
        self.current_chat: Optional[Chat] = None
        self.messages: List[Dict[str, str]] = []
        self.console = Console(theme=custom_theme)
        self.code_blocks: List[str] = []  # Store code blocks for copying
        self.verbose = verbose
        self.model = DEFAULT_MODEL

        # MCP related attributes
        self.sessions: Dict[str, ClientSession] = {}
        self.system_prompt: Optional[str] = None

        if chat_id:
            # Load existing chat if chat_id provided
            existing_chat = self.service.get_chat(chat_id)
            if not existing_chat:
                self.console.print(f"[red]Chat {chat_id} not found[/red]", err=True)
                raise ValueError(f"Chat {chat_id} not found")

            # Convert existing messages to OpenAI API format
            self.messages = [{
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            } for msg in existing_chat.messages]
            self.current_chat = existing_chat
            if self.verbose:
                self.console.print(f"Loaded {len(self.messages)} messages from chat {chat_id}")

    def process_code_blocks(self, content: str) -> Tuple[str, List[str]]:
        """Process code blocks in content, adding sequence numbers and copy instructions.

        Returns:
            Tuple of (modified content, list of code blocks for copying)
        """
        code_blocks = []
        start_idx = len(self.code_blocks)

        def replace_code_block(match):
            nonlocal start_idx
            lang = match.group(1) or ''
            code = match.group(2).strip()
            block_num = len(code_blocks) + start_idx + 1
            code_blocks.append(code)

            # Format with sequence number and copy instruction
            return f"> copy [{block_num}]\n```{lang} {code}\n```"

        # Replace code blocks with numbered versions and copy instructions
        pattern = r'```(\w*\n|\n)?(.+?)```'
        modified_content = re.sub(pattern, replace_code_block, content, flags=re.DOTALL)

        return modified_content, code_blocks

    def display_message_panel(self, msg: dict):
        """Display a message in a panel with role-colored borders.

        Args:
            msg: The message dictionary containing role, content, and timestamp
        """
        timestamp = f"[timestamp]{msg['timestamp']}[/timestamp]"
        role = f"[{msg['role']}]{msg['role'].capitalize()}[/{msg['role']}]"

        # Extract content text from structured content if needed
        content = msg['content']
        if isinstance(content, list):
            content = next((part['text'] for part in content if part['type'] == 'text'), '')

        # Process code blocks and update content
        modified_content, code_blocks = self.process_code_blocks(content)
        self.code_blocks.extend(code_blocks)

        self.console.print(Panel(
            Markdown(modified_content),
            title=f"{role} {timestamp}",
            border_style=msg['role']
        ))

    def get_input(self) -> str:
        """Get user input with support for multi-line input using EOF flags.

        Multi-line input starts with <<EOF and ends with EOF. For example:
        <<EOF
        line 1
        line 2
        EOF

        Returns:
            str: The user input, either single line or multiple lines joined with newlines.
        """
        from prompt_toolkit import prompt
        text = prompt('请输入: ', in_thread=True)
        text = text.rstrip()

        # Check for multi-line input start flag
        if text == "<<EOF":
            lines = []
            while True:
                line = prompt(in_thread=True)
                line = line.rstrip()
                if line == "EOF":
                    break
                lines.append(line)
            return "\n".join(lines)

        return text

    def stream_response(self, response_stream) -> str:
        collected_messages = []
        current_content = ""
        timestamp = get_iso8601_timestamp()
        role_title = f"[assistant]Assistant[/assistant]"
        timestamp_str = f"[timestamp]{timestamp}[/timestamp]"

        # Create a panel that will be updated with streaming content
        with Live("", console=self.console, refresh_per_second=10, auto_refresh=False) as live:
            for chunk in response_stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    current_content += content
                    collected_messages.append(content)

                    # Update panel with current content
                    panel = Panel(
                        Markdown(current_content),
                        title=f"{role_title} {timestamp_str}",
                        border_style="assistant"
                    )
                    live.update(panel)
                    live.refresh()

        return "".join(collected_messages)

    def load_mcp_settings(self) -> dict:
        """Load MCP server settings from json file"""
        try:
            settings_path = os.path.expanduser(MCP_SETTINGS_FILE)
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            return settings.get('mcpServers', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.console.print(f"[red]Error loading MCP settings: {str(e)}[/red]")
            return {}

    async def connect_to_server(self, server_name: str, server_config: dict, exit_stack: AsyncExitStack):
        """Connect to an MCP server using configuration"""
        try:
            command = server_config['command']

            server_params = StdioServerParameters(
                command=command,
                args=server_config.get('args', []),
                env=server_config.get('env', {})
            )

            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))

            await session.initialize()

            self.sessions[server_name] = session
            self.console.print(f"[green]Connected to server '{server_name}'[/green]")

        except Exception as e:
            self.console.print(f"[red]Error connecting to server '{server_name}': {str(e)}[/red]")
            if hasattr(e, '__traceback__'):
                import traceback
                self.console.print(f"[red]Detailed error:\n{''.join(traceback.format_tb(e.__traceback__))}[/red]")

    async def connect_to_servers(self, exit_stack: AsyncExitStack):
        """Connect to all enabled MCP servers from settings"""
        servers = self.load_mcp_settings()

        for server_name, config in servers.items():
            if config.get('disabled', False) or server_name == 'git':
                self.console.print(f"[yellow]Skipping server '{server_name}'[/yellow]")
                continue

            await self.connect_to_server(server_name, config, exit_stack)
            await asyncio.sleep(1)

    async def initialize_chat(self):
        """Initialize chat with system prompt"""
        self.system_prompt = await get_system_prompt(self)
        # Add system message with cache_control
        system_message = {
            "role": "system",
            "content": [{
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"}
            }]
        }
        self.messages = [system_message] + self.messages

        # Add cache_control to last two user messages
        user_messages = [msg for msg in self.messages if msg["role"] == "user"][-2:]
        for msg in user_messages:
            if isinstance(msg["content"], str):
                msg["content"] = [{"type": "text", "text": msg["content"]}]

            if isinstance(msg["content"], list):
                text_parts = [part for part in msg["content"] if part.get("type") == "text"]
                if text_parts:
                    last_text_part = text_parts[-1]
                else:
                    last_text_part = {"type": "text", "text": "..."}
                    msg["content"].append(last_text_part)
                last_text_part["cache_control"] = {"type": "ephemeral"}

    def extract_mcp_tool_use(self, content: str) -> Optional[tuple[str, str, dict]]:
        """Extract MCP tool use details from content if present"""
        import re

        match = re.search(r'<use_mcp_tool>(.*?)</use_mcp_tool>', content, re.DOTALL)
        if not match:
            return None

        tool_content = match.group(1)

        server_match = re.search(r'<server_name>(.*?)</server_name>', tool_content)
        if not server_match:
            return None
        server_name = server_match.group(1).strip()

        tool_match = re.search(r'<tool_name>(.*?)</tool_name>', tool_content)
        if not tool_match:
            return None
        tool_name = tool_match.group(1).strip()

        args_match = re.search(r'<arguments>\s*(\{.*?\})\s*</arguments>', tool_content, re.DOTALL)
        if not args_match:
            return None

        try:
            arguments = json.loads(args_match.group(1))
        except json.JSONDecodeError:
            return None

        return (server_name, tool_name, arguments)

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

    def get_user_confirmation(self, content: str) -> bool:
        """Get user confirmation before executing tool use"""
        self.console.print("\n[yellow]Tool use detected in response:[/yellow]")
        self.console.print(content)
        while True:
            response = input("\nWould you like to proceed with tool execution? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            self.console.print("[yellow]Please answer 'y' or 'n'[/yellow]")

    def split_content(self, content: str) -> tuple[str, Optional[str]]:
        """Split content into plain text and tool definition parts.

        Handles cases where tool content appears in the middle of the message,
        preserving any content that comes after the tool block.
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

    def persist_chat(self):
        # Persist chat if needed
        if not self.current_chat:
            self.current_chat = self.service.create_chat(self.messages)
        else:
            self.current_chat = self.service.update_chat(self.current_chat.id, self.messages)

    async def process_response(self, response_stream) -> str:
        """Process streaming response and handle tool use recursively"""
        assistant_response = self.stream_response(response_stream)
        return await self._handle_response(assistant_response)

    async def _handle_response(self, response_content: str) -> str:
        """Internal helper to handle response content recursively"""
        if not self.contains_tool_use(response_content):
            # Base case: no tool use, append message and return
            self.messages.append({
                "role": "assistant",
                "content": response_content,
                "timestamp": get_iso8601_timestamp(),
                "unix_timestamp": get_unix_timestamp()
            })
            return response_content

        # Handle response with tool use
        plain_content, tool_content = self.split_content(response_content)

        # Add assistant's message before tool use
        if plain_content:
            self.messages.append({
                "role": "assistant",
                "content": plain_content,
                "timestamp": get_iso8601_timestamp(),
                "unix_timestamp": get_unix_timestamp()
            })

        # Get user confirmation for tool execution
        if not self.get_user_confirmation(tool_content):
            no_exec_msg = "Tool execution cancelled by user."
            self.console.print(f"\n[yellow]{no_exec_msg}[/yellow]")
            user_message = {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": no_exec_msg,
                    "cache_control": {"type": "ephemeral"}
                }],
                "timestamp": get_iso8601_timestamp(),
                "unix_timestamp": get_unix_timestamp()
            }
            self.messages.append(user_message)
            return no_exec_msg

        # Execute tool and get results
        mcp_tool = self.extract_mcp_tool_use(response_content)
        if mcp_tool:
            server_name, tool_name, arguments = mcp_tool
            if server_name in self.sessions:
                try:
                    self.console.print(f"[cyan]Executing MCP tool '{tool_name}' on server '{server_name}'[/cyan]")
                    result = await self.sessions[server_name].call_tool(tool_name, arguments)

                    text_contents = []
                    for item in result.content:
                        if hasattr(item, 'type') and item.type == 'text':
                            text_contents.append(item.text)

                    tool_results = '\n'.join(text_contents) if text_contents else "No text content found in result"
                except Exception as e:
                    tool_results = f"Error executing MCP tool: {str(e)}"
            else:
                tool_results = f"Error: MCP server '{server_name}' not found"
        else:
            self.console.print("\n[yellow]Tool use detected in response. Please provide the tool results:[/yellow]")
            tool_results = self.get_input()

        # Add tool results as user message with cache_control
        user_message = {
            "role": "user",
            "content": [{
                "type": "text",
                "text": tool_results,
                "cache_control": {"type": "ephemeral"}
            }],
            "timestamp": get_iso8601_timestamp(),
            "unix_timestamp": get_unix_timestamp()
        }
        self.messages.append(user_message)
        self.display_message_panel(user_message)

        # Get next response from OpenAI
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )

        # Process the follow-up response recursively
        next_response = self.stream_response(response)
        return await self._handle_response(next_response)

    async def chat(self):
        async with AsyncExitStack() as exit_stack:
            try:
                # Initialize MCP and system prompt only for new chats
                await self.connect_to_servers(exit_stack)
                await self.initialize_chat()

                if self.verbose:
                    self.console.print("\n[bold]Enter 'exit' or 'quit' to end the conversation.[/bold]")
                    self.console.print("[bold]Enter your message and press Enter to send.[/bold]")
                    self.console.print("[bold]For multi-line input:[/bold]")
                    self.console.print("  1. Type <<EOF and press Enter")
                    self.console.print("  2. Type your multi-line message")
                    self.console.print("  3. Type EOF and press Enter to finish")
                    self.console.print("[bold]Use 'copy N' to copy code block N, or 'copy 0' to copy the entire last response.[/bold]\n")

                # Display existing messages if continuing from a previous chat
                if self.messages:
                    self.console.print("\n[bold]Chat history:[/bold]")
                    for msg in self.messages:
                        # skip system messages
                        if msg['role'] == 'system':
                            continue
                        self.display_message_panel(msg)
                    self.console.print("\n[bold]Continue the conversation:[/bold]")

                while True:
                    user_input = self.get_input()

                    if user_input.lower() in ['exit', 'quit']:
                        self.console.print("\n[yellow]Goodbye![/yellow]")
                        break

                    if not user_input:
                        self.console.print("[yellow]Please enter a message.[/yellow]")
                        continue

                    # Handle copy command
                    if user_input.lower().startswith('copy '):
                        try:
                            block_num = int(user_input.split()[1])
                            if block_num == 0:
                                # Find last assistant message
                                last_assistant = next((msg for msg in reversed(self.messages)
                                                    if msg['role'] == 'assistant'), None)
                                if last_assistant and last_assistant['content']:
                                    pyperclip.copy(last_assistant['content'].strip())
                                    self.console.print("[green]Copied last assistant message to clipboard[/green]")
                                else:
                                    self.console.print("[yellow]No previous assistant message to copy[/yellow]")
                            elif 1 <= block_num <= len(self.code_blocks):
                                pyperclip.copy(self.code_blocks[block_num - 1])
                                self.console.print(f"[green]Copied code block [{block_num}] to clipboard[/green]")
                            else:
                                self.console.print("[yellow]Invalid code block number[/yellow]")
                            continue
                        except (IndexError, ValueError):
                            self.console.print("[yellow]Invalid copy command. Use 'copy <number>' or 'copy 0' for last message[/yellow]")
                            continue

                    # Add user message to history with cache_control
                    user_message = {
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": user_input,
                            "cache_control": {"type": "ephemeral"}
                        }],
                        "timestamp": get_iso8601_timestamp(),
                        "unix_timestamp": get_unix_timestamp()
                    }
                    self.messages.append(user_message)

                    # clear user_input using ANSI escape sequences
                    sys.stdout.write("\033[F")  # Cursor up one line

                    # display user message
                    self.display_message_panel(user_message)

                    try:
                        # Get streaming response from OpenAI
                        response = client.chat.completions.create(
                            model=self.model,
                            messages=self.messages,
                            stream=True
                        )

                        # Process response and handle tool use
                        await self.process_response(response)

                        # Persist chat after each message
                        self.persist_chat()
                    except Exception as e:
                        self.console.print(f"\n[red]Error: {str(e)}[/red]\n", err=True)
                        break

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Chat interrupted. Exiting...[/yellow]")
            finally:
                # Clear sessions on exit
                self.sessions.clear()

async def main():
    try:
        # Set binary mode for stdin/stdout on Windows
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

        app = ChatApp(verbose=True)
        await app.chat()
    except KeyboardInterrupt:
        # Exit silently on Ctrl+C
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
