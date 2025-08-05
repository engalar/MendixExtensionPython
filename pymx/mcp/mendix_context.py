# /your_python_script_folder/mendix_context.py

# 这个模块用作一个简单的上下文持有者，
# 用于存储在运行时从 C# 接收到的 Mendix 服务对象。
# 这样，任何工具模块都可以轻松地导入和使用它们，
# 而无需在每个函数调用中都传递它们。

# --- Mendix API 服务占位符 ---
# 这些变量将在服务器启动时由 main.py 填充。
CurrentApp = None
messageBoxService = None
extensionFileService = None
microflowActivititesService = None
microflowExpressionService = None
microflowService = None
untypedModelAccessService = None
dockingWindowService = None
domainModelService = None
backgroundJobService = None
configurationService = None
extensionFeaturesService = None
httpClientService = None
nameValidationService = None
navigationManagerService = None
pageGenerationService = None
appService = None
dialogService = None
entityService = None
findResultsPaneService = None
localRunConfigurationsService = None
notificationPopupService = None
runtimeService = None
selectorDialogService = None
versionControlService = None


def set_mendix_services(
    _CurrentApp,
    _messageBoxService,
    _extensionFileService,
    _microflowActivititesService,
    _microflowExpressionService,
    _microflowService,
    _untypedModelAccessService,
    _dockingWindowService,
    _domainModelService,
    _backgroundJobService,
    _configurationService,
    _extensionFeaturesService,
    _httpClientService,
    _nameValidationService,
    _navigationManagerService,
    _pageGenerationService,
    _appService,
    _dialogService,
    _entityService,
    _findResultsPaneService,
    _localRunConfigurationsService,
    _notificationPopupService,
    _runtimeService,
    _selectorDialogService,
    _versionControlService
):
    """在服务器启动时，用实际的服务对象填充此模块的全局变量。"""
    global CurrentApp, messageBoxService, extensionFileService, microflowActivititesService, microflowExpressionService, microflowService, untypedModelAccessService, dockingWindowService, domainModelService, backgroundJobService, configurationService, extensionFeaturesService, httpClientService, nameValidationService, navigationManagerService, pageGenerationService, appService, dialogService, entityService, findResultsPaneService, localRunConfigurationsService, notificationPopupService, runtimeService, selectorDialogService, versionControlService

    CurrentApp = _CurrentApp
    messageBoxService = _messageBoxService
    extensionFileService = _extensionFileService
    microflowActivititesService = _microflowActivititesService
    microflowExpressionService = _microflowExpressionService
    microflowService = _microflowService
    untypedModelAccessService = _untypedModelAccessService
    dockingWindowService = _dockingWindowService
    domainModelService = _domainModelService
    backgroundJobService = _backgroundJobService
    configurationService = _configurationService
    extensionFeaturesService = _extensionFeaturesService
    httpClientService = _httpClientService
    nameValidationService = _nameValidationService
    navigationManagerService = _navigationManagerService
    pageGenerationService = _pageGenerationService
    appService = _appService
    dialogService = _dialogService
    entityService = _entityService
    findResultsPaneService = _findResultsPaneService
    localRunConfigurationsService = _localRunConfigurationsService
    notificationPopupService = _notificationPopupService
    runtimeService = _runtimeService
    selectorDialogService = _selectorDialogService
    versionControlService = _versionControlService
