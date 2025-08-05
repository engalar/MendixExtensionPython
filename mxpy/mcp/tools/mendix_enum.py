from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

# 导入包含枚举核心逻辑和 Pydantic 数据模型的模块
from mxpy.model import enum
importlib.reload(enum)

# --- 工具定义 ---
# @mcp.tool 装饰器将这个函数注册为一个可由 MCP 调用的工具。
# 它遵循了将工具定义与实现分离的模式，核心逻辑位于 mxpy.model 目录中。

# 取消下面的注释以显示输入数据结构的 JSON 示例
# ctx.messageBoxService.ShowInformation(
#     "Sample Data", enum.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="create_enumerations",
    description="根据请求列表，在 Mendix 应用模型中创建或更新一个或多个枚举，包括它们的值。"
)
async def create_mendix_enumerations(data: enum.CreateEnumerationsToolInput) -> str:
    """
    接收一个包含枚举创建请求的列表，并调用核心逻辑来处理它们。
    该函数作为 Mendix 工具和核心业务逻辑之间的桥梁。

    Args:
        data: 一个 CreateEnumerationsToolInput 实例，包含了所有待创建枚举的信息。

    Returns:
        一个详细的字符串报告，说明了每个请求的处理过程和最终结果。
    """
    # 将整个流程委托给 mxpy.model.enum 模块中的 create_enumerations 函数。
    # 这种方式将工具的定义（本文件）与具体的实现逻辑（enum.py）解耦。
    # ctx.CurrentApp 提供了对当前 Mendix Studio Pro App 实例的访问。
    report = await enum.create_enumerations(ctx.CurrentApp, data)
    return report
