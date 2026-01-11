# Mendix 模型属性类型索引

> 基于 `debug2.py` 中 `@MendixMap` 类的注释提取的完整属性类型签名

---

## 使用说明

### 类型签名格式

```python
@MendixMap("Module$TypeName")
class Module_TypeName(MendixElement):
    # .property_name:TypeName
    # .list_property:List[TypeName]
```

**类型含义**:
- `str` - 字符串
- `int` - 整数
- `bool` - 布尔值
- `List[X]` - X 类型的列表
- `Module_TypeName` - 对应的 Mendix 对象类型
- `(Enum: ...)` - 枚举值说明
- `(Expression)` - 表达式字符串

---

## 类型索引 (按模块)

### Pages 模块

#### Pages_ClientAction
```python
# .disabled_during_execution:bool
```

#### Pages_Page
```python
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
```

#### Pages_LayoutCall
```python
# .arguments:List[Pages_LayoutCallArgument]
# .layout:str
```

#### Pages_LayoutCallArgument
```python
# .widgets:List[Pages_Widget]
# .parameter:str
```

#### Pages_Appearance
```python
# .class_:str
# .design_properties:List[Pages_DesignPropertyValue]
```

#### Pages_OptionDesignPropertyValue
```python
# .option:str
# .key:str
```

#### Pages_ToggleDesignPropertyValue
```python
# .key:str
```

#### Pages_CompoundDesignPropertyValue
```python
# .properties:List[Pages_DesignPropertyValue]
# .key:str
```

#### Pages_CustomWidget
```python
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
```

#### Pages_CustomWidgetType
```python
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
```

#### Pages_WidgetObjectType
```python
# .property_types:List[Pages_WidgetPropertyType]
```

#### Pages_WidgetPropertyType
```python
# .value_type:Pages_WidgetValueType
# .key:str
# .category:str
# .caption:str
# .description:str
# .is_default:bool
```

#### Pages_WidgetValueType
```python
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
```

#### Pages_WidgetEnumerationValue
```python
# .key:str
# .caption:str
```

#### Pages_WidgetReturnType
```python
# .type:str
# .is_list:bool
```

#### Pages_WidgetObject
```python
# .properties:List[Pages_WidgetProperty]
# .type:str
```

#### Pages_WidgetProperty
```python
# .value:Pages_WidgetValue
# .type:str
```

#### Pages_WidgetValue
```python
# .action:Pages_ClientAction
# .text_template:Pages_ClientTemplate
# .translatable_value:Texts_Text
# .type:str
# .primitive_value:str
# .image:str
# .selection:str
```

#### Pages_NoClientAction
```python
# (继承自 Pages_ClientAction，无额外属性)
```

#### Pages_CallNanoflowClientAction
```python
# .nanoflow:str
# .progress_bar:str
```

#### Pages_ClientTemplate
```python
# .template:Texts_Text
# .fallback:Texts_Text
```

#### Pages_DivContainer
```python
# .widgets:List[Pages_Widget]
# .appearance:Pages_Appearance
# .on_click_action:Pages_ClientAction
# .name:str
# .tab_index:int
# .render_mode:str
# .screen_reader_hidden:bool
```

#### Pages_LayoutGrid
```python
# .rows:List[Pages_LayoutGridRow]
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
# .width:str
```

#### Pages_LayoutGridRow
```python
# .columns:List[Pages_LayoutGridColumn]
# .appearance:Pages_Appearance
# .vertical_alignment:str
# .horizontal_alignment:str
# .spacing_between_columns:bool
```

#### Pages_LayoutGridColumn
```python
# .widgets:List[Pages_Widget]
# .appearance:Pages_Appearance
# .weight:int
# .tablet_weight:int
# .phone_weight:int
# .preview_width:int
# .vertical_alignment:str
```

#### Pages_DynamicText
```python
# .content:Pages_ClientTemplate
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
# .render_mode:str
# .native_text_style:str
```

#### Pages_ValidationMessage
```python
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
```

#### Pages_LoginIdTextBox
```python
# .label:Texts_Text
# .placeholder:Texts_Text
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
# .label_width:int
```

#### Pages_PasswordTextBox
```python
# .label:Texts_Text
# .placeholder:Texts_Text
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
# .label_width:int
```

#### Pages_IconCollectionIcon
```python
# .image:str
```

#### Pages_ActionButton
```python
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
```

#### Pages_LoginButton
```python
# .caption:Pages_ClientTemplate
# .tooltip:Texts_Text
# .appearance:Pages_Appearance
# .name:str
# .tab_index:int
# .render_type:str
# .button_style:str
# .validation_message_widget:str
```

