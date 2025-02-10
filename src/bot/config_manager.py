"""Bot configuration manager."""

from typing import List
from .models import BotConfig
from .repository import BotRepository
from .service import BotService
import click

class BotConfigManager:
    """Manages bot configurations using a service-based architecture."""

    def __init__(self, config_file: str):
        """Initialize the bot config manager.
        
        Args:
            config_file: Path to the config file
        """
        self.repository = BotRepository(config_file)
        self.service = BotService(self.repository)

    @property
    def default_config(self) -> BotConfig:
        """Get the default bot configuration."""
        return self.service.default_config

    def add_config(self, config: BotConfig) -> None:
        """Add a new bot config or update existing one."""
        self.service.add_config(config)

    def list_configs(self) -> List[BotConfig]:
        """List all bot configs."""
        return self.service.list_configs()

    def delete_config(self, name: str) -> bool:
        """Delete a bot config by name.
        
        Returns:
            bool: True if deleted, False if not found
        """
        return self.service.delete_config(name)

    def get_config(self, name: str = "default") -> BotConfig:
        """Get a bot config by name.
        
        Returns:
            BotConfig: The requested config or default config if not found
        """
        config = self.service.get_config(name)
        if not config:
            click.echo(click.style(f"Error: Bot configuration '{name}' not found, using default", fg='red'))
            self.service._ensure_default_config()
            config  = self.service.get_config("default")
        return config
