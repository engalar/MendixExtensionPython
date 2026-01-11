import os
import clr
import traceback
from System import Exception as SystemException

clr.AddReference("Mendix.StudioPro.ExtensionsAPI")
from Mendix.StudioPro.ExtensionsAPI.Model.UntypedModel import PropertyType

# ==============================================================================
# 1. 核心框架 (Core Framework)
# ==============================================================================

# region 1. 核心框架 (Core Framework)
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


# endregion

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

# region 2.1 Projects
# endregion

# endregion


# region 3. 业务逻辑层 (Business Logic)
class DomainModelAnalyzer:
    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name):
        module = self.ctx.find_module(module_name)
        if not module:
            return

        self.ctx.log(f"# DOMAIN MODEL: {module.name}\n")
        dm = module.get_domain_model()
        if not dm.is_valid:
            return

        # 构建局部 Lookup Table，避免全局耦合
        id_map = {}

        # 1. 分析实体
        for ent in dm.entities:
            # 记录 ID 到全名的映射
            id_map[ent.id] = f"{module.name}.{ent.name}"

            p_tag = " [P]" if ent.is_persistable() else " [NP]"
            gen_info = (
                f" extends {ent.generalization.generalization}"
                if ent.generalization.type_name == "Generalization"
                else ""
            )
            self.ctx.log(f"## Entity: {ent.name}{p_tag}{gen_info}")

            if ent.documentation:
                self.ctx.log(f"> {ent.documentation}")
            for attr in ent.attributes:
                self.ctx.log(attr.get_summary(), indent=1)
            self.ctx.log("")

        # 2. 分析关联关系 (使用 get_info 传递查找表)
        if dm.associations:
            self.ctx.log("## Associations (Internal)")
            for assoc in dm.associations:
                self.ctx.log(assoc.get_info(id_map))
            self.ctx.log("")

        if dm.cross_associations:
            self.ctx.log("## Associations (Cross)")
            for assoc in dm.cross_associations:
                self.ctx.log(assoc.get_info(id_map))
            self.ctx.log("")


class MicroflowAnalyzer:
    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name, mf_name):
        module = self.ctx.find_module(module_name)
        if not module:
            return
        mf = module.find_microflow(mf_name)
        if not mf.is_valid:
            return

        # 修改点1：打印全名
        self.ctx.log(f"# MICROFLOW: {module_name}.{mf.name}\n```")

        nodes = {obj.id: obj for obj in mf.object_collection.objects}
        adj = {}
        for flow in mf.flows:
            src, dst = str(flow.origin), str(flow.destination)
            if src not in adj:
                adj[src] = []
            adj[src].append((flow, dst))

        start_node = next(
            (n for n in nodes.values() if "StartEvent" in n.type_name), None
        )
        if not start_node:
            return

        stack = [(start_node.id, 0, "")]
        visited = set()

        while stack:
            node_id, indent, flow_label = stack.pop()
            node = nodes.get(node_id)
            if not node:
                continue

            label_str = f"--({flow_label})--> " if flow_label else ""
            self.ctx.log(f"{label_str}{node.get_summary()}", indent=indent)

            if node_id in visited:
                self.ctx.log("└─ (Jump/Loop)", indent=indent + 1)
                continue
            visited.add(node_id)

            out_flows = adj.get(node_id, [])
            # 修改点2：同一 flow 不增加缩进，只有分叉(Condition)才增加
            has_branches = len(out_flows) > 1

            for flow, target_id in reversed(out_flows):
                case_val = ""
                if has_branches and len(flow.case_values) > 0:
                    cv = flow.case_values[0]
                    case_val = getattr(cv, "value", cv.type_name)

                # 如果是单线流，indent不变；如果是分叉流，indent+1
                new_indent = indent + 1 if has_branches else indent
                stack.append((target_id, new_indent, case_val))

        self.ctx.log(f"```")


