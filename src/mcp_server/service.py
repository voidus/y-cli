from typing import List, Optional
from .models import McpServerConfig
from .repository import McpServerConfigRepository

class McpServerConfigService:
    """Service for managing MCP config business logic"""
    
    @property
    def default_config(self) -> McpServerConfig:
        """Get the default MCP server configuration"""
        return McpServerConfig(
            name="todo",
            command="uvx",
            args=["mcp-todo"],
            env={}
        )
    
    def __init__(self, repository: McpServerConfigRepository):
        """
        Initialize the service with a repository
        
        Args:
            repository (McpServerConfigRepository): Repository for MCP config persistence
        """
        self.repository = repository
        self._ensure_default_config()
        
    def _ensure_default_config(self):
        """Ensure the default MCP server configuration exists"""
        if not self.get_config("todo"):
            self.create_config(
                name=self.default_config.name,
                command=self.default_config.command,
                args=self.default_config.args,
                env=self.default_config.env
            )
    
    def get_all_configs(self) -> List[McpServerConfig]:
        """
        Get all MCP config
        
        Returns:
            List[McpServerConfig]: List of all MCP config
        """
        return self.repository.load()
        
    def get_config(self, name: str) -> Optional[McpServerConfig]:
        """
        Get a specific MCP setting by name
        
        Args:
            name (str): Name of the MCP server
            
        Returns:
            Optional[McpServerConfig]: The MCP setting if found, None otherwise
        """
        return self.repository.get_by_name(name)
        
    def create_config(
        self,
        name: str,
        command: str,
        args: List[str],
        env: dict[str, str]
    ) -> bool:
        """
        Create a new MCP setting
        
        Args:
            name (str): Name of the MCP server
            command (str): Command to execute the server
            args (List[str]): Command line arguments
            env (dict[str, str]): Environment variables
            
        Returns:
            bool: True if creation was successful, False otherwise
        """
        setting = McpServerConfig(name=name, command=command, args=args, env=env)
        return self.repository.add_or_update(setting)
        
    def update_config(self, setting: McpServerConfig) -> bool:
        """
        Update an existing MCP setting
        
        Args:
            setting (McpServerConfig): The MCP setting to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        return self.repository.add_or_update(setting)
        
    def delete_config(self, name: str) -> bool:
        """
        Delete an MCP setting
        
        Args:
            name (str): Name of the MCP server to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        return self.repository.remove(name)
