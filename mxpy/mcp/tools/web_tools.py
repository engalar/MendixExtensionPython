# /your_python_script_folder/tools/web_tools.py

import mcp.types as types
from mcp.shared._httpx_utils import create_mcp_http_client
from tool_registry import mcp # 导入共享的 MCP 实例

# --- 业务逻辑函数 ---
async def fetch_website(url: str) -> list[types.ContentBlock]:
    """一个辅助函数，执行实际的 web 请求。"""
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"
    }
    async with create_mcp_http_client(headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return [types.TextContent(type="text", text=response.text)]

# --- 工具定义 ---
@mcp.tool()
async def fetch(url: str) -> list[types.ContentBlock]:
    """
    获取一个网站并返回其内容。

    这个文档字符串将作为工具的描述。
    参数 `url` 及其类型提示定义了输入模式。

    :param url: 要获取的网站的 URL。
    """
    try:
        return await fetch_website(url)
    except Exception as e:
        # 向 LLM 返回结构化的错误是一个好习惯
        return [types.ErrorContent(type="error", text=f"获取 URL 失败: {str(e)}")]