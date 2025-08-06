
import traceback
import clr
from System import ValueTuple, String  # type: ignore
import importlib
from pymx.model.util import TransactionManager
from pymx.model import folder as _folder
from pymx.model import module as _module
from pymx.model.dto import type_microflow
from typing import Optional
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows import (  # type: ignore
    IMicroflow, MicroflowReturnValue
)
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import IEntity  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration  # type: ignore
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")


# 确保所有依赖的模块都是最新的
importlib.reload(_module)
importlib.reload(_folder)
importlib.reload(type_microflow)


def _create_data_type(current_app, type_info: type_microflow.DataTypeDefinition) -> Optional[DataType]:
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


async def create_microflows(ctx, tool_input: type_microflow.CreateMicroflowsToolInput) -> str:
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
                        return_type_obj, microflowExpressionService.CreateFromString(request.return_exp)) if request.return_exp else None
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
