import clr
import traceback
from System import Exception as SystemException

clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
from Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel import PropertyType

# @CORE:UntypedModelWrapper - 核心动态代理框架，提供对 Mendix Untyped Model 的 Pythonic 访问。
# This module provides a dynamic proxy framework for interacting with Mendix's Untyped Model API.
# It simplifies property access and type mapping, allowing for a more Pythonic way to navigate the Mendix model.

# ==============================================================================
# 概念解释 (Concept Explanations)
# ==============================================================================
#
# **Untyped Model (非类型化模型):**
#   指通过 `IUntypedModelAccessService` 访问的 Mendix 模型对象。这些对象不具有预定义的 Python 类型，
#   其属性需要通过 `GetProperty("PropertyName").Value` 动态访问。它们是 Mendix SDK 的底层表示，
#   提供了极大的灵活性，但也增加了开发的复杂性。
#
# **Typed Model (类型化模型):**
#   指 Mendix API 中预定义了特定类型和接口的模型对象（例如 `IDomainModelService.CreateEntity()` 返回的对象）。
#   这些对象具有明确的属性和方法签名，易于使用和IDE类型检查。
#
# **Wrapped Model (包装模型 / 代理模型):**
#   指本框架中 `MendixElement` 及其子类。它们封装了 Untyped Model 对象，
#   通过 Python 的 `__getattr__` 魔法方法，将 `snake_case` 属性名自动映射到 Mendix SDK 的 `CamelCase` 属性，
#   并自动将返回的 Untyped Model 对象再次封装为 Wrapped Model。这极大地简化了 Untyped Model 的使用，
#   使其行为类似于 Typed Model，但仍保持了 Untyped Model 的动态性。
#
# ==============================================================================


_MENDIX_TYPE_REGISTRY = {}


def MendixMap(mendix_type_str):
    """装饰器：建立 Mendix 类型与 Python 类的映射"""

    def decorator(cls):
        _MENDIX_TYPE_REGISTRY[mendix_type_str] = cls
        return cls

    return decorator


class MendixContext:
    """运行上下文：负责日志管理、全局搜索缓存和 Unit 查找"""

    def __init__(self, model, root_node):
        self.root = root_node
        self.model = model
        self.log_buffer = []
        self._entity_qname_cache = {}
        self._is_initialized = False

    def _ensure_initialized(self):
        if self._is_initialized:
            return
        # 预扫描所有模块和实体，建立 O(1) 查询表
        modules = self.root.GetUnitsOfType("Projects$Module")
        for mod in modules:
            dm_units = mod.GetUnitsOfType("DomainModels$DomainModel")
            for dm in dm_units:
                # 注意：此处使用原始 SDK 访问以防初始化循环
                ents = dm.GetProperty("entities").GetValues()
                for e in ents:
                    qname = f"{mod.Name}.{e.GetProperty('name').Value}"
                    self._entity_qname_cache[qname] = e
        self._is_initialized = True

    def log(self, msg, indent=0):
        prefix = "  " * indent
        self.log_buffer.append(f"{prefix}{msg}")

    def flush_logs(self):
        return "\n".join(self.log_buffer)

    def find_module(self, module_name):
        modules = list(self.root.GetUnitsOfType("Projects$Module"))
        raw = next((m for m in modules if m.Name == module_name), None)
        return ElementFactory.create(raw, self) if raw else None

    def find_entity_by_qname(self, qname):
        self._ensure_initialized()
        raw = self._entity_qname_cache.get(qname)
        return ElementFactory.create(raw, self) if raw else None


class ElementFactory:
    """工厂类：负责对象的动态封装"""

    @staticmethod
    def create(raw_obj, context):
        if raw_obj is None:
            return MendixElement(None, context)

        # 处理基础类型
        if isinstance(raw_obj, (str, int, float, bool)):
            return raw_obj

        try:
            full_type = raw_obj.Type
        except AttributeError:
            return MendixElement(raw_obj, context)

        target_cls = _MENDIX_TYPE_REGISTRY.get(full_type, MendixElement)
        return target_cls(raw_obj, context)


