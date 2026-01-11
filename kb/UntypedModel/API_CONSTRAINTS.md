# Mendix Studio Pro Python 环境 API 约束文档

> 基于 `debug2.py` 提取的受限环境 API 使用规范

## 1. 环境导入限制

### 必需导入
```python
import clr
```

### Mendix SDK 引用
```python
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
from Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel import PropertyType
```

**约束**: 只能导入标准Python库和通过`clr.AddReference`加载的.NET程序集

---

## 2. 核心对象模型

### 2.1 全局变量（预定义）
- `currentApp`: 当前应用对象
- `root`: 模型(untyped)根节点，此模型为非类型化的只读模型。

### 2.2 类型字符串格式
所有Mendix类型(untyped)使用 `Module$TypeName` 格式：
```
Projects$Module
DomainModels$DomainModel
DomainModels$Entity
Microflows$Microflow
Pages$Page
Workflows$Workflow
```

---

## 3. 基础API调用模式

### 3.1 获取单元集合

#### 按类型获取单元
```python
units = container.GetUnitsOfType("Module$TypeName")
# 示例
modules = self.root.GetUnitsOfType("Projects$Module")
microflows = mod.GetUnitsOfType("Microflows$Microflow")
```

#### 获取所有单元
```python
all_units = container.GetUnits()
# 返回迭代器，建议用 list() 转换
all_units_list = list(container_raw.GetUnits())
```

### 3.2 属性访问

#### 获取属性对象
```python
prop = obj.GetProperty("propertyName")
# 支持驼峰命名 (CamelCase)
# 如果不存在返回 None
```

#### 获取属性值
```python
value = prop.Value
# 返回类型:
# - 基本类型: str, int, float, bool
# - 对象类型: 有 Type 和 ID 属性的对象
# - 列表: 使用 prop.GetValues()
```

#### 判断是否为列表
```python
if prop.IsList:
    values = prop.GetValues()
    # values 是迭代器
```

### 3.3 对象元数据

```python
# 获取类型
obj.Type  # 返回 "Module$TypeName" 格式字符串

# 获取ID
obj.ID.ToString()  # 注意: ID 需要 .ToString() 转换为字符串

# 获取名称
obj.Name  # 返回字符串
```

---

## 4. 集合遍历模式

### 4.1 遍历单元
```python
units = module.GetUnitsOfType("Microflows$Microflow")
for unit in units:
    print(unit.Name)
```

### 4.2 遍历列表属性
```python
entities = domain_model.GetProperty("entities").GetValues()
for entity in entities:
    name = entity.GetProperty("name").Value
```

### 4.3 使用next()查找单个元素
```python
# 查找第一个匹配的元素
target = next(
    (u for u in units if u.Name == "TargetName"),
    None  # 默认值
)
```

---

## 5. 通信API

### 5.1 PostMessage函数

用于与前端通信：

```python
# 清除消息
PostMessage("backend:clear", "")

# 发送信息
PostMessage("backend:info", "Information message")

# 发送错误
PostMessage("backend:error", f"Error: {error_msg}")
```

**消息类型**:
- `backend:clear` - 清空消息队列
- `backend:info` - 信息消息
- `backend:error` - 错误消息

---

## 6. 文件操作约束

### 6.1 允许的操作
```python
# 写入文件
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Windows下打开文件
if os.name == "nt":
    os.startfile(file_path)
```

### 6.2 路径处理
```python
user_home = os.path.expanduser("~")
file_path = os.path.join(user_home, "filename.md")
```

---

## 7. 错误处理模式

```python
try:
    # 业务逻辑
    ctx = MendixContext(currentApp, root)
    # ...
except Exception as e:
    PostMessage("backend:error", f"Error: {str(e)}\n{traceback.format_exc()}")
```

---

## 8. 已知类型和属性映射

### 8.1 Module (Projects$Module)
- `Name`: str
- `GetUnitsOfType(type)`: 返回指定类型的单元

### 8.2 DomainModel (DomainModels$DomainModel)
- `entities`: List<Entity>
- `associations`: List<Association>
- `cross_associations`: List<CrossAssociation>

### 8.3 Entity (DomainModels$Entity)
- `name`: str
- `attributes`: List<Attribute>
- `generalization`: Generalization

