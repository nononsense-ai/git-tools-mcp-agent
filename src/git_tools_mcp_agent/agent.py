import json
import sys
from typing import cast

from git_tools_mcp_client.exceptions import ClientError
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from git_tools_mcp_agent.mcp_tools import AgentGitToolsClient

SYSTEM_PROMPT = (
    "You are a git assistant. Use the tools to inspect the staged changes "
    "and commit them when asked. Always call git_diff before git_commit and "
    "write a commit message that matches the real changes. "
    "Never invent diff content."
)
DEFAULT_MAX_STEPS = 8


async def dispatch(git: AgentGitToolsClient, name: str, args: dict) -> str:
    try:
        return await git.call_tool(name, args)
    except ClientError as e:
        return f"error: {e}"


async def agent_loop(
    git: AgentGitToolsClient,
    llm: AsyncOpenAI,
    tools: list[ChatCompletionToolUnionParam],
    user_prompt: str,
    model: str,
    max_steps: int,
) -> str:
    messages = cast(
        list[ChatCompletionMessageParam],
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    for _ in range(max_steps):
        resp = await llm.chat.completions.create(
            model=model, messages=messages, tools=tools
        )
        msg = resp.choices[0].message
        messages.append(
            cast(ChatCompletionAssistantMessageParam, msg.model_dump(exclude_none=True))
        )

        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            if call.type != "function":
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": f"error: unsupported tool call type: {call.type}",
                    }
                )
                continue
            try:
                raw = call.function.arguments
                args = json.loads(raw or "{}") if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                result = "error: arguments were not valid JSON"
            else:
                print(f"[tool] {call.function.name}({args})", file=sys.stderr)
                result = await dispatch(git, call.function.name, args)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
    return "stopped: too many steps"
