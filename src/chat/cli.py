from typing import Optional
from tabulate import tabulate
import asyncio
import click
import json
import os
from rich.console import Console

from .app import ChatApp
from .display_manager import custom_theme
from .config import (
    OPENROUTER_API_KEY, DATA_FILE, OPENROUTER_API_BASE, DEFAULT_MODEL,
    TMP_DIR, config
)

@click.group()
def cli():
    """Command-line interface for chat application."""
    # Skip API key check for init command
    if click.get_current_context().invoked_subcommand != 'init' and not OPENROUTER_API_KEY:
        click.echo("Error: OpenRouter API key is not set")
        click.echo("Please set it using 'y-cli init' or set OPENROUTER_API_KEY environment variable")
        raise click.Abort()

@cli.command()
def init():
    """Initialize y-cli configuration with required settings.

    Creates a config file at ~/.config/y-cli/config.toml and prompts for required settings.
    """
    import toml
    from .config import get_default_config

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
    if OPENROUTER_API_KEY:
        click.echo("OpenRouter API key is already set in environment")
        config["openrouter_api_key"] = OPENROUTER_API_KEY
    else:
        # Prompt for OpenRouter API key
        api_key = click.prompt(
            "Please enter your OpenRouter API key",
            type=str,
            default=config.get("openrouter_api_key", ""),
            show_default=False
        )
        # Update config with new API key
        config["openrouter_api_key"] = api_key

    # Write updated config
    with open(config_file, "w") as f:
        toml.dump(config, f)

    click.echo(f"\nConfiguration saved to: {config_file}")
    click.echo(f"Chat data will be stored in: {os.path.expanduser(config['data_file'])}")
    click.echo("\nOptional settings that can be edited in the config file:")
    click.echo("- default_model: The default model to use for chat")
    click.echo("- openrouter_base_url: OpenRouter API base URL")
    click.echo("- proxy_host/proxy_port: Network proxy settings")
    click.echo("- s3_bucket/cloudfront_distribution_id: For sharing chats")

@cli.command()
@click.option('--chat-id', '-c', help='Continue from an existing chat')
@click.option('--latest', '-l', is_flag=True, help='Continue from the latest chat')
@click.option('--model', '-m', help=f'OpenRouter model to use (default: {DEFAULT_MODEL})')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed usage instructions')
def chat(chat_id: Optional[str], latest: bool, model: Optional[str] = None, verbose: bool = False):
    """Start a new chat conversation or continue an existing one.

    Use --latest/-l to continue from your most recent chat.
    Use --chat-id/-c to continue from a specific chat ID.
    If neither option is provided, starts a new chat.
    """
    console = Console(theme=custom_theme)

    # if not model
    if not model:
        model = DEFAULT_MODEL

    # Create a single ChatApp instance for all operations
    chat_app = ChatApp(verbose=verbose, model=model)

    # Handle --latest flag
    if latest:
        chats = chat_app.chat_manager.service.list_chats(limit=1)
        if not chats:
            click.echo("Error: No existing chats found")
            raise click.Abort()
        chat_id = chats[0].id
        # Reinitialize ChatApp with the found chat_id
        chat_app = ChatApp(chat_id=chat_id, verbose=verbose, model=model)

    # Handle --chat-id flag
    elif chat_id:
        # Verify the chat exists
        if not chat_app.chat_manager.service.get_chat(chat_id):
            click.echo(f"Error: Chat with ID {chat_id} not found")
            raise click.Abort()
        # Reinitialize ChatApp with the specified chat_id
        chat_app = ChatApp(chat_id=chat_id, verbose=verbose, model=model)

    if verbose:
        console.print(f"Using file for chat data: {DATA_FILE}")
        console.print(f"Using OpenRouter API Base URL: {OPENROUTER_API_BASE}")
        console.print(f"Using model: {model or DEFAULT_MODEL}")
        if chat_id:
            console.print(f"Continuing from chat {chat_id}")
        else:
            console.print("Starting new chat")

    asyncio.run(chat_app.chat())

