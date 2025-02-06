import os
import toml

def get_default_config():
    """Get default configuration"""
    return {
        "data_file": "~/.local/share/chat/chat.jsonl",
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv("OPENROUTER_API_BASE", "https://api.openrouter.com/v1"),
        "default_model": os.getenv("MODEL", "anthropic/claude-3.5-sonnet:beta"),
        "openrouter_import_dir": "~/.local/share/chat/openrouter_import",
        "openrouter_import_history": "~/.local/share/chat/openrouter_import_history.jsonl",
        "openrouter_config_file": "~/.config/chat/openrouter_config.json",
        "mcp_settings_file": "~/.config/chat/mcp_settings.json",
        "tmp_dir": "~/.local/share/chat/tmp",
        "s3_bucket": os.getenv("S3_BUCKET", ""),
        "cloudfront_distribution_id": os.getenv("CLOUDFRONT_DISTRIBUTION_ID", "")
    }

def load_config():
    """Load configuration from TOML file or create with defaults if it doesn't exist"""
    # toml config file
    CONFIG_FILE = os.path.expanduser("~/.config/chat/config.toml")
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
