# y-cli 🚀

A tiny command-line interface chat application that brings AI conversations to your terminal.

## ✨ Features

- 📝 All chat data stored in single JSONL files for easy access and sync
- 💬 Interactive chat interface
- 🤖 Support for multiple bot configurations (any base_url/api_key/model combination compatible with [OpenAI chat completion streaming format](https://platform.openai.com/docs/api-reference/chat/streaming))
- 🤔 Deepseek-r1 reasoning content support for enhanced AI responses
- 🔗 MCP (Model Context Protocol) client support with multiple server configurations

## Demo

### Interactive chat
![interactive-chat](.github/visuals/interactive-chat.png)

### Multiple bot configurations
```
➜  ~ y-cli bot list
Name     API Key      Base URL             Model                Print Speed    Description    OpenRouter Config    MCP Servers
-------  -----------  -------------------  -------------------  -------------  -------------  -------------------  -------------
default  sk-or-v1...  https://gateway....  anthropic/claude...  60             N/A            Yes                  todo, tavily
gemini   sk-or-v1...  https://gateway....  google/gemini-2....  60             N/A            Yes                  No
ds-chat  sk-or-v1...  https://gateway....  deepseek/deepsee...  60             N/A            Yes                  No
ds-r1    sk-or-v1...  https://gateway....  deepseek/deepsee...  60             N/A            Yes                  No
qc-r1    QC-3cce2...  https://maas.qc-...  DeepSeek-R1          60             N/A            No                   No
```

### Reasoning content
![r1](.github/visuals/r1.gif)

[asciicast](https://asciinema.org/a/702204)

### MCP client
![mcp](.github/visuals/mcp.gif)

[asciicast](https://asciinema.org/a/702199)

### Multiple MCP servers
```
➜  ~ y-cli mcp list
Name    Command    Arguments                                Environment
------  ---------  ---------------------------------------  ---------------------------------------
todo    uvx        mcp-todo
tavily  npx        -y tavily-mcp                            TAVILY_API_KEY=tvly-api-key...
pplx    node       /Users/mac/src/researcher-mcp/build/...  PERPLEXITY_API_KEY=pplx-api-key...
```

## ⚡ Quick Start

### Prerequisites

Required:
1. uv
2. OpenRouter API key

Setup Instructions:
1. **uv**
   - Follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/)
   - uv will automatically manage Python installation

2. **OpenRouter API key**
   - Visit [OpenRouter Settings](https://openrouter.ai/settings/keys)
   - Create a new API key
   - Save it for the initialization step

### Run without Installation
```bash
uvx y-cli
```

### Install with uv tool
```bash
uv tool install y-cli
```

### Initialize
```bash
y-cli init
```

### Start Chat
```bash
y-cli chat
```

## 🛠️ Usage

```bash
y-cli [OPTIONS] COMMAND [ARGS]...
```

### Commands
- `chat`   Start a new chat conversation or continue an existing one
- `list`   List chat conversations with optional filtering
- `share`  Share a chat conversation by generating a shareable link
- `bot`    Manage bot configurations:
  - `add`     Add a new bot configuration
  - `list`    List all configured bots
  - `delete`  Delete a bot configuration

### Options
- `--help`  Show help message and exit
