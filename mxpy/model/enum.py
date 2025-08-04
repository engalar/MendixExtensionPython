from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration, IEnumerationValue  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Images import IImage  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Texts import IText  # type: ignore
from pydantic import BaseModel, Field
from typing import List, Optional

import clr
import importlib
import traceback

from mxpy.model import folder as _folder
from mxpy.model.util import TransactionManager

importlib.reload(_folder)
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")

# region Pydantic Models for Enumeration Creation


class EnumValue(BaseModel):
    """定义了枚举值的结构。"""
    name: str = Field(..., alias="Name", description="枚举值的键/开发者名称。")
    caption: str = Field(..., alias="Caption", description="面向用户的枚举值标题。")
    image_qualified_name: Optional[str] = Field(
        None, alias="ImageQualifiedName", description="与此值关联的图像的限定名称。")

    class Config:
        allow_population_by_field_name = True


class EnumerationRequest(BaseModel):
    """定义了创建单个枚举的完整请求。"""
    full_path: str = Field(..., alias="FullPath",
                           description="枚举的完整路径，例如 'MyModule.MyEnumeration' 或 'MyModule/SubFolder/MyEnumeration'。")
    values: List[EnumValue] = Field(..., alias="Values", description="枚举值的列表。")

    class Config:
        allow_population_by_field_name = True


class CreateEnumerationsToolInput(BaseModel):
    """用于创建多个枚举的工具的根模型。"""
    requests: List[EnumerationRequest]

# endregion


def create_demo_input() -> CreateEnumerationsToolInput:
    """为演示目的创建示例输入对象。"""
    demo_requests = [
        EnumerationRequest(
            FullPath="MyFirstModule/OrderStatus",
            Values=[
                EnumValue(Name="Pending", Caption="Pending Review"),
                EnumValue(Name="Shipped", Caption="Shipped to Customer"),
                EnumValue(Name="Delivered", Caption="Delivered"),
                EnumValue(Name="Cancelled", Caption="Cancelled"),
            ]
        ),
        EnumerationRequest(
            FullPath="MyFirstModule/Ratings/StarRating",
            Values=[
                EnumValue(Name="OneStar", Caption="1 Star"),
                EnumValue(Name="TwoStars", Caption="2 Stars",
                          ImageQualifiedName="Atlas_Core.Content.Mendix"),
                EnumValue(Name="ThreeStars", Caption="3 Stars"),
                # 重复项以测试跳过逻辑
                EnumValue(Name="ThreeStars", Caption="3 Stars"),
            ]
        )
    ]
    return CreateEnumerationsToolInput(requests=demo_requests)


async def create_enumerations(current_app, tool_input: CreateEnumerationsToolInput) -> str:
    """
    遍历枚举请求，创建/更新它们，并返回纯文本报告。
    """
    report_lines = ["Starting enumeration creation process..."]
    success_count = 0
    failure_count = 0

    for i, request in enumerate(tool_input.requests):
        report_lines.append(
            f"\n--- Processing Request {i+1}/{len(tool_input.requests)}: {request.full_path} ---")

        try:
            with TransactionManager(current_app, f"Create/Update Enumeration {request.full_path}"):
                # 1. 确保文件夹结构存在并获取父容器
                full_path = request.full_path
                parent_container, doc_name, module_name = _folder.ensure_folder(
                    current_app, full_path)

                if not parent_container or not doc_name:
                    raise ValueError(
                        f"Could not determine parent folder or document name from path '{full_path}'.")

                report_lines.append(
                    f"- Module '{module_name}' ensured and folder structure verified.")

                # 2. 查找或创建枚举
                enum = next(
                    (e for e in parent_container.GetDocuments() if e.Name == doc_name), None)

                if not enum:
                    enum = current_app.Create[IEnumeration]()
                    enum.Name = doc_name
                    parent_container.AddDocument(enum)
                    report_lines.append(
                        f"- [SUCCESS] Enumeration '{enum.QualifiedName}' created.")
                else:
                    # i need get the sub class of IDocument a.k.a. IEnumeration
                    enum = current_app.ToQualifiedName[IEnumeration](
                        f'{module_name}.{doc_name}').Resolve()
                    # maybe it has a same name document not IEnumeration
                    if enum:
                        report_lines.append(
                            f"- [INFO] Enumeration '{enum.QualifiedName}' already exists. Updating...")
                    else:
                        report_lines.append(
                            f"- [ERROR] Document '{doc_name}' exists but is not an enumeration. Skipping...")

                # 3. 添加枚举值
                report_lines.append("- Processing values:")
                existing_value_names = {v.Name.lower()
                                        for v in enum.GetValues()}

                for val_info in request.values:
                    if val_info.name.lower() in existing_value_names:
                        report_lines.append(
                            f"  - [SKIPPED] Value '{val_info.name}' already exists.")
                        continue

                    new_value = current_app.Create[IEnumerationValue]()
                    new_value.Name = val_info.name
                    caption = current_app.Create[IText]()
                    # 假设默认语言为 en_US
                    caption.AddOrUpdateTranslation("en_US", val_info.caption)
                    new_value.Caption = caption
                    if val_info.image_qualified_name:
                        qualifiedImage = current_app.ToQualifiedName[IImage](
                            val_info.image_qualified_name)  # .Resolve()
                        if qualifiedImage:
                            new_value.Image = qualifiedImage

                    enum.AddValue(new_value)
                    existing_value_names.add(new_value.Name.lower())
                    report_lines.append(
                        f"  - [SUCCESS] Value '{new_value.Name}' added.")

            # 事务成功
            report_lines.append(
                f"[SUCCESS] Transaction for '{request.full_path}' committed.")
            success_count += 1

        except Exception as e:
            # TransactionManager 会自动回滚事务
            report_lines.append(
                f"[ERROR] Failed to process '{request.full_path}': {e}")
            report_lines.append(
                f"[STACK TRACE] {traceback.format_exc()}")
            report_lines.append("[INFO] Transaction has been rolled back.")
            failure_count += 1
            continue

    # 最终摘要
    report_lines.append("\n\n--- Final Summary ---")
    report_lines.append(
        f"Total requests processed: {len(tool_input.requests)}")
    report_lines.append(f"Successful: {success_count}")
    report_lines.append(f"Failed: {failure_count}")
    report_lines.append("---------------------")

    return "\n".join(report_lines)
