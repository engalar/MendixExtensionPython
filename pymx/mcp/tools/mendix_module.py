import json
import clr
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import AssociationDirection, IGeneralization, INoGeneralization  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule
from pymx.model import util
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
import traceback
from pydantic import Field

from pymx.mcp import mendix_context as ctx
# 导入包含核心逻辑和 Pydantic 数据模型的模块
from pymx.model import module as _module
from typing import Annotated
importlib.reload(_module)

# todo: move to module.py


@mcp.tool(
    name="ensure_modules",
    description="Ensure module exists, if not create it"
)
async def ensure_mendix_modules(names: Annotated[list[str], Field(description="A module name to ensure exist")]) -> str:
    with util.TransactionManager(ctx.CurrentApp, 'ensure list module exist') as tx:
        for name in names:
            _module.ensure_module(ctx.CurrentApp, name)
    return 'ensure success'


@mcp.resource("model://project/info", description="mendix project info include module name", mime_type="application/json")
def model_project_resource() -> str:
    """mendix project info"""
    reports = []
    modules = ctx.CurrentApp.Root.GetModules()
    for module in modules:
        reports.append(module.Name)
    return json.dumps(reports)

# module domain resource


@mcp.resource("model://module/{module_name}/domain", description="list all entity in specific module domain", mime_type="application/json")
def model_module_resource(module_name: str) -> str:
    """list all entity in specific module"""
    importlib.reload(util)
    entity_reports = []
    modules = ctx.CurrentApp.Root.GetModules()
    module = next((m for m in modules if m.Name == module_name), None)

    try:
        # 使用事务可以确保类型转换等操作的原子性
        with util.TransactionManager(ctx.CurrentApp, f"list_entity_in_{module_name}") as tx:
            if not module:
                return json.dumps({"error": f"Module '{module_name}' not found."})

            domain_model = module.DomainModel
            entities = domain_model.GetEntities()

            for entity in entities:
                entity_info = {
                    "name": entity.Name,
                    "qualified_name": entity.QualifiedName.FullName,
                    "documentation": entity.Documentation
                }

                # 添加位置信息
                location = entity.Location
                entity_info["location"] = {
                    "x": location.X,
                    "y": location.Y
                }

                # 添加属性信息
                attributes_info = []
                for attribute in entity.GetAttributes():
                    attributes_info.append({
                        "name": attribute.Name,
                        "qualified_name": attribute.QualifiedName.FullName,
                        "documentation": attribute.Documentation
                    })
                entity_info["attributes"] = attributes_info

                # 添加关联信息
                associations_info = []
                for entity_association in entity.GetAssociations(AssociationDirection.Parent, None):
                    association = entity_association.Association
                    associations_info.append({
                        "name": association.Name,
                        "documentation": association.Documentation,
                        "child_delete_behavior": str(association.ChildDeleteBehavior),
                        "parent_delete_behavior": str(association.ParentDeleteBehavior),
                        "owner": str(association.Owner),
                        "type": str(association.Type),
                        "child_entity": entity_association.Child.QualifiedName.FullName,
                        "parent_entity": entity_association.Parent.QualifiedName.FullName,
                    })
                entity_info["associations"] = associations_info

                # 添加事件处理器信息
                event_handlers_info = []
                for event_handler in entity.GetEventHandlers():
                    handler_info = {
                        "event": str(event_handler.Event),
                        "moment": str(event_handler.Moment),
                        "pass_event_object": event_handler.PassEventObject,
                        "raise_error_on_false": event_handler.RaiseErrorOnFalse,
                        "microflow": event_handler.Microflow.FullName if event_handler.Microflow else None
                    }
                    event_handlers_info.append(handler_info)
                entity_info["event_handlers"] = event_handlers_info

                # --- 继承信息处理 (修改部分) ---
                def append_generalization(current_entity, gen_info_dict):
                    """
                    递归地查找并记录实体的所有父类。
                    使用 try-except 来正确处理 IGeneralization 和 INoGeneralization 代理。
                    """
                    g_proxy = current_entity.Generalization

                    has_parent = False
                    parent_entity_qualified_name = None

                    try:
                        # 尝试像访问 IGeneralization 一样访问 'Generalization' 属性
                        # 1. 创建一个 IGeneralization 类型的辅助对象以获取属性信息
                        helper_obj = ctx.CurrentApp.Create[IGeneralization]()
                        prop_info = helper_obj.GetType().GetProperty('Generalization')
                        # 2. 尝试从代理对象 g_proxy 获取该属性的值
                        parent_entity_qualified_name = prop_info.GetValue(
                            g_proxy, None)
                        has_parent = True
                    except Exception:
                        # 3. 如果失败，说明 g_proxy 是 INoGeneralization 类型，没有父类
                        has_parent = False

                    if has_parent and parent_entity_qualified_name:
                        # 如果有父类，记录其名称并递归查找
                        gen_info_dict["parents"].append(
                            parent_entity_qualified_name.FullName)
                        parent_entity = parent_entity_qualified_name.Resolve()
                        append_generalization(parent_entity, gen_info_dict)
                    else:
                        # 到达继承链的顶端，此时可以安全地访问 INoGeneralization 的属性
                        def get_no_gen_property(prop_name):
                            try:
                                helper_obj = ctx.CurrentApp.Create[INoGeneralization](
                                )
                                prop_info = helper_obj.GetType().GetProperty(prop_name)
                                return prop_info.GetValue(g_proxy, None)
                            except:
                                return None  # 出错时返回 None

                        gen_info_dict["persistable"] = get_no_gen_property(
                            "Persistable")
                        gen_info_dict["has_owner"] = get_no_gen_property(
                            "HasOwner")
                        gen_info_dict["has_changed_by"] = get_no_gen_property(
                            "HasChangedBy")
                        gen_info_dict["has_created_date"] = get_no_gen_property(
                            "HasCreatedDate")
                        gen_info_dict["has_changed_date"] = get_no_gen_property(
                            "HasChangedDate")

                gen_info = {"parents": []}
                append_generalization(entity, gen_info)
                entity_info["generalization"] = gen_info

                entity_reports.append(entity_info)

    except Exception as e:
        # 返回结构化的错误信息
        error_info = {
            "error": "An unexpected error occurred",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        return json.dumps(error_info, indent=2)

    # 确保返回格式正确的 JSON 字符串
    return json.dumps(entity_reports, indent=2)


@mcp.resource("model://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"
