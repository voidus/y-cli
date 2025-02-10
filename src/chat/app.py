import os
import sys
import asyncio
from typing import Optional

from .repository import ChatRepository
from cli.display_manager import DisplayManager
from cli.input_manager import InputManager
from mcp_setting.mcp_manager import MCPManager
from .openrouter_manager import OpenRouterManager
from .chat_manager import ChatManager
from config import bot_config_manager

class ChatApp:
    def __init__(self, chat_id: Optional[str] = None, verbose: bool = False, model: Optional[str] = None, 
                 api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the chat application.

        Args:
            chat_id: Optional ID of existing chat to load
            verbose: Whether to show verbose output
            model: Optional model to use for chat (defaults to MODEL)
            api_key: Optional API key override
            base_url: Optional base URL override
        """
        # Initialize managers
        display_manager = DisplayManager()
        input_manager = InputManager(display_manager.console)
        mcp_manager = MCPManager(display_manager.console)
        openrouter_manager = OpenRouterManager(
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        # Initialize repository and create chat manager
        repository = ChatRepository()
        bot_config = bot_config_manager.get_config()
        self.chat_manager = ChatManager(
            repository=repository,
            display_manager=display_manager,
            input_manager=input_manager,
            mcp_manager=mcp_manager,
            openrouter_manager=openrouter_manager,
            bot_config=bot_config,
            model=model,
            chat_id=chat_id,
            verbose=verbose
        )

    async def chat(self):
        """Start the chat session"""
        await self.chat_manager.run()

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
