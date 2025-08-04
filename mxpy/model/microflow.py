
import clr
from System import ValueTuple, String
import importlib
from mxpy.model.util import TransactionManager
from mxpy.model import folder as _folder
from mxpy.model import module as _module
from typing import List, Literal, Optional, Self
from pydantic import BaseModel, Field, model_validator, field_validator
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows import (  # type: ignore
    IMicroflow, MicroflowReturnValue
)
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import IEntity # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration # type: ignore
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
import traceback


# 确保所有依赖的模块都是最新的
importlib.reload(_module)
importlib.reload(_folder)


# region Pydantic Models for Microflow Creation

# 这些模型严格遵循 MicroflowTools.cs 中定义的 JSON Schema

class DataTypeDefinition(BaseModel):
    """定义一个 Mendix 数据类型。"""
    type_name: Literal[
        "Enumeration", "Decimal", "Binary", "Boolean", "DateTime",
        "Integer", "Long", "String", "Void", "Object", "List"
    ] = Field(..., alias="TypeName", description="Mendix 数据类型名称。")
    qualified_name: Optional[str] = Field(
        None, alias="QualifiedName",
        description="当类型为 Object, List 或 Enumeration 时，需要提供其限定名 (例如 'MyModule.MyEntity')。")

    class Config:
        allow_population_by_field_name = True

    @model_validator(mode='after')
    def check_qualified_name_is_present(self) -> Self:
        """验证需要限定名的类型是否已提供。"""
        if self.type_name in ("Object", "List", "Enumeration") and not self.qualified_name:
            raise ValueError(
                f"'{self.type_name}' 类型需要一个 'QualifiedName'。")
        if self.type_name not in ("Object", "List", "Enumeration") and self.qualified_name:
            raise ValueError(
                f"'{self.type_name}' 类型不应提供 'QualifiedName'。")
        return self


class MicroflowParameter(BaseModel):
    """定义一个微流参数。"""
    name: str = Field(..., alias="Name", description="参数的名称。")
    type: DataTypeDefinition = Field(
        ..., alias="Type", description="参数的数据类型。")

    class Config:
        allow_population_by_field_name = True


class MicroflowRequest(BaseModel):
    """定义一个创建微流的完整请求。"""
    full_path: str = Field(..., alias="FullPath",
                           description="微流的完整路径，例如 'MyModule/SubFolder/MyMicroflow'。")
    return_type: DataTypeDefinition = Field(
        ..., alias="ReturnType", description="微流的返回类型。")
    return_exp: Optional[str] = Field(
        None, alias="ReturnExp", description="返回表达式。")
    parameters: List[MicroflowParameter] = Field(
        [], alias="Parameters", description="微流的参数列表。")

    class Config:
        allow_population_by_field_name = True

    @field_validator('full_path')
    def validate_full_path(cls, v: str):
        if not v or len(v.split('/')) < 2:
            raise ValueError(
                "FullPath 必须至少包含 'ModuleName/MicroflowName'。")
        return v


class CreateMicroflowsToolInput(BaseModel):
    """该工具的根输入模型，包含一个请求列表。"""
    requests: List[MicroflowRequest]

# endregion


def create_demo_input() -> CreateMicroflowsToolInput:
    """创建一个示例输入对象，用于演示。"""
    demo_requests = [
        MicroflowRequest(
            FullPath="MyFirstModule/Folder1/Folder2/MyMicroflow",
            ReturnType=DataTypeDefinition(TypeName="String"),
            ReturnExp="'Hello, World!'",
            Parameters=[
                MicroflowParameter(
                    Name="param1", Type=DataTypeDefinition(TypeName="String")),
                MicroflowParameter(Name="param2", Type=DataTypeDefinition(
                    TypeName="Enumeration", QualifiedName="System.DeviceType")),
                MicroflowParameter(
                    Name="param3", Type=DataTypeDefinition(TypeName="DateTime")),
                MicroflowParameter(Name="param4", Type=DataTypeDefinition(
                    TypeName="List", QualifiedName="System.User"))
            ]
        ),
        MicroflowRequest(
            FullPath="MySecondModule/MyMicroflow",
            ReturnType=DataTypeDefinition(TypeName="Void"),
            Parameters=[
                MicroflowParameter(
                    Name="param1", Type=DataTypeDefinition(TypeName="Integer"))
            ]
        ),
    ]
    return CreateMicroflowsToolInput(requests=demo_requests)


