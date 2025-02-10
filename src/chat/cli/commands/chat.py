import os
import asyncio
import click
from typing import Optional
from rich.console import Console

from ...app import ChatApp
from ...display_manager import custom_theme
from ...config import (
    API_KEY, MODEL, BASE_URL, config
)
from ...preset_manager import PresetManager

@click.command()
@click.option('--chat-id', '-c', help='Continue from an existing chat')
@click.option('--latest', '-l', is_flag=True, help='Continue from the latest chat')
@click.option('--model', '-m', help=f'OpenRouter model to use (default: {MODEL})')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed usage instructions')
@click.option('--preset', '-p', help='Use specific configuration preset')
def chat(chat_id: Optional[str], latest: bool, model: Optional[str] = None, verbose: bool = False, preset: Optional[str] = None):
    """Start a new chat conversation or continue an existing one.

    Use --latest/-l to continue from your most recent chat.
    Use --chat-id/-c to continue from a specific chat ID.
    If neither option is provided, starts a new chat.
    Use --preset/-p to use a specific configuration preset.
    """
    console = Console(theme=custom_theme)

    # Handle preset if specified
    current_api_key = API_KEY
    current_base_url = BASE_URL
    current_model = model or MODEL

    if preset:
        preset_manager = PresetManager(config["preset_file"])
        preset_config = preset_manager.get_preset(preset)
        if not preset_config:
            click.echo(f"Error: Preset '{preset}' not found")
            raise click.Abort()
        current_api_key = preset_config.api_key
        current_base_url = preset_config.base_url
        current_model = preset_config.model

    # Create a single ChatApp instance for all operations
    chat_app = ChatApp(
        verbose=verbose,
        model=current_model,
        api_key=current_api_key,
        base_url=current_base_url
    )

    # Handle --latest flag
    if latest:
        chats = chat_app.chat_manager.service.list_chats(limit=1)
        if not chats:
            click.echo("Error: No existing chats found")
            raise click.Abort()
        chat_id = chats[0].id
        # Reinitialize ChatApp with the found chat_id
        chat_app = ChatApp(
            chat_id=chat_id,
            verbose=verbose,
            model=current_model,
            api_key=current_api_key,
            base_url=current_base_url
        )

    # Handle --chat-id flag
    elif chat_id:
        # Verify the chat exists
        if not chat_app.chat_manager.service.get_chat(chat_id):
            click.echo(f"Error: Chat with ID {chat_id} not found")
            raise click.Abort()
        # Reinitialize ChatApp with the specified chat_id
        chat_app = ChatApp(
            chat_id=chat_id,
            verbose=verbose,
            model=current_model,
            api_key=current_api_key,
            base_url=current_base_url
        )

    if verbose:
        console.print(f"Using OpenRouter API Base URL: {current_base_url}")
        console.print(f"Using model: {current_model}")
        if preset:
            console.print(f"Using preset: {preset}")
        if chat_id:
            console.print(f"Continuing from chat {chat_id}")
        else:
            console.print("Starting new chat")

    # Override environment variables for this session
    os.environ["OPENROUTER_API_KEY"] = current_api_key
    os.environ["OPENROUTER_BASE_URL"] = current_base_url

    asyncio.run(chat_app.chat())
