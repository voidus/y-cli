import os
import sys
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from tabulate import tabulate
import wcwidth
from dotenv import load_dotenv
import openai
import click
import pyperclip
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.live import Live
from rich.text import Text

from .models import Chat, Message
from .repository import ChatRepository
from .service import ChatService
from .config import DATA_FILE, OPENAI_API_KEY, OPENAI_API_BASE, DEFAULT_MODEL
from .util import get_iso8601_timestamp

# Load environment variables
load_dotenv()

# Initialize OpenAI client with custom base URL support
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE
)

# Custom theme for role-based colors
custom_theme = Theme({
    "user": "green",
    "assistant": "cyan",
    "system": "yellow",
    "timestamp": "dim white",
})

class ChatApp:
    def __init__(self, chat_id: Optional[str] = None, verbose: bool = False):
        self.repository = ChatRepository(DATA_FILE)
        self.service = ChatService(self.repository)
        self.current_chat: Optional[Chat] = None
        self.messages: List[Dict[str, str]] = []
        self.console = Console(theme=custom_theme)
        self.code_blocks: List[str] = []  # Store code blocks for copying
        self.verbose = verbose
        
        if chat_id:
            # Load existing chat if chat_id provided
            existing_chat = self.service.get_chat(chat_id)
            if not existing_chat:
                self.console.print(f"[red]Chat {chat_id} not found[/red]", err=True)
                raise click.Abort()
            
            # Convert existing messages to OpenAI API format
            self.messages = [{
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            } for msg in existing_chat.messages]
            self.current_chat = existing_chat
            if self.verbose:
                self.console.print(f"Loaded {len(self.messages)} messages from chat {chat_id}")

    def process_code_blocks(self, content: str) -> Tuple[str, List[str]]:
        """Process code blocks in content, adding sequence numbers and copy instructions.
        
        Returns:
            Tuple of (modified content, list of code blocks for copying)
        """
        code_blocks = []
        start_idx = len(self.code_blocks)
        
        def replace_code_block(match):
            nonlocal start_idx
            lang = match.group(1) or ''
            code = match.group(2).strip()
            block_num = len(code_blocks) + start_idx + 1
            code_blocks.append(code)
            
            # Format with sequence number and copy instruction
            return f"> copy [{block_num}]\n```{lang} {code}\n```"
        
        # Replace code blocks with numbered versions and copy instructions
        pattern = r'```(\w*\n|\n)?(.+?)```'
        modified_content = re.sub(pattern, replace_code_block, content, flags=re.DOTALL)
        
        return modified_content, code_blocks

    def display_message_panel(self, msg: dict):
        """Display a message in a panel with role-colored borders.
        
        Args:
            msg: The message dictionary containing role, content, and timestamp
        """
        timestamp = f"[timestamp]{msg['timestamp']}[/timestamp]"
        role = f"[{msg['role']}]{msg['role'].capitalize()}[/{msg['role']}]"
        
        # Process code blocks and update content
        modified_content, code_blocks = self.process_code_blocks(msg['content'])
        self.code_blocks.extend(code_blocks)
        
        self.console.print(Panel(
            Markdown(modified_content),
            title=f"{role} {timestamp}",
            border_style=msg['role']
        ))
    
    def get_input(self) -> str:
        """Get user input with support for multi-line input using EOF flags.

        Multi-line input starts with <<EOF and ends with EOF. For example:
        <<EOF
        line 1
        line 2
        EOF

        Returns:
            str: The user input, either single line or multiple lines joined with newlines.
        """
        try:
            text = input("Please enter: ").strip()

            # Check for multi-line input start flag
            if text == "<<EOF":
                lines = []
                while True:
                    line = input().rstrip()
                    if line == "EOF":
                        break
                    lines.append(line)
                return "\n".join(lines)

            return text

        except (EOFError, KeyboardInterrupt):
            self.console.print("\n[yellow]Exiting chat...[/yellow]")
            sys.exit(0)

    def stream_response(self, response_stream) -> str:
        collected_messages = []
        current_content = ""
        timestamp = get_iso8601_timestamp()
        role_title = f"[assistant]Assistant[/assistant]"
        timestamp_str = f"[timestamp]{timestamp}[/timestamp]"
        
        # Create a panel that will be updated with streaming content
        with Live("", console=self.console, refresh_per_second=10, auto_refresh=False) as live:
            for chunk in response_stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    current_content += content
                    collected_messages.append(content)
                    
                    # Update panel with current content
                    panel = Panel(
                        Markdown(current_content),
                        title=f"{role_title} {timestamp_str}",
                        border_style="assistant"
                    )
                    live.update(panel)
                    live.refresh()
        
        return "".join(collected_messages)

    def chat(self):
        if self.verbose:
            self.console.print("\n[bold]Enter 'exit' or 'quit' to end the conversation.[/bold]")
            self.console.print("[bold]Enter your message and press Enter to send.[/bold]")
            self.console.print("[bold]For multi-line input:[/bold]")
            self.console.print("  1. Type <<EOF and press Enter")
            self.console.print("  2. Type your multi-line message")
            self.console.print("  3. Type EOF and press Enter to finish")
            self.console.print("[bold]Use 'copy N' to copy code block N, or 'copy 0' to copy the entire last response.[/bold]\n")
        
        # Display existing messages if continuing from a previous chat
        if self.messages:
            self.console.print("\n[bold]Chat history:[/bold]")
            for msg in self.messages:
                self.display_message_panel(msg)
            self.console.print("\n[bold]Continue the conversation:[/bold]")
        
        while True:
            user_input = self.get_input().strip()
            
            if user_input.lower() in ['exit', 'quit']:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            
            if not user_input:
                self.console.print("[yellow]Please enter a message.[/yellow]")
                continue
                
            # Handle copy command
            if user_input.lower().startswith('copy '):
                try:
                    block_num = int(user_input.split()[1])
                    if block_num == 0:
                        # Find last assistant message
                        last_assistant = next((msg for msg in reversed(self.messages) 
                                            if msg['role'] == 'assistant'), None)
                        if last_assistant and last_assistant['content']:
                            pyperclip.copy(last_assistant['content'].strip())
                            self.console.print("[green]Copied last assistant message to clipboard[/green]")
                        else:
                            self.console.print("[yellow]No previous assistant message to copy[/yellow]")
                    elif 1 <= block_num <= len(self.code_blocks):
                        pyperclip.copy(self.code_blocks[block_num - 1])
                        self.console.print(f"[green]Copied code block [{block_num}] to clipboard[/green]")
                    else:
                        self.console.print("[yellow]Invalid code block number[/yellow]")
                    continue
                except (IndexError, ValueError):
                    self.console.print("[yellow]Invalid copy command. Use 'copy <number>' or 'copy 0' for last message[/yellow]")
                    continue
            # Add user message to history and persist
            user_message = {"role": "user", "content": user_input, "timestamp": get_iso8601_timestamp()}
            self.messages.append(user_message)

            # clear user_input using ANSI escape sequences
            sys.stdout.write("\033[F")  # Cursor up one line

            # display user message
            self.display_message_panel(user_message)
            
            try:
                # Get streaming response from OpenAI
                response = client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    stream=True
                )
                
                # Stream and collect assistant's response
                assistant_response = self.stream_response(response)
                
                # Add assistant response to history and persist
                assistant_message = {
                    "role": "assistant", 
                    "content": assistant_response,
                    "timestamp": get_iso8601_timestamp(),
                    "model": self.model
                }
                self.messages.append(assistant_message)

                # Persist chat if needed
                if not self.current_chat:
                    self.current_chat = self.service.create_chat(self.messages)
                else:
                    self.current_chat = self.service.update_chat(self.current_chat.id, self.messages)
                
            except openai.APIError as e:
                self.console.print(f"\n[red]Error: {str(e)}[/red]\n", err=True)
            except Exception as e:
                self.console.print(f"\n[red]Unexpected error: {str(e)}[/red]\n", err=True)

