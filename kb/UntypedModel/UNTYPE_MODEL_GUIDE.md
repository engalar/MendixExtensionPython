# Mendix Untyped Model 编码指导手册

> 基于 `untype visualizer/main.py` 实践归纳
>
> 本手册总结如何使用 Mendix Studio Pro Extensions API 探索和操作 untyped model（无类型模型）。

---

## 1. 核心概念

### 1.1 Untyped Model 特性

Mendix 的 untyped model 是指：
- **动态类型系统**：对象类型通过 `.Type` 属性获取（如 `"Projects$Module"`, `"Microflows$Microflow"`）
- **统一访问接口**：通过 `GetProperties()` 方法获取所有属性，而非直接属性访问
- **属性元数据**：每个属性包含 `Name`、`Value`、`Type`、`IsList` 等元信息
- **嵌套结构**：支持 Element（单对象）和 List（集合）两种引用类型

### 1.2 核心类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Unit** | 顶级容器单元，具有唯一 ID | Module, Folder, Document |
| **Element** | 模型元素，属于某个 Unit | Entity, Microflow, Attribute |
| **List** | 元素集合，支持 `.Count` 和迭代 | Module.GetUnits() |
| **Property** | 属性描述对象 | `.GetProperties()` 返回值 |

---

## 2. 基础操作模式

### 2.1 属性遍历模式

```python
# @PATTERN:属性遍历 - 获取对象所有属性
if hasattr(element, "GetProperties"):
    for prop in element.GetProperties():
        name = prop.Name           # 属性名
        value = prop.Value         # 属性值
        type_str = str(prop.Type)  # 类型字符串
        is_list = prop.IsList      # 是否为列表
```

### 2.2 类型判断模式

```python
# @PATTERN:类型判断 - 识别元素类型
element_type = str(element.Type)        # 完整类型：Projects$Module
short_type = element.Type.split('$')[-1]  # 简短类型：Module

# 判断类别
is_unit = hasattr(element, "ID")          # 是否为 Unit
has_children = hasattr(element, "GetUnits")  # 是否有子单元
```

### 2.3 引用解析模式

```python
# @PATTERN:引用解析 - 处理不同类型的属性值
val = prop.Value

if prop.IsList:
    # List 类型：集合对象
    count = val.Count
    for item in val:
        process(item)
elif hasattr(val, "GetProperties"):
    # Element 类型：嵌套对象
    process_nested(val)
else:
    # Primitive 类型：简单值
    print(str(val))
```

---

## 3. 导航模式

### 3.1 父子关系导航

```python
# @PATTERN:向下导航 - 获取子节点
if hasattr(parent, "GetUnits"):
    # Unit -> Unit 关系（如 Module -> Folder）
    child_units = list(parent.GetUnits())

if hasattr(parent, "GetElements"):
    # Element -> Element 关系（如 Entity -> Attribute）
    child_elements = list(parent.GetElements())
```

### 3.2 向上导航（容器链）

```python
# @PATTERN:向上导航 - 遍历容器链
path_segments = []
curr = element
while curr:
    name = getattr(curr, "Name", None)
    if name:
        path_segments.insert(0, name)
    try:
        curr = curr.Container  # 获取父容器
    except:
        break

full_path = "/".join(path_segments)
```

### 3.3 类型过滤查询

```python
# @PATTERN:类型过滤 - 按类型查找节点
# 获取特定类型的所有 Unit
specific_units = root.GetUnitsOfType("Projects$Module")
for unit in specific_units:
    print(unit.Name)

# 过滤子节点
folders = list(parent.GetUnitsOfType('Projects$Folder'))
```

---

## 4. Pythonic 封装模式

### 4.1 MxNode 包装器

核心思想：将 Mendix untyped API 包装为 Pythonic 接口。

