# /your_python_script_folder/main.py

# --- 只保留绝对安全的顶层导入 ---
import importlib
from .mendix_context import set_mendix_services
import anyio
import sys
import clr
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")

# --- 导入我们自己的模块 ---
# 注意：这些导入放在这里，以便在 C# 调用之前不执行任何复杂逻辑。

# --- 提供给 C# 的同步入口点 ---


def run_server_blocking(
    freePort,
    CurrentApp,
    messageBoxService,
    extensionFileService,
    microflowActivititesService,
    microflowExpressionService,
    microflowService,
    untypedModelAccessService
):
    """
    这是 C# 调用的唯一函数。
    它是一个同步的、阻塞的函数，封装了所有异步的复杂性。
    """

    try:
        # 1. 设置全局 Mendix 上下文，以便所有工具都能访问
        set_mendix_services(
            CurrentApp,
            messageBoxService,
            extensionFileService,
            microflowActivititesService,
            microflowExpressionService,
            microflowService,
            untypedModelAccessService
        )
        from mxpy.mcp import server
        importlib.reload(server)

        # 2. 运行异步服务器
        # anyio.run 将创建、运行和销毁它自己的事件循环，并阻塞直到 run_async_server 完成。
        anyio.run(server.run_async_server, freePort)

    except Exception as e:
        import traceback
        error_message = f"Python: 在顶层发生未处理的异常。\n"
        error_message += f"类型: {type(e).__name__}\n"
        error_message += f"消息: {e}\n"
        error_message += f"回溯:\n{traceback.format_exc()}"
        if messageBoxService:
            messageBoxService.ShowInformation(error_message)
        else:
            print(error_message, file=sys.stderr)
