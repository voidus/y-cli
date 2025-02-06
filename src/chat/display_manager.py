import re
from typing import List, Tuple
from .util import get_iso8601_timestamp
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
from rich.live import Live

# Custom theme for role-based colors
custom_theme = Theme({
    "user": "green",
    "assistant": "cyan",
    "system": "yellow",
    "timestamp": "dim white",
})

class DisplayManager:
    def __init__(self):
        self.console = Console(theme=custom_theme, height=None)
        self.code_blocks: List[str] = []

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
        
        # Add model/provider info if available
        model_info = ""
        if 'model' in msg and msg['model']:
            provider = f" [{msg['provider']}]" if 'provider' in msg and msg['provider'] else ""
            model_info = f" [dim][{msg['model']}{provider}][/dim]"

        # Extract content text from structured content if needed
        content = msg['content']
        if isinstance(content, list):
            content = next((part['text'] for part in content if part['type'] == 'text'), '')

        # Process code blocks and update content
        modified_content, code_blocks = self.process_code_blocks(content)
        self.code_blocks.extend(code_blocks)

        # Construct display content with reasoning first
        display_content = ""
        if 'reasoning_content' in msg and msg['reasoning_content']:
            display_content = f"```markdown\n{msg['reasoning_content']}\n```\n"
        display_content += modified_content

        self.console.print(Panel(
            Markdown(display_content),
            title=f"{role} {timestamp}{model_info}",
            border_style=msg['role']
        ))

    async def stream_response(self, response_stream) -> Tuple[str, str]:
        """Stream and display the response in real-time with a live-updating panel.

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
        
        # Create a panel that will be updated with streaming content
        # Cache for Markdown parsing
        last_content = ""
        
        with Live("", console=self.console, refresh_per_second=4, auto_refresh=True, vertical_overflow="visible") as live:
            async for chunk in response_stream:
                delta = chunk.choices[0].delta
                content = delta.content
                reasoning_content = delta.reasoning_content
                if content is not None or reasoning_content is not None:
                    model = chunk.model
                    provider = chunk.provider
                    provider_info = f" [{provider}]" if provider else ""
                    model_info = f" [dim][{model}{provider_info}][/dim]"
                    if content is not None:
                        all_content += content
                        collected_content.append(content)
                    if reasoning_content is not None:
                        all_reasoning_content += reasoning_content
                        collected_reasoning_content.append(reasoning_content)
                    # Construct display content with reasoning first
                    display_content = ""
                    if all_reasoning_content:
                        display_content = f"```markdown\n{all_reasoning_content}\n```\n"
                    display_content += all_content

                    # Only update if content has changed
                    if display_content != last_content:
                        last_content = display_content
                        # Create panel with current content
                        panel = Panel(
                            Markdown(f"{display_content}"),
                            title=f"{role_title} {timestamp_str}{model_info}",
                            border_style="assistant"
                        )
                        live.update(panel)

        return "".join(collected_content), "".join(collected_reasoning_content)

    def display_help(self):
        """Display help information about available commands and features"""
        self.console.print("\n[bold]Enter 'exit' or 'quit' to end the conversation.[/bold]")
        self.console.print("[bold]Enter your message and press Enter to send.[/bold]")
        self.console.print("[bold]For multi-line input:[/bold]")
        self.console.print("  1. Type <<EOF and press Enter")
        self.console.print("  2. Type your multi-line message")
        self.console.print("  3. Type EOF and press Enter to finish")
        self.console.print("[bold]Use 'copy N' to copy code block N, or 'copy 0' to copy the entire last response.[/bold]\n")

    def display_chat_history(self, messages: List[dict]):
        """Display the chat history, skipping system messages"""
        if messages:
            self.console.print("\n[bold]Chat history:[/bold]")
            for msg in messages:
                if msg['role'] == 'system':
                    continue
                self.display_message_panel(msg)
            self.console.print("\n[bold]Continue the conversation:[/bold]")

    def print_error(self, error: str, show_traceback: bool = False):
        """Display an error message with optional traceback"""
        self.console.print(f"\n[red]Error: {error}[/red]\n", err=True)
        if show_traceback and hasattr(error, '__traceback__'):
            import traceback
            self.console.print(f"[red]Detailed error:\n{''.join(traceback.format_tb(error.__traceback__))}[/red]")
