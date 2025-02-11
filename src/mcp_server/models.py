from typing import Dict, List

class McpServerConfig:
    """
    Configuration class for MCP (Model Context Protocol) server settings.
    
    Attributes:
        name (str): The name of the MCP server
        command (str): The command to execute the server (e.g., 'node', 'python')
        args (list[str]): Command line arguments for the server
        env (dict[str, str]): Environment variables for the server process
    """
    
    def __init__(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Dict[str, str]
    ):
        self.name = name
        self.command = command
        self.args = args
        self.env = env
