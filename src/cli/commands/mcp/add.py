import click
from typing import List

from mcp_server.models import McpServerConfig
from mcp_server.service import McpServerConfigService
from mcp_server.repository import McpServerConfigRepository

@click.command('add')
def mcp_add():
    """Add a new MCP server configuration."""
    from config import config
    # Initialize repository and service
    repository = McpServerConfigRepository(config['mcp_config_file'])
    service = McpServerConfigService(repository)
    
    # Get server name
    name = click.prompt("Server name")
    
    # Check if server already exists
    existing_config = service.get_config(name)
    if existing_config:
        if not click.confirm(f"MCP server '{name}' already exists. Do you want to overwrite it?"):
            click.echo("Operation cancelled")
            return
    
    # Get command
    command = click.prompt("Command (e.g., 'node', 'python')")
    
    # Get arguments as a space-separated string and convert to list
    args_str = click.prompt("Arguments (space-separated)", default="")
    args = args_str.split() if args_str else []
    
    # Get environment variables
    env = {}
    while True:
        if not click.confirm("Add environment variable?", default=False):
            break
        key = click.prompt("Environment variable name")
        value = click.prompt("Environment variable value")
        env[key] = value
    
    # Create new config
    config = McpServerConfig(
        name=name,
        command=command,
        args=args,
        env=env
    )
    
    # Save the config
    if service.create_config(
        name=config.name,
        command=config.command,
        args=config.args,
        env=config.env
    ):
        click.echo(f"MCP server '{name}' added successfully")
    else:
        click.echo(f"Failed to add MCP server '{name}'")
