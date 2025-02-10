import click
from tabulate import tabulate

from ....preset_manager import PresetManager
from ....config import config

@click.command('list')
def preset_list():
    """List all configuration presets."""
    preset_manager = PresetManager(config["preset_file"])
    presets = preset_manager.list_presets()
    
    if not presets:
        click.echo("No presets found")
        return

    # Prepare table data
    table_data = []
    for preset in presets:
        table_data.append([
            preset.name,
            preset.api_key[:8] + "..." if preset.api_key else "N/A",
            preset.base_url,
            preset.model
        ])

    # Print formatted table
    headers = ["Name", "API Key", "Base URL", "Model"]
    click.echo(tabulate(
        table_data,
        headers=headers,
        tablefmt="simple",
        numalign='left',
        stralign='left'
    ))
