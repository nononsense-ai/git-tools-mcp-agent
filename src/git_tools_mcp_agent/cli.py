import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from git_tools_mcp_client.config import load_params, resolve_repo
from git_tools_mcp_client.exceptions import ClientError
from openai import OpenAIError

from git_tools_mcp_agent.agent import DEFAULT_MAX_STEPS, agent_loop
from git_tools_mcp_agent.llm import DEFAULT_MODEL, make_llm
from git_tools_mcp_agent.mcp_tools import AgentGitToolsClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="git-tools-mcp-agent",
        description="LLM agent that uses the git tools mcp server",
    )
    p.add_argument(
        "prompt",
        nargs="?",
        default="Review my staged changes and commit them with a good message",
        help="what to ask the agent (default: review and commit staged changes)",
    )
    p.add_argument(
        "--repo", type=Path, default=Path("."), help="git repo to operate on"
    )
    p.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("GIT_TOOLS_CONFIG", "mcp.json")),
        help="MCP servers config (default: $GIT_TOOLS_CONFIG, else mcp.json)",
    )
    p.add_argument("--server", default="git-tools", help="server name in the config")
    p.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter model id")
    p.add_argument(
        "--max-steps", type=int, default=DEFAULT_MAX_STEPS, help="max LLM round trips"
    )
    p.add_argument(
        "--timeout", type=float, default=30.0, help="MCP request timeout in seconds"
    )
    return p.parse_args()


async def run(args: argparse.Namespace) -> None:
    llm = make_llm()
    params = load_params(args.config, args.server, resolve_repo(args.repo))

    async with AgentGitToolsClient(params) as git:
        tools = await git.openai_tools()
        print(
            await agent_loop(git, llm, tools, args.prompt, args.model, args.max_steps)
        )


def main() -> None:
    load_dotenv()
    args = parse_args()
    try:
        asyncio.run(run(args))
    except* (ClientError, OSError, OpenAIError) as eg:
        for e in eg.exceptions:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
