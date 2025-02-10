import click
import shutil
from tabulate import tabulate

from config import bot_config_manager

def truncate_text(text, max_length):
    """Truncate text to max_length with ellipsis if needed."""
    if not text or len(str(text)) <= max_length:
        return text
    return str(text)[:max_length-3] + "..."

@click.command('list')
def bot_list():
    """List all bot configurations."""
    from config import config
    click.echo(f"{click.style('Bot config data will be stored in:', fg='green')}\n{click.style(config['bot_config_file'], fg='cyan')}")

    configs = bot_config_manager.list_configs()
    
    if not configs:
        click.echo("No bot configurations found")
        return

    # Get terminal width
    term_width = shutil.get_terminal_size().columns
    
    # Define column width ratios (total should be < 1 to leave space for separators)
    width_ratios = {
        "Name": 0.15,
        "API Key": 0.1,
        "Base URL": 0.15,
        "Model": 0.15,
        "Print Speed": 0.08,
        "Description": 0.17,
        "OpenRouter Config": 0.1,
        "MCP Settings": 0.1
    }
    
    # Calculate actual column widths
    col_widths = {k: max(10, int(term_width * ratio)) for k, ratio in width_ratios.items()}
    
    # Prepare table data with truncated values
    table_data = []
    headers = ["Name", "API Key", "Base URL", "Model", "Print Speed", "Description", "OpenRouter Config", "MCP Settings"]
    
    for config in configs:
        table_data.append([
            truncate_text(config.name, col_widths["Name"]),
            truncate_text(config.api_key[:8] + "..." if config.api_key else "N/A", col_widths["API Key"]),
            truncate_text(config.base_url, col_widths["Base URL"]),
            truncate_text(config.model, col_widths["Model"]),
            truncate_text(str(config.print_speed), col_widths["Print Speed"]),
            truncate_text(config.description or "N/A", col_widths["Description"]),
            "Yes" if config.openrouter_config else "No",
            "Yes" if config.mcp_server_settings else "No"
        ])
    click.echo(tabulate(
        table_data,
        headers=headers,
        tablefmt="simple",
        numalign='left',
        stralign='left'
    ))
