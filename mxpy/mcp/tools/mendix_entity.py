# https://aistudio.google.com/prompts/1sMNKyk691_cpP-fEn13xt2BRnnif8TXF

from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

# 导入包含核心逻辑和 Pydantic 数据模型的模块
from mxpy.model import entity
importlib.reload(entity)

# --- 工具定义 ---
# @mcp.tool 装饰器将这个函数注册为一个可由 MCP 调用的工具。
# 它遵循了与 mendix_constant.py 相同的模式，将实现细节封装在 model 目录中。

# ctx.messageBoxService.ShowInformation(
    # "示例数据", entity.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="create_entities",
    description="根据请求列表在 Mendix 应用模型中创建或更新一个或多个实体，包括其属性和关联。"
)
async def create_mendix_entities(data: entity.CreateEntitiesToolInput) -> str:
    """
    接收一个包含实体创建请求的列表，并调用核心逻辑来处理它们。
    该函数作为 Mendix 工具和核心业务逻辑之间的桥梁。

    Args:
        data: 一个 CreateEntitiesToolInput 实例，包含了所有待创建实体的信息。

    Returns:
        一个详细的字符串报告，说明了每个请求的处理过程和最终结果。
    """
    # 将整个流程委托给 mxpy.model.entity 模块中的 create_entities 函数。
    # 这种方式将工具的定义（本文件）与具体的实现逻辑（entity.py）解耦。
    # ctx.CurrentApp 提供了对当前 Mendix Studio Pro App 实例的访问。
    report = await entity.create_entities(ctx.CurrentApp, data)
    return report
