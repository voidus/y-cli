"""Bot configuration service."""

from typing import List, Optional
from .models import BotConfig
from .repository import BotRepository

class BotService:
    def __init__(self, repository: BotRepository):
        self.repository = repository
        self._ensure_default_config()

    @property
    def default_config(self) -> BotConfig:
        """Get the default bot configuration."""
        return BotConfig(name="default")

    def _ensure_default_config(self) -> None:
        """Ensure default config exists."""
        if not self.get_config("default"):
            self.add_config(self.default_config)

    def list_configs(self) -> List[BotConfig]:
        """List all bot configs."""
        return self.repository.list_configs()

    def get_config(self, name: str) -> Optional[BotConfig]:
        """Get a specific bot config by name."""
        return self.repository.get_config(name)

    def add_config(self, config: BotConfig) -> BotConfig:
        """Add a new bot config or update existing one."""
        return self.repository.add_config(config)

    def delete_config(self, name: str) -> bool:
        """Delete a bot config by name.
        
        Returns:
            bool: True if config was deleted, False if not found
        """
        if name == "default":
            return False  # Prevent deletion of default config
        return self.repository.delete_config(name)
