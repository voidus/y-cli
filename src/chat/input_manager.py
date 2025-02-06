import sys
import pyperclip
from typing import List, Optional, Tuple
from prompt_toolkit import prompt
from rich.console import Console

class InputManager:
    def __init__(self, console: Console):
        self.console = console

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
        text = prompt('请输入: ', in_thread=True)
        text = text.rstrip()

        # Check for multi-line input start flag
        if text == "<<EOF":
            lines = []
            while True:
                line = prompt(in_thread=True)
                line = line.rstrip()
                if line == "EOF":
                    break
                lines.append(line)
            return "\n".join(lines)

        return text

    def handle_copy_command(self, command: str, code_blocks: List[str], last_assistant_message: Optional[str]) -> bool:
        """Handle the copy command for code blocks or last message.

        Args:
            command: The copy command (e.g., 'copy 1' or 'copy 0')
            code_blocks: List of available code blocks
            last_assistant_message: Content of the last assistant message

        Returns:
            bool: True if command was handled, False otherwise
        """
        try:
            block_num = int(command.split()[1])
            if block_num == 0:
                if last_assistant_message:
                    pyperclip.copy(last_assistant_message.strip())
                    self.console.print("[green]Copied last assistant message to clipboard[/green]")
                else:
                    self.console.print("[yellow]No previous assistant message to copy[/yellow]")
            elif 1 <= block_num <= len(code_blocks):
                pyperclip.copy(code_blocks[block_num - 1])
                self.console.print(f"[green]Copied code block [{block_num}] to clipboard[/green]")
            else:
                self.console.print("[yellow]Invalid code block number[/yellow]")
            return True
        except (IndexError, ValueError):
            self.console.print("[yellow]Invalid copy command. Use 'copy <number>' or 'copy 0' for last message[/yellow]")
            return True

    def is_exit_command(self, text: str) -> bool:
        """Check if the input is an exit command.

        Args:
            text: The input text to check

        Returns:
            bool: True if the input is an exit command, False otherwise
        """
        return text.lower() in ['exit', 'quit']

    def clear_input_line(self):
        """Clear the current input line using ANSI escape sequences"""
        sys.stdout.write("\033[F")  # Cursor up one line
