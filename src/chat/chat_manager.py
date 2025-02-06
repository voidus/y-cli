from typing import List, Dict, Optional
from contextlib import AsyncExitStack
import pyperclip

from .models import Chat, Message
from .repository import ChatRepository
from .service import ChatService
from .display_manager import DisplayManager
from .input_manager import InputManager
from .mcp_manager import MCPManager
from .openai_manager import OpenAIManager
from .util import get_iso8601_timestamp, get_unix_timestamp
from .config import MCP_SETTINGS_FILE

class ChatManager:
    def __init__(
        self,
        repository: ChatRepository,
        display_manager: DisplayManager,
        input_manager: InputManager,
        mcp_manager: MCPManager,
        openai_manager: OpenAIManager,
        chat_id: Optional[str] = None,
        verbose: bool = False
    ):
        """Initialize chat manager with required components.

        Args:
            repository: Repository for chat persistence
            display_manager: Manager for display and UI
            input_manager: Manager for user input
            mcp_manager: Manager for MCP operations
            openai_manager: Manager for OpenAI interactions
            chat_id: Optional ID of existing chat to load
            verbose: Whether to show verbose output
        """
        self.service = ChatService(repository)
        self.display_manager = display_manager
        self.input_manager = input_manager
        self.mcp_manager = mcp_manager
        self.openai_manager = openai_manager
        self.verbose = verbose

        # Set up cross-manager references
        self.openai_manager.set_display_manager(display_manager)

        # Initialize chat state
        self.current_chat: Optional[Chat] = None
        self.messages: List[Dict] = []
        self.system_prompt: Optional[str] = None

        if chat_id:
            self._load_chat(chat_id)

    def _load_chat(self, chat_id: str):
        """Load an existing chat by ID"""
        existing_chat = self.service.get_chat(chat_id)
        if not existing_chat:
            self.display_manager.print_error(f"Chat {chat_id} not found")
            raise ValueError(f"Chat {chat_id} not found")

        # Convert existing messages to OpenAI API format
        self.messages = [{
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp
        } for msg in existing_chat.messages]
        self.current_chat = existing_chat

        if self.verbose:
            self.display_manager.console.print(f"Loaded {len(self.messages)} messages from chat {chat_id}")

    def get_user_confirmation(self, content: str) -> bool:
        """Get user confirmation before executing tool use"""
        self.display_manager.console.print("\n[yellow]Tool use detected in response:[/yellow]")
        self.display_manager.console.print(content)
        while True:
            response = input("\nWould you like to proceed with tool execution? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            self.display_manager.console.print("[yellow]Please answer 'y' or 'n'[/yellow]")

    async def process_response(self, response_content: str) -> str:
        """Process assistant response and handle tool use recursively"""
        if not self.openai_manager.contains_tool_use(response_content):
            # Base case: no tool use, append message and return
            message = self.openai_manager.create_message("assistant", response_content)
            self.messages.append(message)
            return response_content

        # Handle response with tool use
        plain_content, tool_content = self.openai_manager.split_content(response_content)

        # Add assistant's message before tool use
        if plain_content:
            message = self.openai_manager.create_message("assistant", plain_content)
            self.messages.append(message)

        # Get user confirmation for tool execution
        if not self.get_user_confirmation(tool_content):
            no_exec_msg = "Tool execution cancelled by user."
            self.display_manager.console.print(f"\n[yellow]{no_exec_msg}[/yellow]")
            message = self.openai_manager.create_message("user", no_exec_msg)
            self.messages.append(message)
            return no_exec_msg

        # Execute tool and get results
        mcp_tool = self.mcp_manager.extract_mcp_tool_use(response_content)
        if mcp_tool:
            server_name, tool_name, arguments = mcp_tool
            tool_results = await self.mcp_manager.execute_tool(server_name, tool_name, arguments)
        else:
            self.display_manager.console.print("\n[yellow]Tool use detected in response. Please provide the tool results:[/yellow]")
            tool_results = self.input_manager.get_input()

        # Add tool results as user message
        message = self.openai_manager.create_message("user", tool_results)
        self.messages.append(message)
        self.display_manager.display_message_panel(message)

        # Get next response from OpenAI with system prompt
        next_response = await self.openai_manager.get_chat_response(self.messages, self.system_prompt)
        return await self.process_response(next_response)

    def persist_chat(self):
        """Persist current chat state"""
        if not self.current_chat:
            self.current_chat = self.service.create_chat(self.messages)
        else:
            self.current_chat = self.service.update_chat(self.current_chat.id, self.messages)

    async def initialize_chat(self):
        """Initialize chat with system prompt"""
        from .system import get_system_prompt
        self.system_prompt = await get_system_prompt(self.mcp_manager)

    async def run(self):
        """Run the chat session"""
        async with AsyncExitStack() as exit_stack:
            try:
                # Initialize MCP and system prompt only for new chats
                await self.mcp_manager.connect_to_servers(MCP_SETTINGS_FILE, exit_stack)
                await self.initialize_chat()

                if self.verbose:
                    self.display_manager.display_help()

                # Display existing messages if continuing from a previous chat
                if self.messages:
                    self.display_manager.display_chat_history(self.messages)

                while True:
                    user_input = self.input_manager.get_input()

                    if self.input_manager.is_exit_command(user_input):
                        self.display_manager.console.print("\n[yellow]Goodbye![/yellow]")
                        break

                    if not user_input:
                        self.display_manager.console.print("[yellow]Please enter a message.[/yellow]")
                        continue

                    # Handle copy command
                    if user_input.lower().startswith('copy '):
                        last_assistant = next((msg for msg in reversed(self.messages)
                                            if msg['role'] == 'assistant'), None)
                        last_content = last_assistant['content'] if last_assistant else None
                        if self.input_manager.handle_copy_command(
                            user_input,
                            self.display_manager.code_blocks,
                            last_content
                        ):
                            continue

                    # Add user message to history
                    user_message = self.openai_manager.create_message("user", user_input)
                    self.messages.append(user_message)

                    # Clear input line and display user message
                    self.input_manager.clear_input_line()
                    self.display_manager.display_message_panel(user_message)

                    try:
                        # Get streaming response from OpenAI with system prompt
                        response = await self.openai_manager.get_chat_response(self.messages, self.system_prompt)

                        # Process response and handle tool use
                        await self.process_response(response)

                        # Persist chat after each message
                        self.persist_chat()
                    except Exception as e:
                        self.display_manager.print_error(str(e))
                        break

            except (KeyboardInterrupt, EOFError):
                self.display_manager.console.print("\n[yellow]Chat interrupted. Exiting...[/yellow]")
            finally:
                # Clear sessions on exit
                self.mcp_manager.clear_sessions()
