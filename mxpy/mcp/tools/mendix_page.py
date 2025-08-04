from mxpy.model.util import TransactionManager
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from pydantic import Field

# 导入包含核心逻辑和 Pydantic 数据模型的模块
from mxpy.model import page as _page
from typing import Annotated
importlib.reload(_page)


@mcp.tool(
    name="ensure_pages",
    description="Ensure page exists, if not create it"
)
async def ensure_mendix_pages(fullPaths: Annotated[list[str], Field(description="A page name to ensure exist, {ModuleName}/{Folder1Name}/{Folder2Name}/{PageName} or {ModuleName}/{PageName}, Module is also a folder")]) -> str:
    report = await _page.ensure_pages(ctx, fullPaths)
    return report