### 8.4 Microflow (Microflows$Microflow)
- `Name`: str
- `object_collection`: 包含 `objects` 列表
- `flows`: 流程连接列表

### 8.5 Page (Pages$Page)
- `name`: str
- `layout_call`: LayoutCall
- `title`: Text

### 8.6 Workflow (Workflows$Workflow)
- `Name`: str
- `parameter`: WorkflowParameter
- `flow`: Flow

---

## 9. 性能优化模式

### 9.1 属性缓存
```python
class MendixElement:
    def __init__(self, raw_obj, context):
        self._cache = {}  # 缓存属性访问结果

    def __getattr__(self, name):
        if name in self._cache:
            return self._cache[name]
        # ... 计算并缓存
        self._cache[name] = result
        return result
```

### 9.2 实体查找缓存
```python
# 预扫描建立O(1)查询表
def _ensure_initialized(self):
    if self._is_initialized:
        return
    # 扫描所有实体
    modules = self.root.GetUnitsOfType("Projects$Module")
    for mod in modules:
        # ... 建立缓存
    self._is_initialized = True
```

---

## 10. 命名转换规则

### 10.1 Python snake_case → Mendix CamelCase
```python
# Python属性名: cross_associations
# 自动转换为: crossAssociations

parts = name.split("_")
camel_name = parts[0] + "".join(x.title() for x in parts[1:])
```

### 10.2 类型名简化
```python
full_type = "DomainModels$Entity"
type_name = full_type.split("$")[-1]  # "Entity"
```

---

## 11. 禁止的操作

❌ **不支持反射**: 无法动态获取所有属性名
❌ **不支持直接实例化**: 不能使用 `new` 创建Mendix对象
❌ **不支持修改操作**: 所有API都是只读的
❌ **不支持异步**: 只能同步执行
❌ **不支持网络IO**: 无法访问外部API

---

## 12. 调用模板

### 12.1 基础查找模板
```python
def find_something(module_name, item_name):
    # 1. 找模块
    modules = root.GetUnitsOfType("Projects$Module")
    module = next((m for m in modules if m.Name == module_name), None)
    if not module:
        return None

    # 2. 找目标
    items = module.GetUnitsOfType("Module$ItemType")
    target = next((i for i in items if i.Name == item_name), None)
    return target
```

### 12.2 属性遍历模板
```python
def process_object(obj):
    # 获取列表属性
    list_prop = obj.GetProperty("items")
    if list_prop and list_prop.IsList:
        for item in list_prop.GetValues():
            # 获取子属性
            name = item.GetProperty("name").Value
            value = item.GetProperty("value").Value
            # 处理...
```

### 12.3 上下文使用模板
```python
# 初始化上下文
ctx = MendixContext(currentApp, root)

# 记录日志
ctx.log("Header message")
ctx.log("Indented message", indent=1)

# 获取结果
result = ctx.flush_logs()
```

---

## 13. 类型系统映射

### 13.1 属性类型 (PropertyType)
```python
# Mendix属性类型
PropertyType.String      # 字符串
PropertyType.Integer     # 整数
PropertyType.Boolean     # 布尔
PropertyType.Decimal     # 小数
PropertyType.DateTime    # 日期时间
PropertyType.Enumeration # 枚举
```

### 13.2 数据类型 (DataTypes)
```python
DataTypes$StringType
DataTypes$IntegerType
DataTypes$BooleanType
DataTypes$VoidType
DataTypes$DecimalType
DataTypes$LongType
DataTypes$DateTimeAttributeType
```

---

## 14. 总结清单

使用此环境时，必须遵守：

✅ 只使用 `GetUnitsOfType()`, `GetProperty()`, `GetValues()`, `Name`, `Type`, `ID` 这些API
✅ 所有属性访问通过 `GetProperty("name").Value` 模式
✅ 列表属性使用 `IsList` 检查和 `GetValues()` 遍历
✅ 使用 `PostMessage()` 与前端通信
✅ 使用 `currentApp` 和 `root` 作为入口点
✅ 严格遵守 `Module$TypeName` 类型字符串格式
✅ 缓存频繁访问的属性以提升性能

❌ 不要尝试使用未在此文档列出的API
❌ 不要尝试修改模型（untyped相关的API只读）
❌ 不要假设存在未验证的属性
❌ 不要使用反射或动态特性分析
