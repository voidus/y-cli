import click

from config import bot_config_manager

@click.command('delete')
@click.argument('name')
def bot_delete(name):
    """Delete a bot configuration."""
    if bot_config_manager.delete_config(name):
        click.echo(f"Bot '{name}' deleted successfully")
    else:
        click.echo(f"Bot '{name}' not found")
