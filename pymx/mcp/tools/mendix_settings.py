# mendix_settings.py

from pymx.model.dto import type_settings
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

from pymx.model import settings
importlib.reload(settings)
importlib.reload(type_settings)

# 取消下面的注释以显示输入数据结构的 JSON 示例
# ctx.messageBoxService.ShowInformation(
    # "Sample Data", type_settings.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="ensure_settings",
    description="根据请求在 Mendix 应用模型中创建或更新配置设置，包括常量和自定义设置。"
)
async def create_mendix_settings(data: type_settings.SettingsRequest) -> str:
    """
    接收一个设置创建请求，并调用核心逻辑来处理它。
    该函数作为 Mendix 工具定义和核心业务逻辑之间的桥梁。

    Args:
        data: 一个 SettingsRequest 实例。该实例是一个 Pydantic 模型，
              它被设计为可以直接从 C# 端发送的 JSON 请求体进行解析，
              包含了所有待创建设置的信息。

    Returns:
        一个详细的字符串报告，说明了请求的处理过程和最终结果。
    """
    # 将整个流程委托给 pymx.model.settings 模块中的 create_settings 函数。
    # 这种方式将工具的定义（本文件）与具体的实现逻辑（settings.py）解耦。
    # ctx.CurrentApp 提供了对当前 Mendix Studio Pro App 实例的访问。
    importlib.reload(settings)  # temp reload in dev mode
    report = await settings.create_settings(ctx, data)
    return report