@cli.command()
@click.option('--keyword', '-k', help='Filter chats by message content')
@click.option('--limit', '-l', default=10, help='Maximum number of chats to show (default: 10)')
def list(keyword: Optional[str], limit: int):
    """List chat conversations with optional filtering.

    Shows chats sorted by creation time (newest first).
    Use --keyword to filter by message content.
    Use --limit to control the number of results.
    """
    chat_app = ChatApp(model=None)
    chats = chat_app.chat_manager.service.list_chats(keyword=keyword, limit=limit)
    if not chats:
        if keyword:
            click.echo(f"No chats found matching keyword: {keyword}")
        else:
            click.echo("No chats found")
        return

    # Prepare table data
    table_data = []
    for chat in chats:
        # Get title from first message if available
        if chat.messages:
            title = chat.messages[0].content[:100]
            if len(chat.messages[0].content) > 100:
                title += "..."
        else:
            title = "No messages"

        # Get full context by joining all message contents
        full_context = " | ".join(f"{m.role}: {m.content}" for m in chat.messages)
        if len(full_context) > 100:
            full_context = full_context[:97] + "..."

        # Get provider and model from last assistant message if available
        model = "N/A"
        provider = "N/A"
        # Search messages in reverse to find the last assistant message
        for msg in reversed(chat.messages):
            if msg.role == "assistant":
                if msg.model:
                    model = msg.model
                if msg.provider:
                    provider = msg.provider
                break

        table_data.append([
            chat.id,
            chat.create_time.split("T")[0],
            title,
            full_context,
            model,
            provider
        ])

    # Print formatted table
    headers = ["ID", "Created Time", "Title", "Full Context", "Model", "Provider"]
    click.echo(tabulate(
        table_data,
        headers=headers,
        tablefmt="simple",
        maxcolwidths=[6, 10, 30, 50, 15, 15],
        numalign='left',
        stralign='left'
    ))

@cli.command()
@click.option('--chat-id', '-c', help='ID of the chat to share')
@click.option('--latest', '-l', is_flag=True, help='Share the latest chat')
@click.option('--push', '-p', is_flag=True, help='Push to S3 after generating HTML')
def share(chat_id: Optional[str], latest: bool, push: bool):
    """Share a chat conversation.

    Use --latest/-l to share your most recent chat.
    Use --chat-id/-c to share a specific chat ID.
    """

    chat_app = ChatApp(model=None)

    # Handle --latest flag
    if latest:
        chats = chat_app.chat_manager.service.list_chats(limit=1)
        if not chats:
            click.echo("Error: No chats found to share")
            raise click.Abort()
        chat_id = chats[0].id
    elif not chat_id:
        raise click.Abort("Error: Chat ID is required for sharing")

    try:
        # Generate HTML file
        tmp_file = chat_app.chat_manager.service.generate_share_html(chat_id)

        if push and (not config["s3_bucket"] or not config["cloudfront_distribution_id"]):
            click.echo("Error: S3 bucket and CloudFront distribution ID must be configured")
            click.echo("Please set S3_BUCKET and CLOUDFRONT_DISTRIBUTION_ID environment variables")
            raise click.Abort()

        # Always open the HTML file
        os.system(f'open "{tmp_file}"')

        if push:
            # Upload to S3
            os.system(f'aws s3 cp "{tmp_file}" s3://{config["s3_bucket"]}/chat/{chat_id}.html > /dev/null')

            # Invalidate CloudFront cache
            os.system(f'aws cloudfront create-invalidation --distribution-id {config["cloudfront_distribution_id"]} --paths "/chat/{chat_id}.html" > /dev/null')

            # Print the shareable URL
            click.echo(f'https://{config["s3_bucket"]}/chat/{chat_id}.html')

    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        raise click.Abort()

if __name__ == "__main__":
    cli()
