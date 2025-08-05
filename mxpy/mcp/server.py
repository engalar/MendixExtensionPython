# /your_python_script_folder/server.py

import asyncio
import importlib
import anyio
import uvicorn
import contextlib
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route, Mount

from . import mendix_context as ctx


async def run_async_server(freePort: int):
    """
    异步主函数，配置并运行 uvicorn 服务器。
    """

    from mxpy.mcp import tool_registry
    importlib.reload(tool_registry)
    # 关键：导入 'tools' 包以触发 __init__.py 中的动态加载
    from . import tools
    importlib.reload(tools)

    mcp = tool_registry.mcp
    
    # pretty json output
    # ts = await mcp.list_tools()
    # import json
    # jsonString = json.dumps([t.inputSchema for t in ts], indent=4)
    # ctx.messageBoxService.ShowInformation(
    #     f"MCP Loaded {len(ts)} tools ", f"{jsonString}")

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        """管理 MCP 会话的生命周期。"""
        async with mcp.session_manager.run():
            yield

    def create_shutdown_handler(server_instance: uvicorn.Server):
        async def handle_shutdown(request):
            # ctx.messageBoxService.ShowInformation("Python: 收到来自 C# 的关闭请求。")
            server_instance.should_exit = True
            return Response(content="服务器正在关闭...", status_code=200)
        return handle_shutdown

    # Uvicorn 服务器配置
    config = uvicorn.Config(app=None, host="127.0.0.1", port=freePort,
                            log_config=None, timeout_graceful_shutdown=0)
    server = uvicorn.Server(config)

    # 创建主 Starlette 应用
    main_app = Starlette(
        debug=True,
        routes=[
            Route("/shutdown", endpoint=create_shutdown_handler(server),
                  methods=["POST"]),
            # 关键：将 FastMCP 的 ASGI 应用挂载到主应用上。
            # mcp.streamable_http_app() 包含了所有已注册工具的路由。
            Mount("/", app=mcp.streamable_http_app())
        ],
        lifespan=lifespan,
    )

    config.app = main_app

    ctx.messageBoxService.ShowInformation(
        f"Python: 正在启动服务器 http://127.0.0.1:{freePort}")
    await server.serve()
    ctx.messageBoxService.ShowInformation("Python: 服务器已关闭。")

    return 0
