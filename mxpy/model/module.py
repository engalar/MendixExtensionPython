from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule, IFolder, IFolderBase  # type: ignore
import clr
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")


def ensure_module(current_app, module_name: str) -> IModule:
    """确保指定的模块存在，如果不存在则创建它。

    参数:
        current_app: 当前应用实例。
        module_name: 模块名称。

    返回:
        IModule: 模块实例。
    """
    module = next((m for m in current_app.Root.GetModules()
                  if m.Name == module_name), None)
    if not module:
        module = current_app.Create[IModule]()
        module.Name = f'{module_name}'
        current_app.Root.AddModule(module)
    return module
