# Mendix Python 框架参考文档

> 基于 `debug2.py` 的 Mendix 模型访问框架系统设计

---

## 目录

1. [框架概览](#1-框架概览)
2. [核心组件](#2-核心组件)
3. [MendixContext 上下文系统](#3-mendixcontext-上下文系统)
4. [ElementFactory 工厂模式](#4-elementfactory-工厂模式)
5. [MendixElement 动态代理](#5-mendixelement-动态代理)
6. [类型映射系统](#6-类型映射系统)
7. [包装类层次结构](#7-包装类层次结构)
8. [扩展指南](#8-扩展指南)

---

## 1. 框架概览

### 1.1 设计目标

框架旨在为 Mendix 的 Untyped Model 提供一个类型安全、易用的 Python 访问层：

- **动态代理**: 通过 `__getattr__` 实现 snake_case → CamelCase 自动转换
- **类型封装**: 自动将原始对象包装为对应的 Python 类
- **属性缓存**: 缓存计算结果提升性能
- **多态方法**: 基于类型的动态行为

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    MendixContext                        │
│  - root: IModel                                         │
│  - model: IModel                                        │
│  - log_buffer: List[str]                                │
│  - _entity_qname_cache: Dict                            │
└───────────────┬─────────────────────────────────────────┘
                │ 提供
                ▼
┌─────────────────────────────────────────────────────────┐
│                 ElementFactory                          │
│  create(raw_obj, context) -> MendixElement              │
└───────────────┬─────────────────────────────────────────┘
                │ 创建
                ▼
┌─────────────────────────────────────────────────────────┐
│                 MendixElement (基类)                    │
│  - _raw: INavigationItem                                │
│  - ctx: MendixContext                                   │
│  - _cache: Dict                                         │
│  + __getattr__(name)                                    │
│  + get_summary()                                        │
└───────────────┬─────────────────────────────────────────┘
                │ 继承
                ▼
┌─────────────────────────────────────────────────────────┐
│            具体类型包装类 (100+ 类)                     │
│  Projects_Module, DomainModels_Entity,                  │
│  Microflows_MicroflowCallAction, Pages_Widget, ...      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 核心组件

### 2.1 组件清单

| 组件 | 职责 | 文件位置 |
|------|------|----------|
| `MendixContext` | 运行上下文、日志、缓存 | 第27-68行 |
| `ElementFactory` | 对象创建、类型路由 | 第70-88行 |
| `MendixElement` | 动态代理基类 | 第91-162行 |
| `MendixMap` | 类型映射装饰器 | 第17-24行 |
| `_MENDIX_TYPE_REGISTRY` | 全局类型注册表 | 第14行 |

---

## 3. MendixContext 上下文系统

### 3.1 类定义

```python
class MendixContext:
    """运行上下文：负责日志管理、全局搜索缓存和 Unit 查找"""

    def __init__(self, model, root_node):
        self.root = root_node          # IModel: 模型根节点
        self.model = model             # IModel: 当前模型
        self.log_buffer = []           # List[str]: 日志缓冲区
        self._entity_qname_cache = {}  # Dict: 实体全名缓存
        self._is_initialized = False   # bool: 初始化标志
```

### 3.2 核心方法

#### 3.2.1 延迟初始化

```python
def _ensure_initialized(self):
    """预扫描所有模块和实体，建立 O(1) 查询表"""
    if self._is_initialized:
        return

    modules = self.root.GetUnitsOfType("Projects$Module")
    for mod in modules:
        dm_units = mod.GetUnitsOfType("DomainModels$DomainModel")
        for dm in dm_units:
            ents = dm.GetProperty("entities").GetValues()
            for e in ents:
                qname = f"{mod.Name}.{e.GetProperty('name').Value}"
                self._entity_qname_cache[qname] = e

    self._is_initialized = True
```

**设计要点**:
- 延迟加载：首次需要时才扫描
- 性能优化：建立 O(1) 查询表
- 全名格式：`ModuleName.EntityName`

#### 3.2.2 日志系统

```python
def log(self, msg, indent=0):
    """记录带缩进的日志"""
    prefix = "  " * indent
    self.log_buffer.append(f"{prefix}{msg}")

def flush_logs(self):
    """获取所有日志并清空缓冲区"""
    return "\n".join(self.log_buffer)
```

**使用示例**:
```python
ctx = MendixContext(currentApp, root)
ctx.log("Header")
ctx.log("Indented item", indent=1)
ctx.log("Nested item", indent=2)
report = ctx.flush_logs()
```

#### 3.2.3 查找方法

```python
def find_module(self, module_name):
    """按名称查找模块"""
    modules = list(self.root.GetUnitsOfType("Projects$Module"))
    raw = next((m for m in modules if m.Name == module_name), None)
    return ElementFactory.create(raw, self) if raw else None

def find_entity_by_qname(self, qname):
    """按全名查找实体（需先初始化）"""
    self._ensure_initialized()
    raw = self._entity_qname_cache.get(qname)
    return ElementFactory.create(raw, self) if raw else None
```

---

## 4. ElementFactory 工厂模式

### 4.1 类定义

```python
class ElementFactory:
    """工厂类：负责对象的动态封装"""

    @staticmethod
    def create(raw_obj, context):
        """根据对象类型创建对应的 Python 包装对象"""
```

### 4.2 创建逻辑

```python
@staticmethod
def create(raw_obj, context):
    # 1. 处理 None
    if raw_obj is None:
        return MendixElement(None, context)

    # 2. 基础类型直接返回
    if isinstance(raw_obj, (str, int, float, bool)):
        return raw_obj

    # 3. 尝试获取 Mendix 类型
    try:
        full_type = raw_obj.Type  # 例如 "DomainModels$Entity"
    except AttributeError:
        return MendixElement(raw_obj, context)

    # 4. 查找注册的包装类
    target_cls = _MENDIX_TYPE_REGISTRY.get(full_type, MendixElement)
    return target_cls(raw_obj, context)
```

### 4.3 工作流程

```
原始对象 (raw_obj)
    │
    ├─→ None? → MendixElement(None, ctx)
    │
    ├─→ 基础类型? → 直接返回值
    │
    ├─→ 无 Type 属性? → MendixElement(raw_obj, ctx)
    │
    └─→ 有 Type? → 查找注册表
                      ├─→ 已注册 → 返回注册类实例
                      └─→ 未注册 → 返回基类 MendixElement
```

---

## 5. MendixElement 动态代理

### 5.1 类定义

```python
class MendixElement:
    """动态代理基类：支持属性缓存、多态摘要和 snake_case 自动转换"""

    def __init__(self, raw_obj, context):
        self._raw = raw_obj           # INavigationItem: 原始 Mendix 对象
        self.ctx = context            # MendixContext: 运行上下文
        self._cache = {}              # Dict: 属性缓存
```

### 5.2 核心属性

```python
@property
def is_valid(self):
    """检查对象是否有效（非 None）"""
    return self._raw is not None

@property
def id(self):
    """获取对象 ID（字符串格式）"""
    return self._raw.ID.ToString() if self.is_valid else "0"

@property
def type_name(self):
    """获取简短类型名（不含模块前缀）"""
    if not self.is_valid:
        return "Null"
    return self._raw.Type.split("$")[-1]  # "DomainModels$Entity" → "Entity"
```

### 5.3 动态属性访问 (`__getattr__`)

这是框架的核心魔法：

```python
def __getattr__(self, name):
    """映射 snake_case 到 CamelCase 并自动封装结果"""
    # 1. 无效对象返回 None
    if not self.is_valid:
        return None

    # 2. 检查缓存
    if name in self._cache:
        return self._cache[name]

    # 3. 转换命名: cross_associations → crossAssociations
    parts = name.split("_")
    camel_name = parts[0] + "".join(x.title() for x in parts[1:])

    # 4. 从 SDK 获取属性
    prop = self._raw.GetProperty(camel_name)
    if prop is None:
        prop = self._raw.GetProperty(name)  # 备用：尝试原始名

    if prop is None:
        raise AttributeError(f"'{self.type_name}' has no property '{name}'")

    # 5. 处理结果
    if prop.IsList:
        # 列表类型：递归封装每个元素
        result = [ElementFactory.create(v, self.ctx) for v in prop.GetValues()]
    else:
        val = prop.Value
        if hasattr(val, "Type") or hasattr(val, "ID"):
            # 对象类型：递归封装
            result = ElementFactory.create(val, self.ctx)
        elif isinstance(val, str):
            # 字符串：清理换行符
            result = val.replace("\r\n", "\\n").strip()
        else:
            # 基础类型：直接返回
            result = val

    # 6. 特殊处理：截断过长的文档
    if name == 'documentation' and len(result) > 30:
        result = result[:30] + "..."

    # 7. 缓存并返回
    self._cache[name] = result
    return result
```

### 5.4 属性访问示例

```python
# 原始 Mendix 模型
entity.GetProperty("name").Value  # 直接访问

# 使用框架（自动转换）
entity.name                       # ✅ 自动调用 GetProperty("name").Value
entity.cross_associations         # ✅ 自动转换为 crossAssociations
entity.generalization             # ✅ 返回封装后的对象
entity.attributes                # ✅ 返回封装后的列表
```

### 5.5 多态方法

```python
def get_summary(self):
    """[多态方法] 默认摘要实现，子类可覆盖"""
    name_val = ""
    try:
        name_val = self.name
    except:
        pass
    return f"[{self.type_name}] {name_val}".strip()

def __str__(self):
    """字符串表示"""
    return self.get_summary()
```

**子类覆盖示例**:
```python
@MendixMap("DomainModels$Attribute")
class DomainModels_Attribute(MendixElement):
    def get_summary(self):
        doc = f" // {self.documentation}" if self.documentation else ""
        return f"- {self.name}: {self.type}{doc}"
```

---

## 6. 类型映射系统

### 6.1 注册机制

```python
# 全局注册表
_MENDIX_TYPE_REGISTRY = {}

def MendixMap(mendix_type_str):
    """装饰器：建立 Mendix 类型与 Python 类的映射"""
    def decorator(cls):
        _MENDIX_TYPE_REGISTRY[mendix_type_str] = cls
        return cls
    return decorator
```

### 6.2 使用示例

```python
@MendixMap("DomainModels$Entity")
class DomainModels_Entity(MendixElement):
    def is_persistable(self):
        # 自定义方法
        gen = self.generalization
        if not gen.is_valid:
            return True
        # ...
```

### 6.3 映射流程

```
ElementFactory.create(raw_obj, ctx)
    │
    ├─→ raw_obj.Type = "DomainModels$Entity"
    │
    ├─→ _MENDIX_TYPE_REGISTRY.get("DomainModels$Entity")
    │       │
    │       └─→ 返回 DomainModels_Entity 类
    │
    └─→ DomainModels_Entity(raw_obj, ctx)
```

---

## 7. 包装类层次结构

### 7.1 类别划分

#### 7.1.1 Projects 模块
```python
@MendixMap("Projects$Module")
class Projects_Module(MendixElement):
    def get_domain_model(self): ...
    def find_microflow(self, mf_name): ...
    def find_workflow(self, workflow_name): ...

@MendixMap("Projects$Folder")
class Projects_Folder(MendixElement):
    """文件夹包装类"""
    pass
```

#### 7.1.2 DomainModels 模块
```python
@MendixMap("DomainModels$Entity")
class DomainModels_Entity(MendixElement):
    def is_persistable(self): ...

@MendixMap("DomainModels$Association")
class DomainModels_Association(MendixElement):
    def get_info(self, lookup): ...

@MendixMap("DomainModels$Attribute")
class DomainModels_Attribute(MendixElement):
    def get_summary(self): ...

# 属性类型
@MendixMap("DomainModels$StringAttributeType")
class DomainModels_StringAttributeType(MendixElement):
    def __str__(self): return f"String({self.length})"

@MendixMap("DomainModels$IntegerAttributeType")
class DomainModels_IntegerAttributeType(MendixElement):
    def __str__(self): return "Integer"
```

#### 7.1.3 Microflows 模块
```python
@MendixMap("Microflows$ActionActivity")
class Microflows_ActionActivity(MendixElement):
    def get_summary(self): ...

@MendixMap("Microflows$MicroflowCallAction")
class Microflows_MicroflowCallAction(MendixElement):
    def get_summary(self): ...

@MendixMap("Microflows$RetrieveAction")
class Microflows_RetrieveAction(MendixElement):
    def get_summary(self): ...
```

#### 7.1.4 Pages 模块
```python
# 基础类
@MendixMap("Pages$Widget")
class Pages_Widget(MendixElement):
    """所有组件的基类"""
    pass

@MendixMap("Pages$ClientAction")
class Pages_ClientAction(MendixElement):
    """客户端动作基类"""
    pass

# 具体组件
@MendixMap("Pages$CustomWidget")
class Pages_CustomWidget(Pages_Widget):
    """自定义组件"""
    pass

@MendixMap("Pages$ActionButton")
class Pages_ActionButton(Pages_Widget):
    """按钮组件"""
    pass

@MendixMap("Pages$Page")
class Pages_Page(MendixElement):
    """页面"""
    pass
```

#### 7.1.5 Workflows 模块
```python
@MendixMap("Workflows$Workflow")
class Workflows_Workflow(MendixElement):
    """工作流"""
    pass

@MendixMap("Workflows$SingleUserTaskActivity")
class Workflows_SingleUserTaskActivity(MendixElement):
    """用户任务活动"""
    pass

@MendixMap("Workflows$ExclusiveSplitActivity")
class Workflows_ExclusiveSplitActivity(MendixElement):
    """分支活动"""
    pass
```

### 7.2 继承层次

```
MendixElement (根)
    │
    ├─→ Pages_Widget (组件基类)
    │       ├─→ Pages_DivContainer
    │       ├─→ Pages_LayoutGrid
    │       ├─→ Pages_CustomWidget
    │       └─→ Pages_ActionButton
    │
    ├─→ Pages_ClientAction (动作基类)
    │       ├─→ Pages_NoClientAction
    │       └─→ Pages_CallNanoflowClientAction
    │
    ├─→ Pages_DesignPropertyValue (设计属性基类)
    │       ├─→ Pages_OptionDesignPropertyValue
    │       ├─→ Pages_ToggleDesignPropertyValue
    │       └─→ Pages_CompoundDesignPropertyValue
    │
    └─→ 具体类型类
            ├─→ DomainModels_Entity
            ├─→ Microflows_MicroflowCallAction
            └─→ ...
```

---

## 8. 扩展指南

### 8.1 添加新的类型映射

#### 步骤 1: 确定类型名称
```python
# 从原始对象获取
obj.Type  # 例如 "MyModule$MyType"
```

#### 步骤 2: 创建包装类
```python
@MendixMap("MyModule$MyType")
class MyModule_MyType(MendixElement):
    """类型文档说明"""

    # 添加自定义方法
    def custom_method(self):
        # 访问属性使用 self.property_name
        value = self.some_property
        return value

    # 覆盖多态方法
    def get_summary(self):
        return f"Custom: {self.name}"
```

#### 步骤 3: 使用
```python
# ElementFactory 会自动识别并创建该类型
obj = ElementFactory.create(raw_obj, ctx)
# obj 的类型是 MyModule_MyType
result = obj.custom_method()
```

### 8.2 添加业务分析器

参考框架中的 `Analyzer` 类：

```python
class MyAnalyzer:
    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name):
        # 1. 查找模块
        module = self.ctx.find_module(module_name)
        if not module:
            return

        # 2. 记录日志
        self.ctx.log(f"# MY ANALYSIS: {module.name}\n")

        # 3. 访问数据
        items = module._raw.GetUnitsOfType("MyModule$ItemType")
        for item in items:
            wrapped = ElementFactory.create(item, self.ctx)
            # 处理 wrapped...

        # 4. 返回或发送日志
        report = self.ctx.flush_logs()
        return report
```

### 8.3 最佳实践

#### ✅ DO
- 使用 `snake_case` 访问属性
- 依赖自动类型封装
- 使用 `is_valid` 检查对象有效性
- 覆盖 `get_summary()` 提供友好输出
- 在子类添加业务方法
- 使用缓存优化性能

#### ❌ DON'T
- 直接访问 `_raw` (除非必要)
- 重复实现已有的属性转换逻辑
- 忘记处理 None 情况
- 创建无限递归的属性访问

### 8.4 性能优化

#### 缓存属性访问
```python
class MyWrapper(MendixElement):
    def expensive_computation(self):
        # 使用缓存
        if 'expensive_result' in self._cache:
            return self._cache['expensive_result']

        result = # ... 复杂计算
        self._cache['expensive_result'] = result
        return result
```

#### 预建查找表
```python
class MyContext(MendixContext):
    def __init__(self, model, root):
        super().__init__(model, root)
        self._my_cache = {}

    def find_something(self, key):
        if key not in self._my_cache:
            # 首次查找并缓存
            self._my_cache[key] = self._expensive_lookup(key)
        return self._my_cache[key]
```

---

## 9. 完整示例

### 9.1 创建新的分析器

```python
class SecurityAnalyzer:
    """分析微流中的安全模式"""

    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name):
        module = self.ctx.find_module(module_name)
        if not module:
            self.ctx.log(f"❌ Module not found: {module_name}")
            return

        self.ctx.log(f"# SECURITY ANALYSIS: {module.name}\n")

        # 分析所有微流
        microflows = module._raw.GetUnitsOfType("Microflows$Microflow")
        for mf in microflows:
            self._analyze_microflow(ElementFactory.create(mf, self.ctx))

        return self.ctx.flush_logs()

    def _analyze_microflow(self, mf):
        """分析单个微流"""
        self.ctx.log(f"## Microflow: {mf.name}")

        # 检查是否有未验证的输入
        # ... 分析逻辑

        # 检查是否有硬编码的凭证
        # ... 分析逻辑
```

### 9.2 创建新的包装类

```python
@MendixMap("Microflows$JavaActionCallAction")
class Microflows_JavaActionCallAction(MendixElement):
    """Java 动作调用"""

    def get_summary(self):
        action = self.java_action
        params = []
        if self.parameter_mappings:
            for m in self.parameter_mappings:
                params.append(f"{m.parameter}={m.argument}")
        param_str = f"({', '.join(params)})" if params else "()"
        return f"☕ Java: {action}{param_str}"

    def is_deprecated(self):
        """检查是否使用了过时的 API"""
        # 自定义业务逻辑
        return "Legacy" in self.java_action
```

---

## 10. 快速参考

### 10.1 属性访问模式

| Python 属性 | SDK 调用 | 返回类型 |
|------------|----------|---------|
| `obj.name` | `obj.GetProperty("name").Value` | `str` |
| `obj.items` | `obj.GetProperty("items").GetValues()` | `List[MendixElement]` |
| `obj.parent` | `ElementFactory.create(obj.GetProperty("parent").Value, ctx)` | `MendixElement` |
| `obj.id` | `obj._raw.ID.ToString()` | `str` |
| `obj.type_name` | `obj._raw.Type.split("$")[-1]` | `str` |

### 10.2 常用方法

| 方法 | 描述 | 示例 |
|------|------|------|
| `ctx.log(msg, indent)` | 记录日志 | `ctx.log("Item", indent=1)` |
| `ctx.find_module(name)` | 查找模块 | `mod = ctx.find_module("MyModule")` |
| `ElementFactory.create(raw, ctx)` | 创建包装对象 | `obj = ElementFactory.create(raw, ctx)` |
| `obj.get_summary()` | 获取摘要 | `print(obj.get_summary())` |
| `obj.is_valid` | 检查有效性 | `if obj.is_valid:` |

---

## 11. 附录：已知类型映射表

完整的类型映射表请参见 `debug2.py` 源码，以下是分类清单：

### Projects (2个)
- `Projects$Module`
- `Projects$Folder`

### DomainModels (20+个)
- `DomainModels$Entity`
- `DomainModels$Association`
- `DomainModels$CrossAssociation`
- `DomainModels$Attribute`
- `DomainModels$*AttributeType` (各种属性类型)

### Microflows (10+个)
- `Microflows$ActionActivity`
- `Microflows$MicroflowCallAction`
- `Microflows$RetrieveAction`
- `Microflows$CreateVariableAction`
- `Microflows$ChangeVariableAction`
- `Microflows$ExclusiveSplit`
- `Microflows$EndEvent`

### Pages (50+个)
- `Pages$Page`
- `Pages$Layout`
- `Pages$Widget` (基类)
- `Pages$ClientAction` (基类)
- `Pages$CustomWidget`
- `Pages$ActionButton`
- `Pages$DivContainer`
- `Pages$LayoutGrid`
- ... 各种组件

### Workflows (15+个)
- `Workflows$Workflow`
- `Workflows$SingleUserTaskActivity`
- `Workflows$MultiUserTaskActivity`
- `Workflows$ExclusiveSplitActivity`
- `Workflows$ParallelSplitActivity`
- ... 各种活动

### DataTypes (5+个)
- `DataTypes$StringType`
- `DataTypes$IntegerType`
- `DataTypes$BooleanType`
- `DataTypes$VoidType`
- ... 各种数据类型

---

**文档版本**: 1.0
**最后更新**: 基于 `debug2.py` 提取
**维护者**: 框架开发团队
