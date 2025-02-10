import click

from .add import preset_add
from .list import preset_list
from .delete import preset_delete

@click.group('preset')
def preset_group():
    """Manage OpenRouter configuration presets."""
    pass

# Register preset subcommands
preset_group.add_command(preset_add)
preset_group.add_command(preset_list)
preset_group.add_command(preset_delete)