class MendixElement:
    """动态代理基类：支持属性缓存、多态摘要和 snake_case 自动转换"""

    def __init__(self, raw_obj, context):
        self._raw = raw_obj
        self.ctx = context
        self._cache = {}  # 性能优化：缓存属性结果

    @property
    def is_valid(self):
        return self._raw is not None

    @property
    def id(self):
        return self._raw.ID.ToString() if self.is_valid else "0"

    @property
    def type_name(self):
        if not self.is_valid:
            return "Null"
        return self._raw.Type.split("$")[-1]

    def __getattr__(self, name):
        """核心魔法：映射 snake_case 到 CamelCase 并自动封装结果"""
        if not self.is_valid:
            return None
        if name in self._cache:
            return self._cache[name]

        # 1. 转换命名: cross_associations -> crossAssociations
        parts = name.split("_")
        camel_name = parts[0] + "".join(x.title() for x in parts[1:])

        # 2. 从 SDK 获取
        prop = self._raw.GetProperty(camel_name)
        if prop is None:
            prop = self._raw.GetProperty(name)  # 备用尝试原始名

        if prop is None:
            raise AttributeError(f"'{self.type_name}' has no property '{name}'")

        # 3. 处理并缓存结果
        if prop.IsList:
            result = [ElementFactory.create(v, self.ctx) for v in prop.GetValues()]
        else:
            val = prop.Value
            if hasattr(val, "Type") or hasattr(val, "ID"):
                result = ElementFactory.create(val, self.ctx)
            elif isinstance(val, str):
                result = val.replace("\r\n", "\\n").strip()
            else:
                result = val

        if name=='documentation':
            if len(result) > 30:
                result = result[:30] + "..."
        self._cache[name] = result
        return result

    def get_summary(self):
        """[多态方法] 默认摘要实现"""
        name_val = ""
        try:
            name_val = self.name
        except:
            pass
        return f"[{self.type_name}] {name_val}".strip()

    def __str__(self):
        return self.get_summary()


# region 2. 类型定义 (Wrapper Classes)


# region 2.1 Projects
@MendixMap("Projects$Module")
class Projects_Module(MendixElement):
    def get_domain_model(self):
        raw_dm = next(iter(self._raw.GetUnitsOfType("DomainModels$DomainModel")), None)
        return ElementFactory.create(raw_dm, self.ctx)

    def find_microflow(self, mf_name):
        raw_mf = next(
            (
                m
                for m in self._raw.GetUnitsOfType("Microflows$Microflow")
                if m.Name == mf_name
            ),
            None,
        )
        return ElementFactory.create(raw_mf, self.ctx)

    def find_workflow(self, workflow_name):
        raw_wf = next(
            (
                w
                for w in self._raw.GetUnitsOfType("Workflows$Workflow")
                if w.Name == workflow_name
            ),
            None,
        )
        return ElementFactory.create(raw_wf, self.ctx)

@MendixMap("Projects$Folder")
class Projects_Folder(MendixElement):
    """文件夹包装类"""
    pass

# endregion
# region 2.1 DomainModels
@MendixMap("DomainModels$Entity")
class DomainModels_Entity(MendixElement):
    def is_persistable(self):
        gen = self.generalization
        if not gen.is_valid:
            return True  # 默认持久化
        # 如果是 NoGeneralization，看其自身的 persistable 属性
        if gen.type_name == "NoGeneralization":
            return gen.persistable
        # 如果是继承，递归看父类
        parent_qname = gen.generalization
        parent = self.ctx.find_entity_by_qname(parent_qname)
        return parent.is_persistable() if parent and parent.is_valid else True


@MendixMap("DomainModels$Association")
class DomainModels_Association(MendixElement):
    def get_info(self, lookup):
        p_name = lookup.get(str(self.parent), "Unknown")
        c_name = lookup.get(str(self.child), "Unknown")
        # 省略模块名
        return f"- [Assoc] {self.name}: {p_name.split('.')[-1]} -> {c_name.split('.')[-1]} [Type:{self.type}, Owner:{self.owner}]"


