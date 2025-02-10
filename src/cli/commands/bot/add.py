import click

from config import bot_config_manager
from bot import BotConfig

@click.command('add')
def bot_add():
    """Add a new bot configuration."""
    name = click.prompt("Bot name")
    
    # Check if bot already exists
    existing_configs = bot_config_manager.list_configs()
    if any(config.name == name for config in existing_configs):
        if not click.confirm(f"Bot '{name}' already exists. Do you want to overwrite it?"):
            click.echo("Operation cancelled")
            return
    
    # get default config(for default values)
    default_config = bot_config_manager.default_config
            
    # Proceed with collecting remaining details
    api_key = click.prompt("API key")
    base_url = click.prompt("Base URL", default=default_config.base_url)
    model = click.prompt("Model", default=default_config.model)

    bot_config = BotConfig(name=name, api_key=api_key, base_url=base_url, model=model)
    bot_config_manager.add_config(bot_config)
    click.echo(f"Bot '{name}' added successfully")