class PageAnalyzer:
    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name, page_name):
        module = self.ctx.find_module(module_name)
        if not module:
            return

        # 在模块中查找页面
        raw_page = next(
            (
                p
                for p in module._raw.GetUnitsOfType("Pages$Page")
                if p.Name == page_name
            ),
            None,
        )
        if not raw_page:
            self.ctx.log(f"❌ Page not found: {module_name}.{page_name}")
            return

        page = ElementFactory.create(raw_page, self.ctx)
        self.ctx.log(f"# PAGE: {module_name}.{page.name}\n")

        # 遍历布局插槽 (Layout Arguments) 中的组件
        if page.layout_call:
            for arg in page.layout_call.arguments:
                self.ctx.log(f"## Placeholder: {arg.parameter}")
                for widget in arg.widgets:
                    self._render_widget(widget, 1)

    def _render_widget(self, w, indent):
        # 获取组件基本信息
        name_str = f" ({w.name})" if hasattr(w, "name") and w.name else ""
        self.ctx.log(f"- [{w.type_name}]{name_str}", indent)

        # 递归处理容器类组件
        # 1. 通用 widgets 列表 (DivContainer, ScrollContainer 等)
        if hasattr(w, "widgets"):
            for child in w.widgets:
                self._render_widget(child, indent + 1)
        # 2. 布局表格 (LayoutGrid)
        elif hasattr(w, "rows"):
            for row in w.rows:
                for col in row.columns:
                    for child in col.widgets:
                        self._render_widget(child, indent + 1)
        # 3. 列表/数据容器 (ListView, DataView)
        elif hasattr(w, "contents") and w.type_name in [
            "ListView",
            "DataView",
            "TemplateGrid",
        ]:
            for child in w.contents.widgets:
                self._render_widget(child, indent + 1)


class WorkflowAnalyzer:
    def __init__(self, context):
        self.ctx = context

    def execute(self, module_name, wf_name):
        module = self.ctx.find_module(module_name)
        if not module:
            return
        wf = module.find_workflow(wf_name)
        if not wf or not wf.is_valid:
            self.ctx.log(f"❌ Workflow not found: {module_name}.{wf_name}")
            return

        self.ctx.log(f"# WORKFLOW: {module_name}.{wf.name}\n```")
        self._render_flow(wf.flow, 0)
        self.ctx.log(f"```")

    def _render_flow(self, flow, indent):
        if not flow or not flow.is_valid:
            return

        for act in flow.activities:
            # 获取标题和名称
            caption = act.caption if hasattr(act, "caption") else ""
            name = f"({act.name})" if hasattr(act, "name") else ""
            self.ctx.log(f"- [{act.type_name}] {caption} {name}".strip(), indent)

            # 递归处理分支 (Outcomes)
            if hasattr(act, "outcomes"):
                # 仅一个outcome且activities为空,可视为无outcome
                if len(act.outcomes)==1 and len(act.outcomes[0].flow.activities) == 0:
                    continue
                for outcome in act.outcomes:
                    val = getattr(outcome, "value", "Outcome")
                    self.ctx.log(f" └─ Case: {val}", indent)
                    # 如果分支有后续 Flow，递归打印
                    if hasattr(outcome, "flow"):
                        self._render_flow(outcome.flow, indent + 2)

