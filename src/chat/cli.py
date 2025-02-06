from typing import Optional
from tabulate import tabulate
import asyncio
import click
import json
import os
from rich.console import Console

from .app import ChatApp, custom_theme
from .config import (
    OPENAI_API_KEY, DATA_FILE, OPENAI_API_BASE, DEFAULT_MODEL,
    TMP_DIR, config
)

@click.group()
def cli():
    """Command-line interface for chat application."""
    if not OPENAI_API_KEY:
        click.echo("Error: OpenAI API key is not set")
        click.echo("Please set it in the config file or OPENAI_API_KEY environment variable")
        raise click.Abort()

@cli.command()
@click.option('--chat-id', '-c', help='Continue from an existing chat')
@click.option('--latest', '-l', is_flag=True, help='Continue from the latest chat')
@click.option('--model', '-m', help=f'OpenAI model to use (default: {DEFAULT_MODEL})')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed usage instructions')
def chat(chat_id: Optional[str], latest: bool, model: Optional[str], verbose: bool):
    """Start a new chat conversation or continue an existing one.

    Use --latest/-l to continue from your most recent chat.
    Use --chat-id/-c to continue from a specific chat ID.
    """
    console = Console(theme=custom_theme)

    # Handle --latest flag
    if latest:
        temp_app = ChatApp()
        chats = temp_app.service.list_chats(limit=1)
        if not chats:
            click.echo("Error: No existing chats found")
            raise click.Abort()
        chat_id = chats[0].id

    if verbose:
        console.print(f"Using file for chat data: {DATA_FILE}")
        console.print(f"Using OpenAI API Base URL: {OPENAI_API_BASE}")
        console.print(f"Using model: {model or DEFAULT_MODEL}")
        if chat_id:
            console.print(f"Continuing from chat {chat_id}")

    chat_app = ChatApp(chat_id, verbose=verbose)
    chat_app.model = model or DEFAULT_MODEL
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
    chat_app = ChatApp()
    chats = chat_app.service.list_chats(keyword=keyword, limit=limit)
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

        # Get source and model from first assistant message if available
        model = "N/A"
        if len(chat.messages) > 1 and chat.messages[1].role == "assistant":
            assistant_msg = chat.messages[1]
            if assistant_msg.model:
                model = assistant_msg.model

        table_data.append([
            chat.id,
            chat.create_time.split("T")[0],
            title,
            full_context,
            model
        ])

    # Print formatted table
    headers = ["ID", "Created Time", "Title", "Full Context", "Model"]
    click.echo(tabulate(
        table_data,
        headers=headers,
        tablefmt="simple",
        maxcolwidths=[6, 10, 30, 60, 20],
        numalign='left',
        stralign='left'
    ))

@cli.command()
@click.option('--chat-id', '-c', help='ID of the chat to share')
@click.option('--latest', '-l', is_flag=True, help='Share the latest chat')
def share(chat_id: Optional[str], latest: bool):
    """Share a chat conversation by generating a shareable link.

    Use --latest/-l to share your most recent chat.
    Use --chat-id/-c to share a specific chat ID.
    """
    if not config["s3_bucket"] or not config["cloudfront_distribution_id"]:
        click.echo("Error: S3 bucket and CloudFront distribution ID must be configured")
        click.echo("Please set S3_BUCKET and CLOUDFRONT_DISTRIBUTION_ID environment variables")
        raise click.Abort()

    chat_app = ChatApp()

    # Handle --latest flag
    if latest:
        chats = chat_app.service.list_chats(limit=1)
        if not chats:
            click.echo("Error: No chats found to share")
            raise click.Abort()
        chat_id = chats[0].id
    elif not chat_id:
        raise click.Abort("Error: Chat ID is required for sharing")

    try:
        # Generate HTML file
        tmp_file = chat_app.service.generate_share_html(chat_id)

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
