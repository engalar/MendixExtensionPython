from pymx.model.util import TransactionManager
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from pydantic import Field

from pymx.mcp import mendix_context as ctx
# 导入包含核心逻辑和 Pydantic 数据模型的模块
from pymx.model import module as _module
from typing import Annotated
importlib.reload(_module)


@mcp.tool(
    name="ensure_modules",
    description="Ensure module exists, if not create it"
)
async def ensure_mendix_modules(names: Annotated[list[str], Field(description="A module name to ensure exist")]) -> str:
    with TransactionManager(ctx.CurrentApp, 'ensure list module exist') as tx:
        for name in names:
            _module.ensure_module(ctx.CurrentApp, name)
    return 'ensure success'


@mcp.resource("model://project", description="mendix project info include module name", mime_type="application/json")
def model_project_resource() -> str:
    """mendix project info"""
    reports = []
    modules = ctx.CurrentApp.Root.GetModules()
    for module in modules:
        reports.append(module.Name)
    return reports
    # return "\n".join(reports)


@mcp.resource("model://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"
