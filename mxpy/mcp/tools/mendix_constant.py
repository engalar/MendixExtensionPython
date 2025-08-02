from .. import mendix_context as ctx  # 使用别名以方便访问
from ..tool_registry import mcp
import importlib
from pydantic import BaseModel, Field
from typing import List, Literal

# 从顶层安全导入
from Mendix.StudioPro.ExtensionsAPI.Model.Constants import IConstant  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule, IFolder  # type: ignore
from mxpy.model import constant
# from mxpy.model.constant import CreateConstantsToolInput, create_constants_with_demo

importlib.reload(constant)

# 导入共享的 MCP 实例和 Mendix 上下文


# --- 工具定义 ---
@mcp.tool(name="create_constants", description="根据请求列表在 Mendix 应用模型中创建一个或多个常量。如果指定路径的常量已存在，则会跳过创建。")
async def create_mendix_constants(data: constant.CreateConstantsToolInput) -> str:
    await constant.create_constants_with_demo(ctx.CurrentApp, data)
    return '创建完成'
