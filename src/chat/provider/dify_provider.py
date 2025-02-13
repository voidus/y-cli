from typing import List, Optional
from chat.models import Message
from bot.models import BotConfig
from .base_provider import BaseProvider
from .display_manager_mixin import DisplayManagerMixin

class DifyProvider(BaseProvider, DisplayManagerMixin):
    def __init__(self, bot_config: BotConfig):
        """Initialize Dify settings.

        Args:
            bot_config: Bot configuration containing API settings
        """
        DisplayManagerMixin.__init__(self)
        self.bot_config = bot_config

    async def call_chat_completions(self, messages: List[Message], system_prompt: Optional[str] = None) -> Message:
        pass