@MendixMap("DomainModels$CrossAssociation")
class DomainModels_CrossAssociation(MendixElement):
    def get_info(self, lookup):
        p_name = lookup.get(str(self.parent), "Unknown")
        # CrossAssociation 的 child 属性通常已经是字符串全名
        return f"- [Cross] {self.name}: {p_name.split('.')[-1]} -> {self.child} [Type:{self.type}, Owner:{self.owner}]"


@MendixMap("DomainModels$AssociationOwner")
class DomainModels_AssociationOwner(MendixElement):
    def __str__(self):
        return self.type_name


@MendixMap("DomainModels$AssociationCapabilities")
class DomainModels_AssociationCapabilities(MendixElement):
    def __str__(self):
        return self.type_name


# --- 属性类型定义 (Attribute Types) ---
@MendixMap("DomainModels$Attribute")
class DomainModels_Attribute(MendixElement):
    def get_summary(self):
        doc = f" // {self.documentation}" if self.documentation else ""
        return f"- {self.name}: {self.type}{doc}"


@MendixMap("DomainModels$EnumerationAttributeType")
class DomainModels_EnumerationAttributeType(MendixElement):
    def __str__(self):
        # enumeration 是属性，返回枚举的全名
        return f"Enum({self.enumeration})"


@MendixMap("DomainModels$StringAttributeType")
class DomainModels_StringAttributeType(MendixElement):
    def __str__(self):
        return f"String({self.length if self.length > 0 else 'Unlimited'})"


@MendixMap("DomainModels$IntegerAttributeType")
class DomainModels_IntegerAttributeType(MendixElement):
    def __str__(self):
        return "Integer"


@MendixMap("DomainModels$DateTimeAttributeType")
class DomainModels_DateTimeAttributeType(MendixElement):
    def __str__(self):
        return "DateTime"


@MendixMap("DomainModels$BooleanAttributeType")
class DomainModels_BooleanAttributeType(MendixElement):
    def __str__(self):
        return "Boolean"


@MendixMap("DomainModels$DecimalAttributeType")
class DomainModels_DecimalAttributeType(MendixElement):
    def __str__(self):
        return "Decimal"


@MendixMap("DomainModels$LongAttributeType")
class DomainModels_LongAttributeType(MendixElement):
    def __str__(self):
        return "Long"


# endregion
# region 2.1 Microflows
@MendixMap("Microflows$ActionActivity")
class Microflows_ActionActivity(MendixElement):
    def get_summary(self):
        # Activity 代理其内部 Action 的摘要
        return self.action.get_summary()


@MendixMap("Microflows$MicroflowCallAction")
class Microflows_MicroflowCallAction(MendixElement):
    def get_summary(self):
        call = self.microflow_call
        target = call.microflow if call else "Unknown"

        # 解析参数映射
        params = []
        if call and call.parameter_mappings:
            for m in call.parameter_mappings:
                p_name = m.parameter.split(".")[-1]  # 只取参数名
                params.append(f"{p_name}={m.argument}")
        param_str = f"({', '.join(params)})" if params else "()"

        out = f" -> ${self.output_variable_name}" if self.use_return_variable else ""
        return f"⚡ Call: {target}{param_str}{out}"


@MendixMap("Microflows$RetrieveAction")
class Microflows_RetrieveAction(MendixElement):
    def get_summary(self):
        src = self.retrieve_source
        entity = getattr(src, "entity", "Unknown")
        xpath = getattr(src, "x_path_constraint", "")
        xpath_str = f" [{xpath}]" if xpath else ""
        return f"🔍 Retrieve: {entity}{xpath_str} -> ${self.output_variable_name}"


@MendixMap("Microflows$CreateVariableAction")
class Microflows_CreateVariableAction(MendixElement):
    def get_summary(self):
        value_format = self.initial_value.replace("\n", "\\n")
        return (
            f"💎 Create: ${self.variable_name} ({self.variable_type}) = {value_format}"
        )


@MendixMap("Microflows$ChangeVariableAction")
class Microflows_ChangeVariableAction(MendixElement):
    def get_summary(self):
        return f"📝 Change: ${self.variable_name} = {self.value}"


