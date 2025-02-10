from typing import Optional
import click
from ..config import API_KEY

from .commands.init import init
from .commands.chat import chat
from .commands.list import list_chats
from .commands.share import share
from .commands.preset import preset_group

@click.group()
def cli():
    """Command-line interface for chat application."""
    # Skip API key check for init command and preset commands
    current_cmd = click.get_current_context().invoked_subcommand
    if current_cmd not in ['init', 'preset'] and not API_KEY:
        click.echo("Error: OpenRouter API key is not set")
        click.echo("Please set it using 'y-cli init' or set API_KEY environment variable")
        raise click.Abort()

# Register commands
cli.add_command(init)
cli.add_command(chat)
cli.add_command(list_chats)
cli.add_command(share)
cli.add_command(preset_group)

if __name__ == "__main__":
    cli()
