from mxpy.model.util import TransactionManager
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from pydantic import Field

# 导入包含核心逻辑和 Pydantic 数据模型的模块
from mxpy.model import module as _module
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
