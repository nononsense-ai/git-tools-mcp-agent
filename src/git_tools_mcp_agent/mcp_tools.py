from typing import Any

from git_tools_mcp_client.client import GitToolsClient
from openai.types.chat import ChatCompletionToolUnionParam


class AgentGitToolsClient(GitToolsClient):
    """GitToolsClient plus a generic toold discovery and dispatch for an LLM agent"""

    async def openai_tools(self) -> list[ChatCompletionToolUnionParam]:
        tools = (await self._client.list_tools()).tools
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.input_schema,
                },
            }
            for t in tools
        ]

    async def call_tool(self, name: str, args: dict[str, Any]) -> str:
        return await self._call(name, args)
