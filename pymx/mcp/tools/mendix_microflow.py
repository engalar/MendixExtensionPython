from typing import List, Literal, Optional, Set, Union, Any, Annotated
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

from pymx.model import microflow
importlib.reload(microflow)
from pymx.model.dto import type_microflow
importlib.reload(type_microflow)

# 取消下面的注释以显示输入数据结构的 JSON 示例
# ctx.messageBoxService.ShowInformation(
    # "Sample Data", microflow.create_demo_input().model_dump_json(by_alias=True, indent=4))


@mcp.tool(
    name="ensure_microflows",
    description="根据请求列表在 Mendix 应用模型中创建或更新一个或多个微流，包括其参数和返回类型。"
)
async def create_mendix_microflows(requests: List[type_microflow.MicroflowRequest]) -> str:
    report = microflow.create_microflows(ctx, requests)
    return report
