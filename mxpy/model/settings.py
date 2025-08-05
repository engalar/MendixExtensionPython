from Mendix.StudioPro.ExtensionsAPI.Model.Settings import (  # type: ignore
    IProjectSettings,
    IConfigurationSettings,
    IConfiguration,
    ICustomSetting
)
from Mendix.StudioPro.ExtensionsAPI.Model.Constants import (  # type: ignore
    IConstant,
    IConstantValue,
    ISharedValue
)
import clr
import traceback
from typing import List, Optional, Any
from mxpy.model.util import TransactionManager

clr.AddReference("Mendix.StudioPro.ExtensionsAPI")


class ConstantItem:
    def __init__(self, qualified_name: str, value: str):
        self.QualifiedName: str = qualified_name
        self.Value: str = value


class CustomItem:
    def __init__(self, name: str, value: str):
        self.Name: str = name
        self.Value: str = value


class SettingsRequest:
    def __init__(self, name: str, application_root_url: Optional[str] = None, 
                 constants: Optional[List[ConstantItem]] = None, 
                 customs: Optional[List[CustomItem]] = None):
        self.Name: str = name
        self.ApplicationRootUrl: Optional[str] = application_root_url
        self.Constants: List[ConstantItem] = constants if constants is not None else []
        self.Customs: List[CustomItem] = customs if customs is not None else []


async def create_settings(ctx: Any, request: SettingsRequest) -> str:
    """
    创建或更新配置设置，并返回一个纯文本报告。
    """
    report_lines: List[str] = ["开始配置设置创建流程..."]
    current_app: Any = ctx.CurrentApp

    try:
        with TransactionManager(current_app, f"创建配置 '{request.Name}'"):
            # 查找 IProjectSettings
            project_settings: Optional[IProjectSettings] = None
            for doc in current_app.Root.GetProjectDocuments():
                if isinstance(doc, IProjectSettings):
                    project_settings = doc
                    break

            if project_settings is None:
                raise Exception("在应用中未找到 IProjectSettings。")

            report_lines.append("- 已找到项目设置文档。")

            # 查找 IConfigurationSettings
            configuration_settings: Optional[IConfigurationSettings] = None
            for part in project_settings.GetSettingsParts():
                if isinstance(part, IConfigurationSettings):
                    configuration_settings = part
                    break

            if configuration_settings is None:
                raise Exception("在项目设置中未找到 IConfigurationSettings。")

            report_lines.append("- 已找到配置设置部分。")

            # 检查是否已存在同名配置
            existing_configuration: Optional[IConfiguration] = None
            for config in configuration_settings.GetConfigurations():
                if config.Name == request.Name:
                    existing_configuration = config
                    break

            if existing_configuration:
                report_lines.append(f"- [INFO] 配置 '{request.Name}' 已存在，将进行更新...")
                configuration: IConfiguration = existing_configuration
            else:
                # 创建新配置
                configuration = current_app.Create[IConfiguration]()
                configuration.Name = request.Name
                configuration_settings.AddConfiguration(configuration)
                report_lines.append(f"- [SUCCESS] 配置 '{request.Name}' 已创建。")

            # 设置 ApplicationRootUrl
            if request.ApplicationRootUrl is not None:
                configuration.ApplicationRootUrl = request.ApplicationRootUrl
                report_lines.append(f"- 已设置应用根URL: {request.ApplicationRootUrl}")

            # 处理常量
            if request.Constants:
                for constant_item in request.Constants:
                    const_value: IConstantValue = current_app.Create[IConstantValue]()
                    const_value.Constant = current_app.ToQualifiedName[IConstant](
                        constant_item.QualifiedName)

                    shared_value: ISharedValue = current_app.Create[ISharedValue]()
                    shared_value.Value = constant_item.Value

                    const_value.SharedOrPrivateValue = shared_value
                    configuration.AddConstantValue(const_value)
                report_lines.append(f"- 已添加 {len(request.Constants)} 个常量。")
            else:
                report_lines.append("- 没有需要添加的常量。")

            # 处理自定义设置
            if request.Customs:
                for custom_item in request.Customs:
                    custom_setting: ICustomSetting = current_app.Create[ICustomSetting]()
                    custom_setting.Name = custom_item.Name
                    custom_setting.Value = custom_item.Value
                    configuration.AddCustomSetting(custom_setting)
                report_lines.append(f"- 已添加 {len(request.Customs)} 个自定义设置。")
            else:
                report_lines.append("- 没有需要添加的自定义设置。")

        # 如果事务成功提交
        report_lines.append(f"[SUCCESS] 配置 '{request.Name}' 的事务已提交。")

    except Exception as e:
        # TransactionManager 会自动回滚
        report_lines.append(f"[ERROR] 创建配置 '{request.Name}' 失败: {e}")
        report_lines.append(traceback.format_exc())
        report_lines.append("[INFO] 事务已回滚。")
        return "\n".join(report_lines)

    # 最终总结
    report_lines.append("\n--- 最终总结 ---")
    report_lines.append(f"配置 '{request.Name}' 处理完成。")
    report_lines.append("---------------------")

    return "\n".join(report_lines)