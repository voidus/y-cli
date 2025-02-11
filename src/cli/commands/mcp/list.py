import click
import shutil
from tabulate import tabulate
from typing import List

from mcp_server.models import McpServerConfig
from mcp_server.service import McpServerConfigService
from mcp_server.repository import McpServerConfigRepository

def truncate_text(text, max_length):
    """Truncate text to max_length with ellipsis if needed."""
    if not text or len(str(text)) <= max_length:
        return text
    return str(text)[:max_length-3] + "..."

@click.command('list')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def mcp_list(verbose: bool = False):
    """List all MCP server configurations."""
    from config import config
    
    if verbose:
        click.echo(f"{click.style('MCP config data will be stored in:', fg='green')}\n{click.style(config['mcp_config_file'], fg='cyan')}")

    # Initialize repository and service
    repository = McpServerConfigRepository(config['mcp_config_file'])
    service = McpServerConfigService(repository)
    
    # Get all configs
    configs = service.get_all_configs()
    
    if not configs:
        click.echo("No MCP server configurations found")
        return

    if verbose:
        click.echo(f"Found {len(configs)} MCP server configuration(s)")
    
    # Define column width ratios (total should be < 1 to leave space for separators)
    width_ratios = {
        "Name": 0.2,
        "Command": 0.2,
        "Arguments": 0.3,
        "Environment": 0.3
    }
    
    # Calculate actual column widths
    term_width = shutil.get_terminal_size().columns
    col_widths = {k: max(10, int(term_width * ratio)) for k, ratio in width_ratios.items()}
    
    # Prepare table data with truncated values
    table_data = []
    headers = ["Name", "Command", "Arguments", "Environment"]
    
    for config in configs:
        # Format args list for display
        args_str = ' '.join(config.args) if config.args else ''
        
        # Format env dict for display
        env_str = ', '.join(f'{k}={v}' for k, v in config.env.items()) if config.env else ''
        
        table_data.append([
            truncate_text(config.name, col_widths["Name"]),
            truncate_text(config.command, col_widths["Command"]),
            truncate_text(args_str, col_widths["Arguments"]),
            truncate_text(env_str, col_widths["Environment"])
        ])
    
    click.echo(tabulate(
        table_data,
        headers=headers,
        tablefmt="simple",
        numalign='left',
        stralign='left'
    ))
