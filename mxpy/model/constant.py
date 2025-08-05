from mxpy.model.util import TransactionManager
import importlib
from typing import List, Literal, Tuple, Optional
from pydantic import BaseModel, Field
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Constants import IConstant  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule, IFolder, IFolderBase  # type: ignore
import clr

from mxpy.model import folder as _folder
importlib.reload(_folder)
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
# 导入所需的Mendix API类

# 导入Pydantic用于数据验证

# region Pydantic Models


class ConstantRequest(BaseModel):
    full_path: str = Field(..., alias="FullPath",
                           description="常量的完整路径。例如：'MyModule/Folders/MyConstant'。第一个是模块名，最后一个是文档（Constant）名，中间可能有若干文件夹")
    data_type: Literal["String", "Boolean", "Integer", "Decimal",
                       "DateTime"] = Field(..., alias="DataType", description="常量的数据类型。")
    default_value: str = Field(..., alias="DefaultValue",
                               description="常量的默认值。")
    exposed_to_client: bool = Field(
        True, alias="ExposedToClient", description="常量是否暴露给客户端。")

    class Config:
        allow_population_by_field_name = True


class CreateConstantsToolInput(BaseModel):
    requests: List[ConstantRequest] = Field(..., description="一个包含待创建常量信息的列表。")
# endregion


# 创建演示数据
def create_demo_input():
    demo_constants = [
        ConstantRequest(
            FullPath="MyFirstModule/API_Key",  # 中间没有文件夹
            DataType="String",
            DefaultValue="sk-demo-api-key-12345",
            ExposedToClient=True
        ),
        ConstantRequest(
            FullPath="MyFirstModule/MyFolder1/MaxRetries",  # 中间有一个文件夹
            DataType="Integer",
            DefaultValue="3",
            ExposedToClient=True
        ),
        ConstantRequest(
            FullPath="MySecondModule/MyFolder1/MyFolder2/IsDebugMode",  # 中间有两个文件夹
            DataType="Boolean",
            DefaultValue="true",
            ExposedToClient=False
        )
    ]
    return CreateConstantsToolInput(requests=demo_constants)


async def create_constants_with_demo(current_app, demo_input: CreateConstantsToolInput):
    """
    遍历请求列表，并使用重构后的 ensure_folder 方法创建常量。
    """
    for request in demo_input.requests:
        # 使用单个事务处理一个常量的创建（包括其文件夹结构）
        with TransactionManager(current_app, f"Create Constant {request.full_path}"):
            try:
                # 确保文件夹路径存在，并获取父容器、文档名和模块名
                parent_container, constant_name, module_name = _folder.ensure_folder(
                    current_app, request.full_path)

                # 如果 ensure_folder 返回 None，说明有错误，跳过此请求
                if parent_container is None:
                    # 错误消息已在 ensure_folder 内部发送
                    continue

                # 检查常量是否已存在
                qName = f'{module_name}.{constant_name}'
                existing_constant = current_app.ToQualifiedName[IConstant](
                    qName).Resolve()
                if existing_constant:
                    continue

                # 创建常量
                constant = current_app.Create[IConstant]()
                constant.Name = constant_name

                # 设置数据类型
                data_type_map = {
                    "String": DataType.String,
                    "Boolean": DataType.Boolean,
                    "Integer": DataType.Integer,
                    "Decimal": DataType.Decimal,
                    "DateTime": DataType.DateTime
                }

                if request.data_type in data_type_map:
                    constant.DataType = data_type_map[request.data_type]
                else:
                    continue

                # 设置默认值和是否暴露给客户端
                constant.DefaultValue = request.default_value
                constant.ExposedToClient = request.exposed_to_client

                # 将常量添加到正确的父容器（IModule 或 IFolder）
                parent_container.AddDocument(constant)

            except Exception as e:
                # 异常将由 TransactionManager 捕获并回滚事务
                # PostMessage 已在 TransactionManager 中处理
                raise
