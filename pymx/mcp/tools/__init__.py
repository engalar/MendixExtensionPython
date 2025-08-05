import pkgutil
import importlib

# 这个 __init__.py 文件使 "tools" 目录成为一个 Python 包。
# 更重要的是，它会自动发现并导入此目录中的所有模块。
# 当一个工具模块（如 mendix_tools.py）被导入时，
# 它文件中定义的带有 @mcp.tool 装饰器的函数就会被执行并注册到共享的 mcp 实例中。
# 这就是实现开闭原则的方式：要添加一个新工具，只需在此目录中创建一个新文件，
# 无需修改任何现有代码。
from .. import mendix_context as ctx

# ctx.messageBoxService.ShowInformation("正在加载工具模块...")
for _, name, _ in pkgutil.iter_modules(__path__):
    try:
        # reload 模块
        importlib.reload(importlib.import_module(f".{name}", __name__))
        # ctx.messageBoxService.ShowInformation(f"已加载工具模块 {name}")
    except Exception as e:
        ctx.messageBoxService.ShowError(f"加载工具模块 {name} 失败: {e}")