@MendixMap("Microflows$ExclusiveSplit")
class Microflows_ExclusiveSplit(MendixElement):
    def get_summary(self):
        expr = self.split_condition.expression
        caption = f" [{self.caption}]" if self.caption and self.caption != expr else ""
        return f"❓ Split{caption}: {expr}"


@MendixMap("Microflows$EndEvent")
class Microflows_EndEvent(MendixElement):
    def get_summary(self):
        ret = f" (Return: {self.return_value})" if self.return_value else ""
        return f"🛑 End{ret}"


# endregion
# region 2.1 DataTypes
# --- 数据类型定义 ---
@MendixMap("DataTypes$StringType")
class DataTypes_StringType(MendixElement):
    def __str__(self):
        return "String"


@MendixMap("DataTypes$VoidType")
class DataTypes_VoidType(MendixElement):
    def __str__(self):
        return "Void"


@MendixMap("DataTypes$BooleanType")
class DataTypes_BooleanType(MendixElement):
    def __str__(self):
        return "Boolean"


# endregion

# region 2.1 Pages
from typing import List, Optional


# Base Classes for Polymorphism


@MendixMap("Pages$Widget")
class Pages_Widget(MendixElement):
    # Base class for all widgets
    pass


@MendixMap("Pages$ClientAction")
class Pages_ClientAction(MendixElement):
    # .disabled_during_execution:bool
    pass


@MendixMap("Pages$DesignPropertyValue")
class Pages_DesignPropertyValue(MendixElement):
    # Base class for design properties
    pass


@MendixMap("Pages$Icon")
class Pages_Icon(MendixElement):
    # Base class for icons
    pass


# --- Core Page Structure ---


@MendixMap("Pages$Page")
class Pages_Page(MendixElement):
    # .layout_call:Pages_LayoutCall
    # .layout:str
    # .title:Texts_Text
    # .appearance:Pages_Appearance
    # .name:str
    # .excluded:bool
    # .export_level:str
    # .canvas_width:int
    # .canvas_height:int
    # .allowed_roles:List[str]
    # .popup_width:int
    # .popup_height:int
    # .popup_resizable:bool
    # .mark_as_used:bool
    pass


@MendixMap("Pages$LayoutCall")
class Pages_LayoutCall(MendixElement):
    # .arguments:List[Pages_LayoutCallArgument]
    # .layout:str
    pass


@MendixMap("Pages$LayoutCallArgument")
class Pages_LayoutCallArgument(MendixElement):
    # .widgets:List[Pages_Widget]
    # .parameter:str
    pass


@MendixMap("Pages$Appearance")
class Pages_Appearance(MendixElement):
    # .class_:str
    # .design_properties:List[Pages_DesignPropertyValue]
    pass


# --- Design Properties ---


@MendixMap("Pages$OptionDesignPropertyValue")
class Pages_OptionDesignPropertyValue(Pages_DesignPropertyValue):
    # .option:str
    # .key:str
    pass


@MendixMap("Pages$ToggleDesignPropertyValue")
class Pages_ToggleDesignPropertyValue(Pages_DesignPropertyValue):
    # .key:str
    pass


@MendixMap("Pages$CompoundDesignPropertyValue")
class Pages_CompoundDesignPropertyValue(Pages_DesignPropertyValue):
    # .properties:List[Pages_DesignPropertyValue]
    # .key:str
    pass


# --- Custom Widget Metamodel ---


@MendixMap("Pages$CustomWidget")
class Pages_CustomWidget(Pages_Widget):
    # .appearance:Pages_Appearance
    # .type:Pages_CustomWidgetType
    # .object:Pages_WidgetObject
    # .name:str
    # .tab_index:int
    # .editable:str
    # .widget_id:str
    # .needs_entity_context:bool
    # .plugin_widget:bool
    # .description:str
    # .studio_pro_category:str
    # .studio_category:str
    # .supported_platform:str
    # .offline_capable:bool
    # .help_url:str
    pass


