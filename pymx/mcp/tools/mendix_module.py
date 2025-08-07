from pymx.model.util import TransactionManager
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib
from pydantic import Field

from pymx.mcp import mendix_context as ctx
# 导入包含核心逻辑和 Pydantic 数据模型的模块
from pymx.model import module as _module
from typing import Annotated
importlib.reload(_module)

# todo: move to module.py
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import AssociationDirection # type: ignore


@mcp.tool(
    name="ensure_modules",
    description="Ensure module exists, if not create it"
)
async def ensure_mendix_modules(names: Annotated[list[str], Field(description="A module name to ensure exist")]) -> str:
    with TransactionManager(ctx.CurrentApp, 'ensure list module exist') as tx:
        for name in names:
            _module.ensure_module(ctx.CurrentApp, name)
    return 'ensure success'


@mcp.resource("model://project:info", description="mendix project info include module name", mime_type="application/json")
def model_project_resource() -> str:
    """mendix project info"""
    reports = []
    modules = ctx.CurrentApp.Root.GetModules()
    for module in modules:
        reports.append(module.Name)
    return reports
    # return "\n".join(reports)

# module domain resource
@mcp.resource("model://project/{module_name}:domain", description="list all entity in specific module domain", mime_type="application/json")
def model_module_resource(module_name: str) -> str:
    """list all entity in specific module"""
    reports = []
    modules = ctx.CurrentApp.Root.GetModules()
    module = next((m for m in modules if m.Name == module_name), None)
    # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.Projects/IModule.md
    if module:
        domain_model = module.DomainModel
        documentation = domain_model.Documentation
        entities = domain_model.GetEntities()
        entity = entities[0] # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.DomainModels/IEntity.md
        entity.Documentation
        entity.Name
        entity.QualifiedName

        location = entity.Location
        location.X # int
        location.Y

        # EntityAssociation
        other_entity = entities[1]
        entityAssociations = entity.GetAssociations(AssociationDirection.Both, other_entity) # AssociationDirection.Both AssociationDirection.Parent AssociationDirection.Child
        entityAssociation = entityAssociations[0]
        association = entityAssociation.Association # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.DomainModels/IAssociation.md
        child = entityAssociation.Child # IEntity
        parent = entityAssociation.Parent

        # IAssociation
        association.ChildDeleteBehavior # enum DeletingBehavior.DeleteMeAndReferences, DeletingBehavior.DeleteMeButKeepReferences, DeletingBehavior.DeleteMeIfNoReferences
        association.ParentDeleteBehavior
        association.Documentation
        association.Name
        association.Owner # enum AssociationOwner.Both, AssociationOwner.Default
        association.Type # enum AssociationType.Reference, AssociationType.ReferenceSet

        # IAttribute 
        attributes = entity.GetAttributes()
        attribute = attributes[0]
        attribute.Documentation
        attribute.Name
        attribute.QualifiedName
        attribute.Type # IStringAttributeType, IIntegerAttributeType, ILongAttributeType, IDecimalAttributeType, IBooleanAttributeType, IAutoNumberAttributeType, IHashStringAttributeType, IBinaryAttributeType, IReferenceAttributeType, IReferenceSetAttributeType

        # if attribute.Type is IStoredValue
        attributeValue = attribute.Value # IStoredValue
        attributeValue.DefaultValue # string

        # IEventHandler
        eventHandlers = entity.GetEventHandlers()
        eventHandler = eventHandlers[0]

        eventHandler.Event # enum EventType.Create, EventType.Delete, EventType.Rollback, EventType.Commit
        eventHandler.Microflow # IQualifiedName<IMicroflow>
        eventHandler.Moment # enum ActivityMoment.Before, ActivityMoment.After
        eventHandler.PassEventObject # bool
        eventHandler.RaiseErrorOnFalse # bool




        generalization = entity.Generalization
        # if generalization is IGeneralization
        generalization.Generalization # IQualifiedName<IEntity>
        # elif generalization is INoGeneralization https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.DomainModels/INoGeneralization.md
        generalization.Persistable
        generalization.HasOwner
        generalization.HasChangedBy
        generalization.HasCreatedDate
        generalization.HasChangedDate

    # https://github.com/mendix/ExtensionAPI-Samples/tree/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Model.DomainModels
    return reports
    # return "\n".join(reports)

@mcp.resource("model://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"