#### Pages_Layout
```python
# .name:str
# .documentation:str
# .excluded:bool
# .export_level:str (Enum: Hidden/Public...)
# .canvas_width:int
# .canvas_height:int
# .content:Pages_WebLayoutContent
```

#### Pages_WebLayoutContent
```python
# .layout_type:str (Enum: Responsive/Legacy...)
# .layout_call:MendixElement
# .widgets:List[MendixElement]
```

#### Pages_SnippetCallWidget
```python
# .name:str
# .tab_index:int
# .appearance:Pages_Appearance
# .snippet_call:Pages_SnippetCall
```

#### Pages_Placeholder
```python
# .name:str
# .tab_index:int
# .appearance:Pages_Appearance
```

#### Pages_SnippetCall
```python
# .parameter_mappings:List
# .snippet:str (Qualified Name)
```

---

### Texts 模块

#### Texts_Text
```python
# .translations:List[Texts_Translation]
```

#### Texts_Translation
```python
# .language_code:str
# .text:str
```

---

### Microflows 模块

#### Microflows_StringTemplate
```python
# .text:str
```

#### Microflows_Annotation
```python
# .description:str
```

---

### Workflows 模块

#### Workflows_Workflow
```python
# .parameter:Workflows_WorkflowParameter
# .flow:Workflows_Flow
# .workflow_name:Microflows_StringTemplate
# .workflow_description:Microflows_StringTemplate
# .name:str
# .excluded:bool
# .export_level:str
# .persistent_id:str
# .title:str
```

#### Workflows_WorkflowParameter
```python
# .name:str
# .entity:str
```

#### Workflows_Flow
```python
# .activities:List[MendixElement]
```

#### Workflows_UserTaskOutcome
```python
# .flow:Workflows_Flow
# .persistent_id:str
# .value:str
```

#### Workflows_SingleUserTaskActivity
```python
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
```

#### Workflows_MultiUserTaskActivity
```python
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
```

#### Workflows_BooleanConditionOutcome
```python
# .flow:Workflows_Flow
# .persistent_id:str
# .value:str
```

#### Workflows_ExclusiveSplitActivity
```python
# .outcomes:List[Workflows_BooleanConditionOutcome]
# .persistent_id:str
# .name:str
# .caption:str
# .expression:str
```

#### Workflows_ParallelSplitOutcome
```python
# .flow:Workflows_Flow
# .persistent_id:str
```

#### Workflows_ParallelSplitActivity
```python
# .outcomes:List[Workflows_ParallelSplitOutcome]
# .persistent_id:str
# .name:str
# .caption:str
```

#### Workflows_WaitForNotificationActivity
```python
# .persistent_id:str
# .name:str
# .caption:str
```

#### Workflows_WaitForTimerActivity
```python
# .annotation:Microflows_Annotation
# .persistent_id:str
# .name:str
# .caption:str
# .delay:str
```

#### Workflows_CallWorkflowActivity
```python
# .persistent_id:str
# .name:str
# .caption:str
# .execute_async:bool
```

#### Workflows_CallMicroflowTask
```python
# .persistent_id:str
# .name:str
# .caption:str
```

---

## 属性交叉引用索引

### 按属性名排序

#### A
- `action` → `Pages_ClientAction`
- `allowed_roles` → `List[str]`
- `annotation` → `Microflows_Annotation`
- `appearance` → `Pages_Appearance`
- `auto_assign_single_target_user` → `bool`

#### B
- `button_style` → `str`

#### C
- `canvas_height` → `int`
- `canvas_width` → `int`
- `caption` → `str`
- `class` → `str`
- `class_` → `str`
- `columns` → `List[Pages_LayoutGridColumn]`
- `completion_criteria` → `Workflows_ConsensusCompletionCriteria`
- `content` → `Pages_ClientTemplate` / `Pages_WebLayoutContent`
- `design_properties` → `List[Pages_DesignPropertyValue]`

#### D
- `default_type` → `str`
- `default_value` → `str`
- `delay` → `str`
- `description` → `str`
- `design_properties` → `List`
- `disabled_during_execution` → `bool`
- `documentation` → `str`
- `dynamic_classes` → `str` (Expression)

#### E
- `editable` → `str`
- `entity` → `str`
- `enumeration_values` → `List[Pages_WidgetEnumerationValue]`
- `excluded` → `bool`
- `execute_async` → `bool`
- `export_level` → `str` (Enum: Hidden/Public...)

#### F
- `flow` → `Workflows_Flow`

#### H
- `help_url` → `str`
- `horizontal_alignment` → `str`

#### I
- `icon` → `Pages_Icon`
- `image` → `str`
- `is_default` → `bool`
- `is_linked` → `bool`
- `is_list` → `bool`
- `is_meta_data` → `bool`
- `is_path` → `str`