@MendixMap("Pages$CustomWidgetType")
class Pages_CustomWidgetType(MendixElement):
    # .object_type:Pages_WidgetObjectType
    # .widget_id:str
    # .needs_entity_context:bool
    # .plugin_widget:bool
    # .name:str
    # .description:str
    # .studio_pro_category:str
    # .studio_category:str
    # .supported_platform:str
    # .offline_capable:bool
    # .help_url:str
    pass


@MendixMap("Pages$WidgetObjectType")
class Pages_WidgetObjectType(MendixElement):
    # .property_types:List[Pages_WidgetPropertyType]
    pass


@MendixMap("Pages$WidgetPropertyType")
class Pages_WidgetPropertyType(MendixElement):
    # .value_type:Pages_WidgetValueType
    # .key:str
    # .category:str
    # .caption:str
    # .description:str
    # .is_default:bool
    pass


@MendixMap("Pages$WidgetValueType")
class Pages_WidgetValueType(MendixElement):
    # .enumeration_values:List[Pages_WidgetEnumerationValue]
    # .return_type:Pages_WidgetReturnType
    # .type:str
    # .is_list:bool
    # .is_linked:bool
    # .is_meta_data:bool
    # .allow_non_persistable_entities:bool
    # .is_path:str
    # .path_type:str
    # .parameter_is_list:bool
    # .multiline:bool
    # .default_value:str
    # .required:bool
    # .set_label:bool
    # .default_type:str
    pass


@MendixMap("Pages$WidgetEnumerationValue")
class Pages_WidgetEnumerationValue(MendixElement):
    # .key:str
    # .caption:str
    pass


@MendixMap("Pages$WidgetReturnType")
class Pages_WidgetReturnType(MendixElement):
    # .type:str
    # .is_list:bool
    pass


@MendixMap("Pages$WidgetObject")
class Pages_WidgetObject(MendixElement):
    # .properties:List[Pages_WidgetProperty]
    # .type:str
    pass


@MendixMap("Pages$WidgetProperty")
class Pages_WidgetProperty(MendixElement):
    # .value:Pages_WidgetValue
    # .type:str
    pass


@MendixMap("Pages$WidgetValue")
class Pages_WidgetValue(MendixElement):
    # .action:Pages_ClientAction
    # .text_template:Pages_ClientTemplate
    # .translatable_value:Texts_Text
    # .type:str
    # .primitive_value:str
    # .image:str
    # .selection:str
    pass


# --- Actions, Templates, and Text ---


@MendixMap("Pages$NoClientAction")
class Pages_NoClientAction(Pages_ClientAction):
    pass


@MendixMap("Pages$CallNanoflowClientAction")
class Pages_CallNanoflowClientAction(Pages_ClientAction):
    # .nanoflow:str
    # .progress_bar:str
    pass


@MendixMap("Pages$ClientTemplate")
class Pages_ClientTemplate(MendixElement):
    # .template:Texts_Text
    # .fallback:Texts_Text
    pass


@MendixMap("Texts$Text")
class Texts_Text(MendixElement):
    # .translations:List[Texts_Translation]
    pass


@MendixMap("Texts$Translation")
class Texts_Translation(MendixElement):
    # .language_code:str
    # .text:str
    pass


# --- Layout and Container Widgets ---


@MendixMap("Pages$DivContainer")
class Pages_DivContainer(Pages_Widget):
    # .widgets:List[Pages_Widget]
    # .appearance:Pages_Appearance
    # .on_click_action:Pages_ClientAction
    # .name:str
    # .tab_index:int
    # .render_mode:str
    # .screen_reader_hidden:bool
    pass


@MendixMap("Pages$LayoutGrid")
class Pages_LayoutGrid(Pages_Widget):
    # .rows:List[Pages_LayoutGridRow]
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .width:str
    pass


@MendixMap("Pages$LayoutGridRow")
class Pages_LayoutGridRow(MendixElement):
    # .columns:List[Pages_LayoutGridColumn]
    # .appearance:Pages_Appearance
    # .vertical_alignment:str
    # .horizontal_alignment:str
    # .spacing_between_columns:bool
    pass


@MendixMap("Pages$LayoutGridColumn")
class Pages_LayoutGridColumn(MendixElement):
    # .widgets:List[Pages_Widget]
    # .appearance:Pages_Appearance
    # .weight:int
    # .tablet_weight:int
    # .phone_weight:int
    # .preview_width:int
    # .vertical_alignment:str
    pass


