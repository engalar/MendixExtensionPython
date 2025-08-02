from typing import Annotated
from pydantic import BaseModel, Field

from ..tool_registry import mcp


@mcp.tool()
def echo_tool(text: Annotated[str, Field(description="this is a echo content, it will return by mcp tool")]) -> str:
    """Echo the input text"""
    return text


@mcp.resource("echo://static")
def echo_resource() -> str:
    return "Echo!"


@mcp.resource("echo://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"


@mcp.prompt("echo")
def echo_prompt(text: str) -> str:
    return text
