from mxpy.model.util import TransactionManager
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from pydantic import Field

# 导入包含核心逻辑和 Pydantic 数据模型的模块
from mxpy.model import folder as _folder
from typing import Annotated
importlib.reload(_folder)


@mcp.tool(
    name="create_folders",
    description="Ensure folder exists, if not create it"
)
async def create_mendix_folders(fullPaths: Annotated[list[str], Field(description="A folder name to ensure exist, {ModuleName}/{Folder1Name}/{Folder2Name} or {ModuleName}/{Folder1Name}, Module is also a folder")]) -> str:
    with TransactionManager(ctx.CurrentApp, 'create list folder') as tx:
        for path in fullPaths:
            _folder.ensure_folder(ctx.CurrentApp, path+'/_')
    return 'create success'