# --- Form and Interaction Widgets ---


@MendixMap("Pages$DynamicText")
class Pages_DynamicText(Pages_Widget):
    # .content:Pages_ClientTemplate
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .render_mode:str
    # .native_text_style:str
    pass


@MendixMap("Pages$ValidationMessage")
class Pages_ValidationMessage(Pages_Widget):
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    pass


@MendixMap("Pages$LoginIdTextBox")
class Pages_LoginIdTextBox(Pages_Widget):
    # .label:Texts_Text
    # .placeholder:Texts_Text
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .label_width:int
    pass


@MendixMap("Pages$PasswordTextBox")
class Pages_PasswordTextBox(Pages_Widget):
    # .label:Texts_Text
    # .placeholder:Texts_Text
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .label_width:int
    pass


@MendixMap("Pages$IconCollectionIcon")
class Pages_IconCollectionIcon(Pages_Icon):
    # .image:str
    pass


@MendixMap("Pages$ActionButton")
class Pages_ActionButton(Pages_Widget):
    # .caption:Pages_ClientTemplate
    # .tooltip:Texts_Text
    # .icon:Pages_Icon
    # .action:Pages_ClientAction
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .render_type:str
    # .button_style:str
    # .aria_role:str
    pass


@MendixMap("Pages$LoginButton")
class Pages_LoginButton(Pages_Widget):
    # .caption:Pages_ClientTemplate
    # .tooltip:Texts_Text
    # .appearance:Pages_Appearance
    # .name:str
    # .tab_index:int
    # .render_type:str
    # .button_style:str
    # .validation_message_widget:str
    pass


@MendixMap("Pages$Layout")
class Pages_Layout(MendixElement):
    # .name:str
    # .documentation:str
    # .excluded:bool
    # .export_level:str (Enum: Hidden/Public...)
    # .canvas_width:int
    # .canvas_height:int
    # .content:Pages_WebLayoutContent
    pass


@MendixMap("Pages$WebLayoutContent")
class Pages_WebLayoutContent(MendixElement):
    # .layout_type:str (Enum: Responsive/Legacy...)
    # .layout_call:MendixElement
    # .widgets:List[MendixElement]
    pass


@MendixMap("Pages$SnippetCallWidget")
class Pages_SnippetCallWidget(MendixElement):
    # .name:str
    # .tab_index:int
    # .appearance:Pages_Appearance
    # .snippet_call:Pages_SnippetCall
    pass


@MendixMap("Pages$Placeholder")
class Pages_Placeholder(MendixElement):
    # .name:str
    # .tab_index:int
    # .appearance:Pages_Appearance
    pass


@MendixMap("Pages$Appearance")
class Pages_Appearance(MendixElement):
    # .class:str
    # .style:str
    # .dynamic_classes:str (Expression)
    # .design_properties:List
    pass


@MendixMap("Pages$SnippetCall")
class Pages_SnippetCall(MendixElement):
    # .parameter_mappings:List
    # .snippet:str (Qualified Name)
    pass


# endregion

# region 2.1 Texts
# endregion

# region 2.1 Workflows


from typing import List


# --- Microflows Module ---


@MendixMap("Microflows$StringTemplate")
class Microflows_StringTemplate(MendixElement):
    # .text:str
    pass


@MendixMap("Microflows$Annotation")
class Microflows_Annotation(MendixElement):
    # .description:str
    pass


# --- Pages Module ---


@MendixMap("Pages$PageReference")
class Pages_PageReference(MendixElement):
    pass


# --- Workflows Module ---


@MendixMap("Workflows$Workflow")
class Workflows_Workflow(MendixElement):
    # .parameter:Workflows_WorkflowParameter
    # .flow:Workflows_Flow
    # .workflow_name:Microflows_StringTemplate
    # .workflow_description:Microflows_StringTemplate
    # .name:str
    # .excluded:bool
    # .export_level:str
    # .persistent_id:str
    # .title:str
    pass


