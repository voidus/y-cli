import os
import toml
import json

# Default MCP settings content
DEFAULT_MCP_SETTINGS = {
    "mcpServers": {
        "todo": {
            "command": "uvx",
            "args": ["mcp-todo"]
        }
    }
}

# Default OpenRouter config content
DEFAULT_OPENROUTER_CONFIG = {
    "config": {
        "provider": {
            "sort": "throughput"
        }
    }
}

def get_default_config():
    """Get default configuration"""
    return {
        "data_file": "~/.local/share/y-cli/chat.jsonl",
        "openrouter_config_file": "~/.config/y-cli/openrouter_config.json",
        "mcp_settings_file": "~/.config/y-cli/mcp_settings.json",
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3.5-sonnet:beta",
        "openrouter_import_dir": "~/.local/share/y-cli/openrouter_import",
        "openrouter_import_history": "~/.local/share/y-cli/openrouter_import_history.jsonl",
        "tmp_dir": "~/.local/share/y-cli/tmp",
        "s3_bucket": os.getenv("S3_BUCKET", ""),
        "cloudfront_distribution_id": os.getenv("CLOUDFRONT_DISTRIBUTION_ID", "")
    }

def load_config():
    """Load configuration from TOML file or create with defaults if it doesn't exist"""
    # toml config file
    CONFIG_FILE = os.path.expanduser("~/.config/y-cli/config.toml")
    # ensure the directory exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

    # Create default config if file doesn't exist
    if not os.path.exists(CONFIG_FILE):
        config = get_default_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            toml.dump(config, f)
    else:
        # read existing config file
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = toml.load(f)
            # Merge with defaults to ensure all required fields exist
            defaults = get_default_config()
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value

    DATA_FILE = os.path.expanduser(config["data_file"])
    # ensure the directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Create default MCP settings file if it doesn't exist
    MCP_SETTINGS_FILE = os.path.expanduser(config["mcp_settings_file"])
    os.makedirs(os.path.dirname(MCP_SETTINGS_FILE), exist_ok=True)
    if not os.path.exists(MCP_SETTINGS_FILE):
        with open(MCP_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_MCP_SETTINGS, f, indent=2)

    # Create default OpenRouter config file if it doesn't exist
    OPENROUTER_CONFIG_FILE = os.path.expanduser(config["openrouter_config_file"])
    os.makedirs(os.path.dirname(OPENROUTER_CONFIG_FILE), exist_ok=True)
    if not os.path.exists(OPENROUTER_CONFIG_FILE):
        with open(OPENROUTER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_OPENROUTER_CONFIG, f, indent=2)

    # network proxy settings
    PROXY_HOST = config.get("proxy_host")
    PROXY_PORT = config.get("proxy_port")
    if PROXY_HOST and PROXY_PORT:
        os.environ["http_proxy"] = f"http://{PROXY_HOST}:{PROXY_PORT}"
        os.environ["https_proxy"] = f"http://{PROXY_HOST}:{PROXY_PORT}"

    return config, DATA_FILE

config, DATA_FILE = load_config()

# Export OpenRouter configuration
OPENROUTER_API_KEY = config["openrouter_api_key"]
OPENROUTER_API_BASE = config["openrouter_base_url"]
DEFAULT_MODEL = config["default_model"]
OPENROUTER_IMPORT_DIR = os.path.expanduser(config["openrouter_import_dir"])
OPENROUTER_IMPORT_HISTORY = os.path.expanduser(config["openrouter_import_history"])
MCP_SETTINGS_FILE = os.path.expanduser(config["mcp_settings_file"])
OPENROUTER_CONFIG_FILE = os.path.expanduser(config["openrouter_config_file"])
TMP_DIR = os.path.expanduser(config["tmp_dir"])
os.makedirs(TMP_DIR, exist_ok=True)