@click.group()
def cli():
    """Command-line interface for chat application."""
    if not OPENAI_API_KEY:
        click.echo("Error: OpenAI API key is not set")
        click.echo("Please set it in the config file or OPENAI_API_KEY environment variable")
        raise click.Abort()

@cli.command()
@click.option('--chat-id', help='Continue from an existing chat')
@click.option('--model', help=f'OpenAI model to use (default: {DEFAULT_MODEL})')
@click.option('--verbose', is_flag=True, help='Show detailed usage instructions')
def chat(chat_id: Optional[str], model: Optional[str], verbose: bool):
    """Start a new chat conversation, optionally continuing from an existing chat."""
    console = Console(theme=custom_theme)
    if verbose:
        console.print(f"Using file for chat data: {DATA_FILE}")
        console.print(f"Using OpenAI API Base URL: {OPENAI_API_BASE}")
        console.print(f"Using model: {model or DEFAULT_MODEL}")
        if chat_id:
            console.print(f"Continuing from chat {chat_id}")
    chat_app = ChatApp(chat_id, verbose=verbose)
    chat_app.model = model or DEFAULT_MODEL
    chat_app.chat()

@cli.command()
@click.option('--keyword', help='Filter chats by message content')
@click.option('--limit', default=10, help='Maximum number of chats to show (default: 10)')
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

if __name__ == "__main__":
    cli()
