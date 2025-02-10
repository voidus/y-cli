import click

from ....preset_manager import PresetManager
from ....config import config

@click.command('delete')
@click.argument('name')
def preset_delete(name):
    """Delete a configuration preset."""
    preset_manager = PresetManager(config["preset_file"])
    if preset_manager.delete_preset(name):
        click.echo(f"Preset '{name}' deleted successfully")
    else:
        click.echo(f"Preset '{name}' not found")
