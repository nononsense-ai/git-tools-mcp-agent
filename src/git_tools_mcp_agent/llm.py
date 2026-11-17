import os

from git_tools_mcp_client.exceptions import ConfigError
from openai import AsyncOpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ConfigError("OPENROUTER_API_KEY is not set; put it in .env or export it")
    return key


def make_llm() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=get_api_key())
