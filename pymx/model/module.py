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
# https://github.com/mendix/ExtensionAPI-Samples/tree/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel

# https://github.com/mendix/ExtensionAPI-Samples/tree/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.Projects


def getAbstractUnitByQualifiedName(ctx, qualifiedName):
    reports = []
    model = ctx.CurrentApp
    module_name, unit_name = qualifiedName.split('.')

    # modelRoot = ctx.untypedModelAccessService.GetUntypedModel(model)
    # modelUnits = modelRoot.GetUnitsOfType('Projects$Module')
    # modelUnit = next((u for u in modelUnits
    #                 if u.Name == module_name), None)
    # if modelUnit:
        # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel/IModelUnit.md
        # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel/IModelStructure.md

    # 查找模块
    module = next((m for m in ctx.CurrentApp.Root.GetModules()
                  if m.Name == module_name), None)
    
    # cascade find document, module is a folder, folder.GetDocuments(), folder.GetFolders()
    def find_document(folder, unit_name):
        # Try to find document in current folder
        document = next((doc for doc in folder.GetDocuments() if doc.Name == unit_name), None)
        if document is not None:
            return document
        
        # Try to find document in subfolders recursively
        for sub_folder in folder.GetFolders():
            document = find_document(sub_folder, unit_name)
            if document is not None:
                return document
        return None
    document = find_document(module, unit_name)
    return document, reports