def _create_data_type(current_app, type_info: DataTypeDefinition) -> Optional[DataType]:
    type_name = type_info.type_name.lower()

    if type_name == "string":
        return DataType.String
    if type_name == "integer":
        return DataType.Integer
    if type_name == "long":
        return DataType.Long
    if type_name == "decimal":
        return DataType.Decimal
    if type_name == "boolean":
        return DataType.Boolean
    if type_name == "datetime":
        return DataType.DateTime
    if type_name == "binary":
        return DataType.Binary
    if type_name == "void":
        return DataType.Void
    if type_name == "object":
        return DataType.Object(current_app.ToQualifiedName[IEntity](type_info.qualified_name))
    if type_name == "list":
        return DataType.List(current_app.ToQualifiedName[IEntity](type_info.qualified_name))
    if type_name == "enumeration":
        return DataType.Enumeration(current_app.ToQualifiedName[IEnumeration](type_info.qualified_name))
    raise ValueError(f"不支持的数据类型 '{type_name}'。")


async def create_microflows(ctx, tool_input: CreateMicroflowsToolInput) -> str:
    """
    遍历微流创建请求，创建或更新它们，并返回一个纯文本报告。
    """
    report_lines = ["开始微流创建流程..."]
    success_count = 0
    failure_count = 0
    current_app = ctx.CurrentApp
    microflowActivititesService = ctx.microflowActivititesService
    microflowExpressionService = ctx.microflowExpressionService
    microflowService = ctx.microflowService
    for i, request in enumerate(tool_input.requests):
        report_lines.append(
            f"\n--- 处理请求 {i+1}/{len(tool_input.requests)}: {request.full_path} ---")

        try:
            with TransactionManager(current_app, f"创建/更新微流 {request.full_path}"):
                # 1. 确保文件夹路径存在并获取父容器和微流名称
                parent_container, mf_name, module_name = _folder.ensure_folder(
                    current_app, request.full_path)

                if not parent_container or not mf_name or not module_name:
                    raise ValueError(f"无效的路径: '{request.full_path}'")

                report_lines.append(f"- 模块 '{module_name}' 和文件夹路径已确保存在。")

                # 2. 查找或创建微流
                mf = next((m for m in parent_container.GetDocuments()
                          if m.Name == mf_name), None)

                # 3. 设置返回类型
                params = [
                    ValueTuple.Create[String, DataType](param.name, _create_data_type(current_app, param.type)) for param in request.parameters]
                return_type_obj = _create_data_type(
                    current_app, request.return_type)
                term = ('<'+request.return_type.qualified_name +
                        '>') if request.return_type.qualified_name else ''
                type_str = f'{request.return_type.type_name}{term}'
                if not return_type_obj:
                    # _create_data_type 返回的错误消息已经很清晰
                    raise ValueError(type_str)
                if not mf:
                    # option 1: 创建微流
                    # mf = current_app.Create[IMicroflow]()
                    # mf.Name = mf_name
                    # parent_container.AddDocument(mf)

                    # option 2: create use service
                    # or create use service
                    microflowReturnValue = MicroflowReturnValue(
                        return_type_obj, microflowExpressionService.CreateFromString(request.return_exp))
                    mf = microflowService.CreateMicroflow(
                        current_app, parent_container, mf_name, microflowReturnValue, params)
                    report_lines.append(
                        f"- [SUCCESS] 微流 '{module_name}.{mf_name}' 已创建。")
                else:
                    existingMicroflow = current_app.ToQualifiedName[IMicroflow](
                        f'{module_name}.{mf_name}').Resolve()
                    if existingMicroflow and existingMicroflow.Id == mf.Id:  # 确保 ID 不变
                        mf = existingMicroflow
                        report_lines.append(
                            f"- [INFO] 微流 '{mf.QualifiedName}' 已存在，将进行更新...")
                        mf.ReturnType = return_type_obj
                        microflowService.Initialize(mf, params)
                    else:
                        raise ValueError(
                            f"[ERROR] 找到同名微流 '{mf.QualifiedName}', 但 ID 不同。请检查输入。")
                mf.ReturnVariableName = 'result'
                report_lines.append(
                    f"- [SUCCESS] 返回类型已设置为: {type_str}。")

                # 4. 更新参数 (为简单起见，先清空再添加)
                report_lines.append("- 处理参数 (清除现有参数后重新添加):")
                if not request.parameters:
                    report_lines.append("  - [INFO] 无参数需要添加。")

            # 如果事务成功提交
            report_lines.append(
                f"[SUCCESS] 针对 '{request.full_path}' 的事务已提交。")
            success_count += 1

        except Exception as e:
            # TransactionManager 会自动回滚
            report_lines.append(
                f"[ERROR] 处理 '{request.full_path}' 失败: {e}")
            # traceback
            report_lines.append(traceback.format_exc())
            report_lines.append("[INFO] 事务已回滚。")
            failure_count += 1
            continue  # 继续处理下一个请求

    # 最终总结
    report_lines.append("\n\n--- 最终总结 ---")
    report_lines.append(
        f"总共处理请求数: {len(tool_input.requests)}")
    report_lines.append(f"成功: {success_count}")
    report_lines.append(f"失败: {failure_count}")
    report_lines.append("---------------------")

    return "\n".join(report_lines)
