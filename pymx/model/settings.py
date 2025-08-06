# https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.Settings/IProjectSettings.md
import System
from pymx.model.dto import type_settings
from Mendix.StudioPro.ExtensionsAPI.Model.Settings import (  # type: ignore
    IProjectSettings,
    IConfigurationSettings,
    IConfiguration,
    ICustomSetting,
    IConstantValue,
    ISharedValue,
)
# https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.Constants/IConstant.md
from Mendix.StudioPro.ExtensionsAPI.Model.Constants import (  # type: ignore
    IConstant,
)
import clr
import traceback
from typing import List, Optional, Any
from pymx.model.util import TransactionManager
import importlib

clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
importlib.reload(type_settings)


def callAsType(model, obj, type, methodName, params=None):
    """
    获取对象方法并调用
    参数：
    model: 模型对象
    obj: 对象
    type: 对象类型
    methodName: 方法名
    params: 方法参数
    """
    helpObj = model.Create[type]()
    mi = helpObj.GetType().GetMethod(methodName)
    return mi.Invoke(obj, params)


async def create_settings(ctx: Any, request: type_settings.SettingsRequest) -> str:
    """
    创建或更新配置设置，并返回一个纯文本报告。
    """
    report_lines: List[str] = ["开始配置设置创建流程..."]
    current_app: Any = ctx.CurrentApp
    messageBoxService = ctx.messageBoxService

    try:
        with TransactionManager(current_app, f"创建配置 '{request.name}'"):
            # 查找 IProjectSettings
            project_settings: Optional[IProjectSettings] = None
            for doc in current_app.Root.GetProjectDocuments():
                if doc.GetType().AssemblyQualifiedName.startswith('Mendix.Modeler.ExtensionLoader.ModelProxies.Settings.ProjectSettingsProxy'):
                    project_settings = doc
                    break

            if project_settings is None:
                raise Exception("在应用中未找到 IProjectSettings。")

            report_lines.append("- 已找到项目设置文档。")

            # found, abstractUnit = current_app.TryGetAbstractUnitById(project_settings.Id, None)  # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model/IModel/TryGetAbstractUnitById.md
            # messageBoxService.ShowInformation(f"found: {found}", f"{dir(abstractUnit)}")

            # messageBoxService.ShowInformation(f"{project_settings.Id}", f"{dir(empty_project_settings)}")

            # type cast workaround, cast from IProjectDocument to IProjectSettings
            empty_project_settings = current_app.Create[IProjectSettings]()
            mi = empty_project_settings.GetType().GetMethod('GetSettingsParts')
            parts = mi.Invoke(project_settings, None)

            # 查找 IConfigurationSettings
            project_settings_part_proxy = None
            for part in parts:
                if part.GetType().AssemblyQualifiedName.startswith('Mendix.Modeler.ExtensionLoader.ModelProxies.Settings.ConfigurationSettingsProxy'):
                    project_settings_part_proxy = part
                    break

            if project_settings_part_proxy is None:
                raise Exception("在项目设置中未找到 IConfigurationSettings。")

            report_lines.append("- 已找到配置设置部分。")

            # 检查是否已存在同名配置
            existing_configuration: Optional[IConfiguration] = None
            configs = callAsType(
                current_app, project_settings_part_proxy, IConfigurationSettings, "GetConfigurations")
            # print len
            # messageBoxService.ShowInformation(f"{configs.Count}")
            for config in configs:
                if config.Name == request.name:
                    existing_configuration = config
                    break

            if existing_configuration:
                report_lines.append(
                    f"- [INFO] 配置 '{request.name}' 已存在，将进行更新...")
                configuration: IConfiguration = existing_configuration
            else:
                # 创建新配置
                configuration = current_app.Create[IConfiguration]()
                configuration.Name = request.name

                # IConfigurationSettings is subclass of IProjectSettingsPart, and IConfigurationSettings has a method AddConfiguration, accepting IConfiguration as parameter.
                # configuration_settings_proxy.AddConfiguration(configuration)
                callAsType(
                    current_app, project_settings_part_proxy, IConfigurationSettings, "AddConfiguration", [configuration])

                report_lines.append(f"- [SUCCESS] 配置 '{request.name}' 已创建。")

            # 设置 ApplicationRootUrl
            if request.application_root_url is not None:
                configuration.ApplicationRootUrl = request.application_root_url
                report_lines.append(
                    f"- 已设置应用根URL: {request.application_root_url}")

            # 处理常量
            if request.constants:
                for constant_item in request.constants:
                    const_value: IConstantValue = current_app.Create[IConstantValue](
                    )
                    const_value.Constant = current_app.ToQualifiedName[IConstant](
                        constant_item.qualified_name)

                    shared_value: ISharedValue = current_app.Create[ISharedValue](
                    )
                    shared_value.Value = constant_item.value

                    const_value.SharedOrPrivateValue = shared_value
                    configuration.AddConstantValue(const_value)
                report_lines.append(f"- 已添加 {len(request.constants)} 个常量。")
            else:
                report_lines.append("- 没有需要添加的常量。")

            # 处理自定义设置
            if request.customs:
                for custom_item in request.customs:
                    custom_setting: ICustomSetting = current_app.Create[ICustomSetting](
                    )
                    custom_setting.Name = custom_item.name
                    custom_setting.Value = custom_item.value
                    configuration.AddCustomSetting(custom_setting)
                report_lines.append(f"- 已添加 {len(request.customs)} 个自定义设置。")
            else:
                report_lines.append("- 没有需要添加的自定义设置。")

        # 如果事务成功提交
        report_lines.append(f"[SUCCESS] 配置 '{request.name}' 的事务已提交。")

    except Exception as e:
        # TransactionManager 会自动回滚
        report_lines.append(f"[ERROR] 创建配置 '{request.name}' 失败: {e}")
        report_lines.append(traceback.format_exc())
        report_lines.append("[INFO] 事务已回滚。")
        return "\n".join(report_lines)

    # 最终总结
    report_lines.append("\n--- 最终总结 ---")
    report_lines.append(f"配置 '{request.name}' 处理完成。")
    report_lines.append("---------------------")

    return "\n".join(report_lines)
