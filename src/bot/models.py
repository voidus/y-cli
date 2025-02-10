"""Bot configuration models."""

from dataclasses import dataclass, asdict, field
from typing import Dict, Optional

DEFAULT_OPENROUTER_SETTINGS = {
    "provider": {
        "sort": "throughput"
    }
}

DEFAULT_MCP_SERVER_SETTINGS = {
    "todo": {
        "command": "uvx",
        "args": ["mcp-todo"]
    }
}

@dataclass
class BotConfig:
    name: str
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    model: str = "anthropic/claude-3.5-sonnet:beta"
    print_speed: int = 60
    description: Optional[str] = None
    openrouter_config: Optional[Dict] = field(default_factory=lambda: DEFAULT_OPENROUTER_SETTINGS.copy())
    mcp_server_settings: Optional[Dict] = field(default_factory=lambda: DEFAULT_MCP_SERVER_SETTINGS.copy())

    @classmethod
    def from_dict(cls, data: Dict) -> 'BotConfig':
        return cls(**data)

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}