class ModuleTreeAnalyzer:
    def __init__(self, context):
        self.ctx = context
        # 定义需要展示在树状结构中的文档类型映射
        self.alias_map = {
            "Microflows$Microflow": "Microflow",
            "Pages$Page": "Page",
            "Workflows$Workflow": "Workflow",
            "Nanoflows$Nanoflow": "Nanoflow",
            "Constants$Constant": "Constant",
            "Enumerations$Enumeration": "Enumeration"
        }

    def execute(self, module_name):
        module = self.ctx.find_module(module_name)
        if not module: return

        self.ctx.log(f"# MODULE STRUCTURE: {module.name}\n```")
        # 从模块根部开始递归
        self._render_container(module._raw, 0)
        self.ctx.log(f"```")

    def _render_container(self, container_raw, indent):
        """核心逻辑：获取所有单元，过滤掉文件夹重叠和无名单元"""
        
        # 1. 获取该容器下所有的单元 (递归获取所有)
        all_units = list(container_raw.GetUnits())
        
        # 2. 识别所有“非直接”的后代 ID
        # 我们需要先找出所有文件夹，再看这些文件夹里面包含了什么
        all_sub_folders = [u for u in all_units if u.Type == "Projects$Folder"]
        
        descendant_ids = set()
        for sub_f in all_sub_folders:
            # 获取该文件夹下的所有子孙单元并记录其 ID
            for grand_unit in sub_f.GetUnits():
                descendant_ids.add(grand_unit.ID.ToString())

        # 3. 过滤出当前层级的“直接”单元
        # 条件：ID 不在后代集合中，且 Name 属性不为空
        direct_units = [
            u for u in all_units 
            if u.ID.ToString() not in descendant_ids and getattr(u, "Name", None)
        ]

        # 4. 分离文件夹与文档 (用于分别渲染)
        # direct_folders 仅包含 Projects$Folder
        direct_folders = [u for u in direct_units if u.Type == "Projects$Folder"]
        # direct_docs 包含除了文件夹以外的所有东西
        direct_docs = [u for u in direct_units if u.Type != "Projects$Folder"]

        # 5. 渲染文档
        # 按名称排序，并处理别名
        for d in sorted(direct_docs, key=lambda x: x.Name):
            full_type = d.Type
            type_label = self.alias_map.get(full_type, full_type.split('$')[-1])
            self.ctx.log(f"[{type_label}] {d.Name}", indent)

        # 6. 渲染文件夹并递归
        for f in sorted(direct_folders, key=lambda x: x.Name):
            self.ctx.log(f"📁 {f.Name}", indent)
            self._render_container(f, indent + 1)

# endregion

# region 4. 执行入口 (Execution)
try:
    PostMessage("backend:clear", "")
    ctx = MendixContext(currentApp, root)

    # 分析模块文件结构
    target_mod = "AltairIntegration" # 替换为你的模块名
    ModuleTreeAnalyzer(ctx).execute(target_mod)

    # 分析领域模型
    DomainModelAnalyzer(ctx).execute("AmazonBedrockConnector")  # 替换为你的模块名

    # 分析微流
    MicroflowAnalyzer(ctx).execute(
        "AltairIntegration", "Tool_SparqlConverter"
    )  # 替换为你的微流
    # 分析页面
    PageAnalyzer(ctx).execute("Evora_UI", "Login")
    # 参数 1: 模块名, 参数 2: 工作流名
    WorkflowAnalyzer(ctx).execute("AltairIntegration", "WF_ScheduleTechnicianAppointment")
    # --- 获取分析报告内容 ---
    final_report = ctx.flush_logs()

    # --- 保存并打开文件 ---
    try:
        # 1. 构建文件路径 (用户根目录/Mendix_Report.md)
        user_home = os.path.expanduser("~")
        file_path = os.path.join(user_home, "Mendix_Analysis_Report.md")

        # 2. 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_report)

        PostMessage("backend:info", f"✅ Report saved to: {file_path}")

        # 3. 使用系统默认程序打开文件 (仅限 Windows)
        if os.name == "nt":
            os.startfile(file_path)
        else:
            # 兼容其他系统(如果适用)
            import subprocess

            subprocess.call(
                ("open" if os.name == "posix" else "start", file_path), shell=True
            )

    except Exception as file_err:
        PostMessage("backend:error", f"File operation failed: {str(file_err)}")

    # 依然在 Studio Pro 后端控制台打印一份
    PostMessage("backend:info", final_report)

except Exception as e:
    PostMessage("backend:error", f"Error: {str(e)}\n{traceback.format_exc()}")
# endregion
