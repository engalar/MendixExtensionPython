from pymx.model.util import TransactionManager
from pymx.mcp import mendix_context as ctx
from pymx.mcp.tool_registry import mcp
import importlib
from pydantic import Field

# 导入包含核心逻辑和 Pydantic 数据模型的模块
from pymx.ide import editor as _editor
from typing import Annotated


@mcp.tool(
    name="open_document",
    description="open specific document in studio pro"
)
async def open_document(qualifiedName: Annotated[str, Field(description="qulified name of the document to open")]
                        # , elementName: Annotated[str, Field(description='element name to focus after document open')]
                        ) -> str:
    importlib.reload(_editor)
    success, reports = _editor.open_document(ctx, qualifiedName, None)
    return "\n".join(reports)
