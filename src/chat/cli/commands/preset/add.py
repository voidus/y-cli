import click

from ....config import BASE_URL, MODEL
from ....preset_manager import PresetManager
from ....config import config

@click.command('add')
def preset_add():
    """Add a new configuration preset."""
    name = click.prompt("Preset name")
    api_key = click.prompt("API key")
    base_url = click.prompt("Base URL", default=BASE_URL)
    model = click.prompt("Model", default=MODEL)

    preset_manager = PresetManager(config["preset_file"])
    preset_manager.add_preset(name, api_key, base_url, model)
    click.echo(f"Preset '{name}' added successfully")
