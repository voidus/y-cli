# y-cli 🚀

A tiny command-line interface chat application that brings AI conversations to your terminal.

## ✨ Features

- 📝 All chat data stored in single JSONL files for easy access and sync
- 💬 Interactive chat interface
- 🤖 Support for multiple bot configurations (any base_url/api_key/model combination). Supported api format type:
  - [OpenAI chat completion streaming format](https://platform.openai.com/docs/api-reference/chat/streaming)
  - [Dify chat-messages streaming format](https://docs.dify.ai/guides/application-publishing/developing-with-apis)
- 🤔 Support for reasoning model
  - [Deepseek-r1 reasoning_content](https://api-docs.deepseek.com/guides/reasoning_model) output print
  - [OpenAI o3-mini reasoning_effort](https://platform.openai.com/docs/guides/reasoning) configuration 
- 🔗 MCP (Model Context Protocol) client support with multiple server configurations

## Demo

### Interactive chat
![interactive-chat](.github/visuals/interactive-chat.png)

### Multiple bot configurations
```
➜  ~ y-cli bot list
Name         API Key      API Type    Base URL                             Model                                Print Speed    Description    OpenRouter Config    MCP Servers    Reasoning Effort
-----------  -----------  ----------  -----------------------------------  -----------------------------------  -------------  -------------  -------------------  -------------  ------------------
default      sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  google/gemini-2.0-flash-001          200            N/A            Yes                  No             N/A
claude       sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  anthropic/claude-3.7-sonnet:beta     60             N/A            Yes                  todo           N/A
o3-mini      sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  openai/o3-mini                       60             N/A            Yes                  No             low
ds-chat      sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  deepseek/deepseek-chat               100            N/A            Yes                  No             N/A
ds-r1        sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  deepseek/deepseek-r1                 100            N/A            Yes                  tavily         N/A
groq-r1-70b  sk-or-v1...  N/A         https://gateway.ai.cloudflare.co...  deepseek/deepseek-r1-distill-lla...  1000           N/A            Yes                  No             N/A
dify-bot     app-2drF...  dify        https://api.dify.ai/v1                                                    60             N/A            No                   No             N/A
```

### Reasoning model & MCP client

![demo](.github/visuals/demo.gif)

[asciicast](https://asciinema.org/a/703255)

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
- `mcp`    Manage MCP server configurations:
  - `add`     Add a new MCP server configuration
  - `list`    List all configured MCP servers
  - `delete`  Delete an MCP server configuration

### Options
- `--help`  Show help message and exit
