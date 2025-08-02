```python
def PostMessage(name, msg):
    print(msg)

# 导入
from mxpy.context import activeDocument

# 定义回调函数
def callback(event):
    PostMessage("python:exe", event)

# 读取
content = activeDocument.content

# 写入测试
activeDocument.content = "旧内容"
PostMessage("python:exe", activeDocument.content)

# 监听变更测试
activeDocument.content = "监听前的内容"
activeDocument.add_listener(callback)  # 添加监听器
activeDocument.content = "监听后的内容"  # 这里会触发 callback
activeDocument.remove_listener(callback)  # 移除监听器
activeDocument.content = "移除监听后的内容"  # 这里不会触发 callback
```