import os
import toml

def get_default_config():
    """Get default configuration"""
    return {
        "data_file": "~/.local/share/chat/chat.jsonl",
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "default_model": os.getenv("MODEL", "gpt-3.5-turbo")
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
    PROXY_HOST = config["proxy_host"]
    PROXY_PORT = config["proxy_port"]
    if PROXY_HOST and PROXY_PORT:
        os.environ["http_proxy"] = f"http://{PROXY_HOST}:{PROXY_PORT}"
        os.environ["https_proxy"] = f"http://{PROXY_HOST}:{PROXY_PORT}"

    return config, DATA_FILE

config, DATA_FILE = load_config()

# Export OpenAI configuration
OPENAI_API_KEY = config["openai_api_key"]
OPENAI_API_BASE = config["openai_base_url"]
DEFAULT_MODEL = config["default_model"]
