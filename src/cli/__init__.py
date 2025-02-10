from typing import Optional
import click
from config import config, bot_config_manager

from cli.commands.init import init
from cli.commands.chat import chat
from cli.commands.list import list_chats
from cli.commands.share import share
from cli.commands.bot import bot_group

@click.group()
def cli():
    """Command-line interface for chat application."""
    # Skip API key check for init command and preset commands
    current_cmd = click.get_current_context().invoked_subcommand
    if current_cmd not in ['init', 'bot']:
        # Check if API key is set in default bot config
        default_config = bot_config_manager.get_config()
        if not default_config.api_key:
            click.echo("Error: OpenRouter API key is not set in default bot config")
            click.echo("Please set it using 'y-cli init'")
            raise click.Abort()

# Register commands
cli.add_command(init)
cli.add_command(chat)
cli.add_command(list_chats)
cli.add_command(share)
cli.add_command(bot_group)

if __name__ == "__main__":
    cli()
