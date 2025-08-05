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

def set_mendix_services(
    app, msg_box, ext_file, mf_activities, mf_expr, mf, untyped_model
):
    """在服务器启动时，用实际的服务对象填充此模块的全局变量。"""
    global CurrentApp, messageBoxService, extensionFileService, microflowActivititesService, microflowExpressionService, microflowService, untypedModelAccessService
    CurrentApp = app
    messageBoxService = msg_box
    extensionFileService = ext_file
    microflowActivititesService = mf_activities
    microflowExpressionService = mf_expr
    microflowService = mf
    untypedModelAccessService = untyped_model