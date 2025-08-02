# /your_python_script_folder/tools/mendix_tools.py

from pydantic import BaseModel, Field
from typing import List, Literal

# 从顶层安全导入
from Mendix.StudioPro.ExtensionsAPI.Model.Constants import IConstant
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType
from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule, IFolder

# 导入共享的 MCP 实例和 Mendix 上下文
from ..tool_registry import mcp
from .. import mendix_context as ctx # 使用别名以方便访问


# --- Pydantic 输入模型 ---
class ConstantRequest(BaseModel):
    full_path: str = Field(..., alias="FullPath", description="常量的完整路径。例如：'MyModule/Folders/MyConstant'。")
    data_type: Literal["String", "Boolean", "Integer", "Decimal", "DateTime"] = Field(..., alias="DataType", description="常量的数据类型。")
    default_value: str = Field(..., alias="DefaultValue", description="常量的默认值。")
    exposed_to_client: bool = Field(True, alias="ExposedToClient", description="常量是否暴露给客户端。")

    class Config:
        allow_population_by_field_name = True

class CreateConstantsToolInput(BaseModel):
    requests: List[ConstantRequest] = Field(..., description="一个包含待创建常量信息的列表。")


# --- 工具定义 ---
@mcp.tool(name="create_constants")
async def create_mendix_constants(data: CreateConstantsToolInput) -> str:
    """
    根据请求列表在 Mendix 应用模型中创建一个或多个常量。
    如果指定路径的常量已存在，则会跳过创建。
    """
    results = []
    # 从 mendix_context 模块访问 CurrentApp
    transaction = ctx.CurrentApp.StartTransaction("Create Constants via Tool")
    need_commit = True

    for req in data.requests:
        try:
            path_parts = req.full_path.replace("\\", "/").strip("/").split("/")
            if len(path_parts) < 2:
                results.append(f"错误 '{req.full_path}': 无效路径。")
                continue

            module_name, constant_name = path_parts[0], path_parts[-1]
            folder_path_parts = path_parts[1:-1] if len(path_parts) > 2 else []

            module = next((m for m in ctx.CurrentApp.Root.GetModules() if m.Name == module_name), None)
            if not module:
                module = ctx.CurrentApp.Create[IModule]()
                module.Name = module_name
                results.append(f"信息: 已创建模块 '{module_name}'。")

            parent_folder = module
            for part in folder_path_parts:
                next_folder = next((f for f in parent_folder.GetFolders() if f.Name == part), None)
                if not next_folder:
                    next_folder = ctx.CurrentApp.Create[IFolder]()
                    next_folder.Name = part
                    parent_folder.AddFolder(next_folder)
                parent_folder = next_folder

            qualified_name = f"{module_name}.{constant_name}"
            if ctx.CurrentApp.ToQualifiedName[IConstant](qualified_name).Resolve():
                results.append(f"信息: 常量 '{qualified_name}' 已存在，已跳过。")
                continue

            new_constant = ctx.CurrentApp.Create[IConstant]()
            new_constant.Name = constant_name
            new_constant.ExposedToClient = req.exposed_to_client
            
            # (省略了数据类型设置的详细代码，与原始版本相同)
            # ...
            if req.data_type == "String":
                new_constant.DataType = DataType.String
                new_constant.DefaultValue = req.default_value
            # ... (其他类型)
            
            parent_folder.AddDocument(new_constant)
            results.append(f"成功: 已创建常量 '{qualified_name}'。")

        except Exception as e:
            results.append(f"失败 '{req.full_path}': {e}")
            need_commit = False

    if need_commit:
        transaction.Commit()
    else:
        transaction.Rollback()
    transaction.Dispose()
    return "\n".join(results)