@MendixMap("Workflows$WorkflowParameter")
class Workflows_WorkflowParameter(MendixElement):
    # .name:str
    # .entity:str
    pass


@MendixMap("Workflows$Flow")
class Workflows_Flow(MendixElement):
    # .activities:List[MendixElement]
    pass


@MendixMap("Workflows$XPathBasedUserSource")
class Workflows_XPathBasedUserSource(MendixElement):
    pass


@MendixMap("Workflows$UserTaskOutcome")
class Workflows_UserTaskOutcome(MendixElement):
    # .flow:Workflows_Flow
    # .persistent_id:str
    # .value:str
    pass


@MendixMap("Workflows$NoEvent")
class Workflows_NoEvent(MendixElement):
    pass


@MendixMap("Workflows$SingleUserTaskActivity")
class Workflows_SingleUserTaskActivity(MendixElement):
    # .task_page:Pages_PageReference
    # .task_name:Microflows_StringTemplate
    # .task_description:Microflows_StringTemplate
    # .user_source:Workflows_XPathBasedUserSource
    # .outcomes:List[Workflows_UserTaskOutcome]
    # .on_created_event:Workflows_NoEvent
    # .persistent_id:str
    # .name:str
    # .caption:str
    # .auto_assign_single_target_user:bool
    pass


@MendixMap("Workflows$AllUserInput")
class Workflows_AllUserInput(MendixElement):
    pass


@MendixMap("Workflows$ConsensusCompletionCriteria")
class Workflows_ConsensusCompletionCriteria(MendixElement):
    pass


@MendixMap("Workflows$MultiUserTaskActivity")
class Workflows_MultiUserTaskActivity(MendixElement):
    # .task_page:Pages_PageReference
    # .task_name:Microflows_StringTemplate
    # .task_description:Microflows_StringTemplate
    # .user_source:Workflows_XPathBasedUserSource
    # .outcomes:List[Workflows_UserTaskOutcome]
    # .on_created_event:Workflows_NoEvent
    # .target_user_input:Workflows_AllUserInput
    # .completion_criteria:Workflows_ConsensusCompletionCriteria
    # .persistent_id:str
    # .name:str
    # .caption:str
    # .auto_assign_single_target_user:bool
    # .await_all_users:bool
    pass


@MendixMap("Workflows$BooleanConditionOutcome")
class Workflows_BooleanConditionOutcome(MendixElement):
    # .flow:Workflows_Flow
    # .persistent_id:str
    # .value:str
    pass


@MendixMap("Workflows$ExclusiveSplitActivity")
class Workflows_ExclusiveSplitActivity(MendixElement):
    # .outcomes:List[Workflows_BooleanConditionOutcome]
    # .persistent_id:str
    # .name:str
    # .caption:str
    # .expression:str
    pass


@MendixMap("Workflows$ParallelSplitOutcome")
class Workflows_ParallelSplitOutcome(MendixElement):
    # .flow:Workflows_Flow
    # .persistent_id:str
    pass


@MendixMap("Workflows$ParallelSplitActivity")
class Workflows_ParallelSplitActivity(MendixElement):
    # .outcomes:List[Workflows_ParallelSplitOutcome]
    # .persistent_id:str
    # .name:str
    # .caption:str
    pass


@MendixMap("Workflows$WaitForNotificationActivity")
class Workflows_WaitForNotificationActivity(MendixElement):
    # .persistent_id:str
    # .name:str
    # .caption:str
    pass


@MendixMap("Workflows$WaitForTimerActivity")
class Workflows_WaitForTimerActivity(MendixElement):
    # .annotation:Microflows_Annotation
    # .persistent_id:str
    # .name:str
    # .caption:str
    # .delay:str
    pass


@MendixMap("Workflows$CallWorkflowActivity")
class Workflows_CallWorkflowActivity(MendixElement):
    # .persistent_id:str
    # .name:str
    # .caption:str
    # .execute_async:bool
    pass


@MendixMap("Workflows$CallMicroflowTask")
class Workflows_CallMicroflowTask(MendixElement):
    # .persistent_id:str
    # .name:str
    # .caption:str
    pass


# endregion