```python
class MxNode:
    def __init__(self, raw_element):
        self.raw = raw_element
        # 缓存属性映射：Name -> Property
        self._props = {}
        if raw_element and hasattr(raw_element, "GetProperties"):
            for p in raw_element.GetProperties():
                self._props[p.Name] = p

    @property
    def type(self):
        """获取简短类型名"""
        if self.raw and hasattr(self.raw, 'Type'):
            return str(self.raw.Type).split('$')[-1]
        return "Null"

    def get(self, key, default=None):
        """获取简单值"""
        if key not in self._props: return default
        val = self._props[key].Value
        return str(val) if val is not None else default

    def resolve(self, key):
        """获取引用对象"""
        if key not in self._props: return None
        val = self._props[key].Value
        return MxNode(val) if val else None

    def children(self, key):
        """获取列表子项"""
        if key not in self._props: return []
        prop = self._props[key]
        if not prop.IsList or not prop.Value: return []
        return [MxNode(item) for item in prop.Value]
```

**使用示例**：
```python
node = MxNode(element)
name = node.get('Name')
attrs = node.children('Attributes')
```

---

## 5. 缓存与生命周期管理

### 5.1 ID 生成策略

```python
# @PATTERN:ID生成 - 统一的对象标识
def cache_element(self, element):
    if element is None: return None

    # Unit 有永久 ID
    if hasattr(element, "ID"):
        uid = str(element.ID)
    else:
        # Element/List 使用临时 ID
        uid = f"tmp_{id(element)}"

    self._element_cache[uid] = element
    return uid
```

### 5.2 缓存注意事项

- **Unit ID**：跨会话稳定，可长期缓存
- **临时 ID**：仅在当前会话有效（基于 Python `id()`）
- **过期处理**：需要在访问时检查是否存在

```python
def get_cached(self, uid):
    return self._element_cache.get(uid)
```

---

## 6. 深度遍历与递归控制

### 6.1 深度保护

```python
# @PATTERN:深度保护 - 防止无限递归
def extract(self, element, depth=0, max_depth=5):
    if depth > max_depth:
        return "..."  # 深度超限标记

    # 递归处理子节点
    for item in children:
        self.extract(item, depth + 1, max_depth)
```

### 6.2 C# List 与 Python List 互操作

**关键点**：Mendix API 返回的 C# List 不能直接切片，需先转换。

```python
# 错误示例
# for item in csharp_list[:20]:  # 不支持！

# 正确做法
raw_collection = val if val else []
py_list = list(raw_collection)  # 转换为 Python list

# 现在可以切片
for item in py_list[:20]:
    process(item)
```

### 6.3 限制集合大小

```python
# 防止大型集合导致性能问题
MAX_ITEMS = 20
items = list(csharp_collection)[:MAX_ITEMS]
```

---

## 7. JSON-RPC 消息处理模式

### 7.1 双层反序列化安全

```python
# @PATTERN:消息处理 - 安全解析嵌套 JSON
json_str = System.Text.Json.JsonSerializer.Serialize(message_wrapper)
data = json.loads(json_str)
raw_request = data.get("Data")

if raw_request:
    request = json.loads(raw_request) if isinstance(raw_request, str) else raw_request

    method = request.get("method")
    params = request.get("params", {})
```

### 7.2 统一响应格式

```python
# 成功响应
response = {
    "jsonrpc": "2.0",
    "result": result,
    "requestId": req_id,
    "traceId": traceId  # 可选：用于追踪
}

# 错误响应
response = {
    "jsonrpc": "2.0",
    "error": {"message": str(e)},
    "requestId": req_id
}
```

---

## 8. 路由装饰器模式

```python
class MendixApp:
    def __init__(self):
        self._routes: Dict[str, Callable] = {}

    def route(self, method_name: str = None):
        """注册路由的装饰器"""
        def decorator(func):
            name = method_name or func.__name__
            self._routes[name] = func
            return func
        return decorator

    def handle_message(self, message_wrapper):
        method = request.get("method")
        if method not in self._routes:
            raise Exception(f"Method '{method}' not found.")

        result = self._routes[method](**params)
```

**使用示例**：
```python
@app.route("get_details")
def get_details(node_id: str):
    target = app.get_cached(node_id)
    return {"name": target.Name, ...}
```

---

## 9. 类型分类与图标映射

