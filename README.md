# git-tools-mcp-agent

A command line agent built on the [git-tools-mcp-server](https://github.com/nononsense-ai/git-tools-mcp-server) and its Python client, [git-tools-mcp-client](https://github.com/nononsense-ai/git-tools-mcp-client). You give it a request, an OpenRouter model decides which git tools to call, and the agent prints the model's final answer.

With no prompt, it reads your staged changes and commits them with a message based on the diff.

## How it works

The agent launches the MCP server over stdio, using the command in `mcp.json`, and asks it for its tool list. Each tool's name, description and input schema get converted to the OpenAI function-calling format, so if the server gains a tool later, the agent picks it up without a code change.

Then it loops:

1. Send the conversation to the model.
2. If the model asks for tools, run them through the MCP client and add the results to the conversation.
3. Repeat until the model replies without a tool call, or `--max-steps` runs out.

When a tool fails (an empty commit message, say), the error text goes back to the model and it can try again.

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)
- git
- An [OpenRouter](https://openrouter.ai) API key
- A local clone of the server:

```
git clone https://github.com/nononsense-ai/git-tools-mcp-server.git
```

## Setup

```
uv sync
cp mcp.example.json mcp.json
```

In `mcp.json`, replace `/path/to/git-tools-mcp-server` with the absolute path to your server clone:

```json
{
  "mcpServers": {
    "git-tools": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/git-tools-mcp-server", "git-tools-mcp-server"]
    }
  }
}
```

Put your key in a `.env` file:

```
OPENROUTER_API_KEY=sk-or-...
```

Both files only make sense on your machine, so add them to `.gitignore`.

## Usage

The agent makes real commits. Try it on a scratch repo first:

```
rm -rf /tmp/scratch && mkdir /tmp/scratch && cd /tmp/scratch
git init -q && echo "hello" > a.txt && git add a.txt
cd -

uv run git-tools-mcp-agent --repo /tmp/scratch
uv run git-tools-mcp-agent --repo /tmp/scratch "Show me the diff but don't commit"
```

Tool calls are logged to stderr as `[tool] name(args)`, and the final answer goes to stdout.

| Option | Default | Meaning |
|---|---|---|
| `prompt` | review and commit staged changes | What to ask the agent |
| `--repo` | `.` | Git repo the server works on |
| `--config` | `$GIT_TOOLS_CONFIG`, else `mcp.json` | MCP servers config |
| `--server` | `git-tools` | Server name in the config |
| `--model` | `openrouter/free` | OpenRouter model id |
| `--max-steps` | `8` | Maximum model round trips |
| `--timeout` | `30.0` | Seconds to wait for an MCP response |

Errors print as a single `error: ...` line and exit with code 1.

## Project layout

```
src/git_tools_mcp_agent/
├── __init__.py    re-exports main
├── cli.py         argument parsing and main()
├── llm.py         OpenRouter client and API key check
├── mcp_tools.py   GitToolsClient subclass: tool discovery and generic calls
└── agent.py       system prompt and the agent loop
```

## Known rough edges

`openrouter/free` routes to whichever free model is available, and some of those are poor at tool calling. If the agent loops or sends malformed arguments, pin a model with `--model`. Free models also hit rate limits, so a retry or a different model usually fixes that.

There's no confirmation step before a commit. Point the agent only at repos where you're fine with it committing.
