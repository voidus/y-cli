import os
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv

from .repository import ChatRepository
from .display_manager import DisplayManager
from .input_manager import InputManager
from .mcp_manager import MCPManager
from .openrouter_manager import OpenRouterManager
from .chat_manager import ChatManager
from .config import (
    DATA_FILE,
    OPENROUTER_API_KEY,
    OPENROUTER_API_BASE,
    DEFAULT_MODEL
)

# Load environment variables
load_dotenv()

class ChatApp:
    def __init__(self, chat_id: Optional[str] = None, verbose: bool = False, model: str = DEFAULT_MODEL):
        """Initialize the chat application.

        Args:
            chat_id: Optional ID of existing chat to load
            verbose: Whether to show verbose output
            model: Optional model to use for chat (defaults to DEFAULT_MODEL)
        """
        # Initialize managers
        display_manager = DisplayManager()
        input_manager = InputManager(display_manager.console)
        mcp_manager = MCPManager(display_manager.console)
        openrouter_manager = OpenRouterManager(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_API_BASE,
            model=model
        )

        # Initialize repository and create chat manager
        repository = ChatRepository(DATA_FILE)
        self.chat_manager = ChatManager(
            repository=repository,
            display_manager=display_manager,
            input_manager=input_manager,
            mcp_manager=mcp_manager,
            openrouter_manager=openrouter_manager,
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
