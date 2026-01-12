from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from typing import List

# 导入包含枚举核心逻辑和 Pydantic 数据模型的模块
from pymx.model import enum
importlib.reload(enum)

# --- 工具定义 ---
# @mcp.tool 装饰器将这个函数注册为一个可由 MCP 调用的工具。
# 它遵循了将工具定义与实现分离的模式，核心逻辑位于 pymx.model 目录中。

# 取消下面的注释以显示输入数据结构的 JSON 示例
# ctx.messageBoxService.ShowInformation(
#     "Sample Data", enum.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="create_enumerations",
    description="根据请求列表，在 Mendix 应用模型中创建或更新一个或多个枚举，包括它们的值。"
)
async def create_mendix_enumerations(requests: List[enum.EnumerationRequest]) -> str:
    report = await enum.create_enumerations(ctx.CurrentApp, requests)
    return report
