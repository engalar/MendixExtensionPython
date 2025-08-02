import mcp.types as types
from ..tool_registry import mcp


@mcp.tool()
async def echo(content: str) -> str:
    """
    echo your content
    """
    return content
