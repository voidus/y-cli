import re
from typing import List, Tuple, Optional
from .models import Message
from .util import get_iso8601_timestamp
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.live import Live
from collections import deque
import sys

# Custom theme for role-based colors
custom_theme = Theme({
    "user": "green",
    "assistant": "cyan",
    "system": "yellow",
    "timestamp": "dim white",
})

class DisplayManager:
    def __init__(self):
        self.console = Console(theme=custom_theme)

    def display_message_panel(self, message: Message, index: Optional[int] = None):
        """Display a message in a panel with role-colored borders.

        Args:
            message: The Message object containing role, content, and other attributes
            index: Optional index of the message in the chat history
        """
        timestamp = f"[timestamp]{message.timestamp}[/timestamp]"
        role = f"[{message.role}]{message.role.capitalize()}[/{message.role}]"
        index_str = f"[{index}] " if index is not None else ""

        # Add model/provider info if available
        model_info = ""
        if message.model:
            provider = f" [{message.provider}]" if message.provider else ""
            model_info = f" [dim][{message.model}{provider}][/dim]"

        # Extract content text from structured content if needed
        content = message.content
        if isinstance(content, list):
            content = next((part['text'] for part in content if part['type'] == 'text'), '')

        # Construct display content with reasoning first
        display_content = ""
        if message.reasoning_content:
            display_content = f"```markdown\n{message.reasoning_content}\n```\n"
        display_content += content

        self.console.print(Panel(
            Markdown(display_content),
            title=f"{index_str}{role} {timestamp}{model_info}",
            border_style=message.role
        ))

    async def stream_response(self, response_stream) -> Tuple[str, str]:
        """Stream and display the response in real-time, showing content in a temporary panel
        that updates during streaming.

        Args:
            response_stream: The streaming response from OpenRouter API

        Returns:
            Tuple[str, str]: A tuple containing (complete response text, reasoning text)
        """
        all_content = ""
        all_reasoning_content = ""
        collected_content = []
        collected_reasoning_content = []
        timestamp = get_iso8601_timestamp()
        role_title = f"[assistant]Assistant[/assistant]"
        timestamp_str = f"[timestamp]{timestamp}[/timestamp]"
        model_info = ""
        max_lines = self.console.height - 7
        content_buffer = deque(maxlen=max_lines)

        is_reasoning = False
        with Live(console=self.console) as live:
            async for chunk in response_stream:
                delta = chunk.choices[0].delta
                content = delta.content
                reasoning_content = delta.reasoning_content
                new_content = ""
                if reasoning_content:
                    # start reasoning block
                    if not is_reasoning:
                        is_reasoning = True
                        new_content += "```markdown\n"
                    new_content += reasoning_content
                    all_reasoning_content += reasoning_content
                    collected_reasoning_content.append(reasoning_content)
                # end reasoning block
                if is_reasoning and not reasoning_content:
                    new_content += "```\n"
                    is_reasoning = False
                if content:
                    new_content += content
                    all_content += content
                    collected_content.append(content)
                if new_content:
                    if not content_buffer:
                        content_buffer.append(new_content)
                    else:
                        if '\n' in new_content:
                            # if start with newline, extend all split lines
                            if new_content.startswith('\n'):
                                content_buffer.extend(new_content.split('\n'))
                            else:
                                # else last item merge first line and extend the rest
                                part, *rest = new_content.split('\n')
                                content_buffer[-1] += part
                                content_buffer.extend(rest)
                        else:
                            # Append to last line
                            content_buffer[-1] += new_content

                    # title info
                    model = chunk.model
                    provider = chunk.provider
                    provider_info = f" [{provider}]" if provider else ""
                    model_info = f" [dim][{model}{provider_info}][/dim]"

                    # Join buffer lines and wrap in panel
                    panel = Panel(
                        Markdown("\n".join(content_buffer)),
                        title=f"{role_title} {timestamp_str}{model_info}",
                        border_style="assistant"
                    )
                    live.update(panel)
            live.update("")

        self.clear_lines(1)

        return "".join(collected_content), "".join(collected_reasoning_content)

    def display_help(self):
        """Display help information about available commands and features"""
        help_content = """
[bold]Available Commands:[/bold]

• Enter 'exit' or 'quit' to end the conversation
• Enter your message and press Enter to send

[bold]Multi-line Input:[/bold]
1. Type <<EOF and press Enter
2. Type your multi-line message
3. Type EOF and press Enter to finish

[bold]Message Copying:[/bold]
• Messages are indexed starting from 0
• Use 'copy n' to copy message n (e.g., 'copy 0' for first message)
"""
        self.console.print(Panel(
            Markdown(help_content),
            title="[bold]Help Information[/bold]",
            border_style="yellow"
        ))

    def display_chat_history(self, messages: List[Message]):
        """Display the chat history, skipping system messages"""
        if messages:
            history_messages = [msg for msg in messages if msg.role != 'system']
            if history_messages:
                for i, message in enumerate(history_messages):
                    self.display_message_panel(message, index=i)
                self.console.print(Panel(
                    "[bold]Type your message to continue the conversation[/bold]",
                    border_style="yellow"
                ))

    def print_error(self, error: str, show_traceback: bool = False):
        """Display an error message with optional traceback in a panel"""
        error_content = f"[red]{error}[/red]"
        if show_traceback and hasattr(error, '__traceback__'):
            import traceback
            error_content += f"\n\n[red]Detailed error:\n{''.join(traceback.format_tb(error.__traceback__))}[/red]"

        self.console.print(Panel(
            Markdown(error_content),
            title="[red]Error[/red]",
            border_style="red"
        ))

    def clear_lines(self, lines: int):
        """Clear the specified number of lines using ANSI escape sequences

        Args:
            lines: Number of lines to clear
        """
        for _ in range(lines):
            sys.stdout.write("\033[F")   # Cursor up one line