#### K
- `key` → `str`

#### L
- `label` → `Texts_Text`
- `label_width` → `int`
- `layout` → `str`
- `layout_call` → `Pages_LayoutCall` / `MendixElement`
- `layout_type` → `str` (Enum: Responsive/Legacy...)

#### M
- `mark_as_used` → `bool`
- `multiline` → `bool`

#### N
- `name` → `str`
- `needs_entity_context` → `bool`
- `native_text_style` → `str`

#### O
- `object` → `Pages_WidgetObject`
- `object_type` → `Pages_WidgetObjectType`
- `offline_capable` → `bool`
- `on_click_action` → `Pages_ClientAction`
- `on_created_event` → `Workflows_NoEvent`
- `option` → `str`
- `outcomes` → `List[Workflows_*Outcome]`

#### P
- `parameter` → `str` / `Workflows_WorkflowParameter`
- `parameter_mappings` → `List`
- `parameter_is_list` → `bool`
- `path_type` → `str`
- `persistent_id` → `str`
- `phone_weight` → `int`
- `placeholder` → `Texts_Text`
- `plugin_widget` → `bool`
- `popup_height` → `int`
- `popup_resizable` → `bool`
- `popup_width` → `int`
- `preview_width` → `int`
- `primitive_value` → `str`
- `progress_bar` → `str`
- `properties` → `List[Pages_*Property]`

#### R
- `render_mode` → `str`
- `render_type` → `str`
- `required` → `bool`
- `return_type` → `Pages_WidgetReturnType`
- `rows` → `List[Pages_LayoutGridRow]`

#### S
- `screen_reader_hidden` → `bool`
- `selection` → `str`
- `set_label` → `bool`
- `snippet` → `str` (Qualified Name)
- `snippet_call` → `Pages_SnippetCall`
- `spacing_between_columns` → `bool`
- `studio_category` → `str`
- `studio_pro_category` → `str`
- `style` → `str`
- `supported_platform` → `str`

#### T
- `tab_index` → `int`
- `target_user_input` → `Workflows_AllUserInput`
- `task_description` → `Microflows_StringTemplate`
- `task_name` → `Microflows_StringTemplate`
- `task_page` → `Pages_PageReference`
- `text` → `str`
- `title` → `str` / `Texts_Text`
- `tooltip` → `Texts_Text`
- `translations` → `List[Texts_Translation]`
- `translatable_value` → `Texts_Text`
- `type` → `str` / `Pages_CustomWidgetType` / `Pages_WidgetValueType`

#### U
- `user_source` → `Workflows_XPathBasedUserSource`

#### V
- `value` → `str` / `Pages_WidgetValue`
- `validation_message_widget` → `str`
- `vertical_alignment` → `str`

#### W
- `weight` → `int`
- `widgets` → `List[Pages_Widget]` / `List[MendixElement]`
- `widget_id` → `str`
- `workflow_description` → `Microflows_StringTemplate`
# .workflow_name → `Microflows_StringTemplate`
- `width` → `str`

---

## 常见类型模式

### 基础类型
- `str` - 字符串
- `int` - 整数
- `bool` - 布尔值

### 对象引用
- `Module_ClassName` - 指向另一个 Mendix 对象
- 示例: `Pages_Widget`, `Texts_Text`, `Workflows_Flow`

### 集合类型
- `List[Module_ClassName]` - 对象列表
- `List[str]` - 字符串列表
- `List` - 未类型化列表

### 枚举值
- `str (Enum: Value1/Value2/...)` - 注释中说明可选值
- 示例: `export_level` (Enum: Hidden/Public...)

### 特殊标记
- `(Expression)` - 包含 MxIX 表达式的字符串
- `(Qualified Name)` - 完全限定名称 (Module$Entity)

---

## 快速查找指南

### 查找属性所属类型

1. **已知类名**: 在上面的"按模块"部分查找
2. **已知属性名**: 在"按属性名排序"部分查找

### 类型关系图

```
Pages_Page
├─→ Pages_LayoutCall
│   ├─→ List[Pages_LayoutCallArgument]
│   │   └─→ List[Pages_Widget]
│   └─→ str (layout name)
├─→ Texts_Text (title)
│   └─→ List[Texts_Translation]
└─→ Pages_Appearance
    └─→ List[Pages_DesignPropertyValue]

Workflows_Workflow
├─→ Workflows_WorkflowParameter
├─→ Workflows_Flow
│   └─→ List[MendixElement] (activities)
└─→ Microflows_StringTemplate
```

---

**使用建议**:
- 在编写分析器时，参考此文档了解属性类型
- 使用类型信息进行智能提示和自动补全
- 在添加新的 `@MendixMap` 类时，按照此格式添加类型注释