```python
# @PATTERN:类型分类 - 根据类型确定 UI 表现
def get_node_type_category(element_type: str, is_unit: bool) -> str:
    if element_type in ['Projects$Module', 'Projects$Folder']:
        return 'folder'   # 文件夹图标
    if is_unit:
        return 'file'     # 文件图标
    return 'element'      # 元素图标
```

---

## 10. 调试与诊断

### 10.1 结构探索工具

```python
# @PATTERN:结构探索 - 递归输出对象结构
def explore(node):
    result = {
        "metaType": str(node.Type),
        "attributes": [],  # 简单属性
        "children": []     # 嵌套结构
    }

    if not hasattr(node, "GetProperties"):
        return {"metaType": "Value", "value": str(node)}

    for p in node.GetProperties():
        if "Element" in str(p.Type):
            # 嵌套对象/列表
            result["children"].append(explore(p.Value))
        else:
            # 简单属性
            result["attributes"].append({
                "key": p.Name,
                "value": str(p.Value)
            })

    return result
```

### 10.2 错误处理

```python
try:
    result = self._routes[method](**params)
    PostMessage("backend:response", json.dumps({"result": result}))
except Exception as e:
    err_msg = f"{str(e)}\n{traceback.format_exc()}"
    PostMessage("backend:info", err_msg)
    PostMessage("backend:response", json.dumps({
        "error": {"message": str(e)}
    }))
```

---

## 11. 最佳实践清单

### ✅ 推荐做法

1. **使用 MxNode 包装器**：简化属性访问逻辑
2. **限制递归深度**：设置 `max_depth=5` 防止无限递归
3. **转换 C# List**：先 `list()` 再切片或迭代
4. **缓存对象引用**：使用 ID 而非序列化整个对象
5. **类型安全检查**：使用 `hasattr()` 检查方法/属性存在性
6. **分层响应设计**：Tree View（轻量）vs Details View（详细）

### ❌ 常见陷阱

1. **直接切片 C# List**：`csharp_list[:10]` 会失败
2. **忽略 None 检查**：`prop.Value` 可能为 None
3. **混淆 Unit 和 Element**：Unit 有 ID，Element 不一定有
4. **无限递归**：忘记深度限制
5. **硬编码类型名**：应使用 `.Type.split('$')[-1]` 获取短名称

---

## 12. 代码架构建议

```
┌─────────────────────────────────────────┐
│         前端 (Frontend)                  │
└──────────────┬──────────────────────────┘
               │ JSON-RPC
┌──────────────▼──────────────────────────┐
│         MendixApp (路由层)               │
│  - route() 装饰器                        │
│  - handle_message()                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      业务逻辑层 (Business Logic)         │
│  - get_root_nodes()                      │
│  - get_details()                         │
│  - get_structure()                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      核心封装层 (Core Wrappers)          │
│  - MxNode (属性访问封装)                 │
│  - YamlExtractor (DSL 数据清洗)          │
│  - StructureExplorer (结构探索)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Mendix Extensions API (底层)           │
│  - IModel, IUnit, IElement               │
│  - GetProperties(), GetUnits()           │
└─────────────────────────────────────────┘
```

---

## 13. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 单元 | Unit | Mendix 模型的顶级容器，有唯一 ID |
| 元素 | Element | 模型中的具体对象，属于 Unit |
| 属性 | Property | 对象的键值对，含元数据 |
| 引用 | Reference | 指向另一个对象的属性 |
| 列表 | List | 对象集合，支持迭代 |
| 类型 | Type | 对象的类型标识（如 `Projects$Module`）|
| 容器 | Container | 父级对象，通过 `.Container` 访问 |

---

## 14. 参考资料

- **Mendix Studio Pro Extensions API**: `Mendix.StudioPro.ExtensionsAPI.dll`
- **依赖**: `pythonnet` (用于 C# 互操作)
- **序列化**: `System.Text.Json` (Mendix 内置)

---

*文档生成时间: 2026-01-14*
*基于代码: `untype visualizer/main.py` (ID: 536df8e04cd5574946a62414abb12ad8)*
