import os
import click
import toml

from ...config import API_KEY, get_default_config

@click.command()
def init():
    """Initialize y-cli configuration with required settings.

    Creates a config file at ~/.config/y-cli/config.toml and prompts for required settings.
    """
    # Get config file path
    config_file = os.path.expanduser("~/.config/y-cli/config.toml")

    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(config_file), exist_ok=True)

    # Load existing config or get defaults
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = toml.load(f)
    else:
        config = get_default_config()

    # Check if API key is already set in environment
    if API_KEY:
        click.echo("OpenRouter API key is already set in environment")
        config["api_key"] = API_KEY
    else:
        # Prompt for OpenRouter API key
        api_key = click.prompt(
            "Please enter your OpenRouter API key",
            type=str,
            default=config.get("api_key", ""),
            show_default=False
        )
        # Update config with new API key
        config["api_key"] = api_key

    # Write updated config
    with open(config_file, "w") as f:
        toml.dump(config, f)

    click.echo(f"\nConfiguration saved to: {config_file}")
    click.echo(f"Chat data will be stored in: {os.path.expanduser(config['data_file'])}")
    click.echo("\nOptional settings that can be edited in the config file:")
    click.echo("- model: The default model to use for chat")
    click.echo("- base_url: OpenRouter API base URL")
    click.echo("- proxy_host/proxy_port: Network proxy settings")
    click.echo("- s3_bucket/cloudfront_distribution_id: For sharing chats")
