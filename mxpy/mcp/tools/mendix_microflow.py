# mendix_microflow.py

from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

from mxpy.model import microflow
importlib.reload(microflow)

# 取消下面的注释以显示输入数据结构的 JSON 示例
# ctx.messageBoxService.ShowInformation(
    # "Sample Data", microflow.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="ensure_microflows",
    description="根据请求列表在 Mendix 应用模型中创建或更新一个或多个微流，包括其参数和返回类型。"
)
async def create_mendix_microflows(data: microflow.CreateMicroflowsToolInput) -> str:
    """
    接收一个包含微流创建请求的列表，并调用核心逻辑来处理它们。
    该函数作为 Mendix 工具定义和核心业务逻辑之间的桥梁。

    Args:
        data: 一个 CreateMicroflowsToolInput 实例。该实例是一个 Pydantic 模型，
              它被设计为可以直接从 C# 端发送的 JSON 数组请求体进行解析，
              包含了所有待创建微流的信息。

    Returns:
        一个详细的字符串报告，说明了每个请求的处理过程和最终结果。
    """
    # 将整个流程委托给 mxpy.model.microflow 模块中的 create_microflows 函数。
    # 这种方式将工具的定义（本文件）与具体的实现逻辑（microflow.py）解耦。
    # ctx.CurrentApp 提供了对当前 Mendix Studio Pro App 实例的访问。
    report = await microflow.create_microflows(ctx, data)
    return report
