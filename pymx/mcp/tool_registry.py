# /your_python_script_folder/tool_registry.py

from mcp.server.fastmcp import FastMCP
import asyncio

# 猴子补丁仍然需要，因为它解决了 sse_starlette 库本身的全局状态问题
# FastMCP 在底层依赖 sse_starlette，所以这个补丁仍然是相关的。
from sse_starlette.sse import AppStatus
AppStatus.should_exit_event = asyncio.Event()


# 1. 初始化 FastMCP 应用
# 我们在这里创建唯一的、共享的 FastMCP 实例。
# 所有工具模块都将从这里导入它，并使用 @mcp.tool 装饰器进行注册。
mcp = FastMCP(
    "mendix-modular-copilot",
    # 我们告诉 FastMCP 使用哪种传输方式，它会据此配置其内部的 Starlette app
    transport="streamable-http"
)