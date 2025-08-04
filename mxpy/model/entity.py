# https://aistudio.google.com/prompts/1ntnBFfv51uT4HBbYRhVLjDLx7N_oKiUQ

from mxpy.model import module as _module
from mxpy.model.util import TransactionManager
from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule  # type: ignore
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import (  # type: ignore
    IEntity, IAttribute, IAssociation, AssociationType, AssociationOwner,
    IGeneralization, INoGeneralization,
    IStringAttributeType, IIntegerAttributeType, ILongAttributeType, IDecimalAttributeType,
    IBooleanAttributeType, IAutoNumberAttributeType, IDateTimeAttributeType, IEnumerationAttributeType, IBinaryAttributeType, IHashedStringAttributeType,
    IAttributeType, IStoredValue, AssociationDirection
)
from pydantic import BaseModel, Field, model_validator, ValidationError
from datetime import datetime
from typing import List, Literal, Optional, Self, Tuple
from decimal import Decimal, InvalidOperation
import importlib
import clr
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")

# Pydantic is used for data validation and settings management.

# Import specific Mendix API types needed for creating domain models.

# Import custom helper modules for transactions and module creation.
importlib.reload(_module)

# region Pydantic Models for Entity Creation


class EntityAttribute(BaseModel):
    """Defines the structure for an entity's attribute."""
    name: str = Field(..., alias="Name",
                      description="The name of the attribute.")
    type: Literal["String", "Integer", "Long", "Decimal", "Boolean", "DateTime", "AutoNumber",
                  "Enumeration", "HashString", "Binary"] = Field(..., alias="Type", description="The data type of the attribute.")
    description: Optional[str] = Field(
        None, alias="Description", description="A description for the attribute.")
    default_value: Optional[str] = Field(
        None, alias="DefaultValue", description="The default value. For Enumerations, this is the enum key/name. if type is 'DateTime',Value should be empty, '[%CurrentDateTime%]' or a valid date (and time) in the format 'yyyy-mm-dd [hh:mm[:ss]]'.")
    enumeration_qualified_name: Optional[str] = Field(
        None, alias="EnumerationQualifiedName", description="The qualified name of the enumeration, required if type is 'Enumeration'.")

    class Config:
        allow_population_by_field_name = True

    @model_validator(mode='after')
    def check_default_value_and_enumeration(self) -> Self:
        """
        Validates 'default_value' based on 'type' and ensures 'enumeration_qualified_name'
        is handled correctly.
        """
        # --- 1. Validate Enumeration specific fields ---
        if self.type == "Enumeration":
            if not self.enumeration_qualified_name:
                raise ValueError(
                    "'enumeration_qualified_name' is required when type is 'Enumeration'")
        elif self.enumeration_qualified_name is not None:
            raise ValueError(
                "'enumeration_qualified_name' must be null when type is not 'Enumeration'")

        # --- 2. Validate default_value based on type ---
        if self.default_value is None:
            return self  # No validation needed if default_value is not set, must return self

        # --- Type-specific validation logic ---
        if self.type in ("Integer", "Long"):
            try:
                int(self.default_value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Default value '{self.default_value}' is not a valid {self.type}.")

        elif self.type == "Decimal":
            try:
                Decimal(self.default_value)
            except InvalidOperation:
                raise ValueError(
                    f"Default value '{self.default_value}' is not a valid Decimal.")

        elif self.type == "Boolean":
            if self.default_value.lower() not in ['true', 'false']:
                raise ValueError(
                    f"Default value '{self.default_value}' for Boolean must be 'true' or 'false'.")

        elif self.type == "DateTime":
            if self.default_value in ('', '[%CurrentDateTime%]'):
                # Valid special value
                pass
            else:
                formats_to_try = ["%Y-%m-%d %H:%M:%S",
                                  "%Y-%m-%d %H:%M", "%Y-%m-%d"]
                valid_format_found = False
                for fmt in formats_to_try:
                    try:
                        datetime.strptime(self.default_value, fmt)
                        valid_format_found = True
                        break
                    except ValueError:
                        continue

                if not valid_format_found:
                    raise ValueError(
                        f"Default value '{self.default_value}' for DateTime is invalid. "
                        "Use '', '[%CurrentDateTime%]', or 'YYYY-MM-DD [HH:MM[:SS]]' format."
                    )

        # Other types like String, AutoNumber, etc., don't need format validation for default_value.

        # The validator must return the model instance
        return self


class EntityAssociation(BaseModel):
    """Defines the structure for an association between entities."""
    name: str = Field(..., alias="Name",
                      description="The name of the association, e.g., 'Order_Customer'.")
    target_entity_qualified_name: str = Field(..., alias="TargetEntityQualifiedName",
                                              description="The qualified name of the entity this association points to.")
    type: Literal["Reference", "ReferenceSet"] = Field(
        "Reference", alias="Type", description="The type of association (one-to-one/many or one-to-many).")
    owner: Literal["Default", "Both"] = Field(
        "Default", alias="Owner", description="The owner of the association. 'Both' indicates a many-to-many relationship.")

    class Config:
        allow_population_by_field_name = True


class EntityRequest(BaseModel):
    """Defines a complete request to create a single entity."""
    qualified_name: str = Field(..., alias="QualifiedName",
                                description="The qualified name of the entity, e.g., 'MyModule.MyEntity'.")
    is_persistable: bool = Field(
        True, alias="IsPersistable", description="Whether the entity is persistable.")
    generalization_qualified_name: Optional[str] = Field(
        None, alias="GeneralizationQualifiedName", description="The qualified name of the parent entity for generalization (inheritance).")
    attributes: List[EntityAttribute] = Field(
        [], alias="Attributes", description="A list of attributes to create for the entity.")
    associations: List[EntityAssociation] = Field(
        [], alias="Associations", description="A list of associations to create from this entity.")

    class Config:
        allow_population_by_field_name = True


class CreateEntitiesToolInput(BaseModel):
    """The root model for a tool that creates multiple entities."""
    requests: List[EntityRequest] = Field(...,
                                          description="A list of entity creation requests.")

# endregion


def create_demo_input() -> CreateEntitiesToolInput:
    """Creates a sample input object for demonstration purposes."""
    demo_requests = [
        EntityRequest(
            QualifiedName="MyFirstModule.Customer",
            IsPersistable=True,
            Attributes=[
                EntityAttribute(Name="CustomerID", Type="AutoNumber"),
                EntityAttribute(Name="Name", Type="String",
                                Description="Customer's full name."),
                EntityAttribute(Name="IsActive", Type="Boolean",
                                DefaultValue="true"),
                # Duplicate to test skipping
                EntityAttribute(Name="Name", Type="String"),
            ]
        ),
        EntityRequest(
            QualifiedName="MyFirstModule.Order",
            IsPersistable=True,
            Attributes=[
                EntityAttribute(Name="OrderID", Type="AutoNumber"),
                EntityAttribute(Name="OrderDate", Type="DateTime"),
                EntityAttribute(Name="TotalAmount",
                                Type="Decimal", DefaultValue="0.00"),
            ],
            Associations=[
                EntityAssociation(
                    Name="Order_Customer",
                    TargetEntityQualifiedName="MyFirstModule.Customer",
                    Type="Reference",  # An order belongs to one customer
                    Owner="Default"
                )
            ]
        ),
        EntityRequest(  # Example with an error
            QualifiedName="MySecondModule.InternalUser",
            GeneralizationQualifiedName="NonExistentModule.Account",  # This will fail
            Attributes=[EntityAttribute(Name="EmployeeID", Type="String")]
        ),
        EntityRequest(
            QualifiedName="MySecondModule.InternalUser",
            GeneralizationQualifiedName="Administration.Account",
            Attributes=[
                EntityAttribute(Name="EmployeeID", Type="String"),
                EntityAttribute(Name="IsActive", Type="Boolean",
                                DefaultValue="true"),
                # enum
                EntityAttribute(Name="Role", Type="Enumeration",
                                DefaultValue="Phone", EnumerationQualifiedName="System.DeviceType"),
                # autonumber
                EntityAttribute(
                    Name="Phone", Type="AutoNumber"),
                # Binary
                EntityAttribute(Name="Photo", Type="Binary"),
                # DateTime
                EntityAttribute(Name="D1", Type="DateTime",
                                DefaultValue="[%CurrentDateTime%]"),
                EntityAttribute(Name="D2", Type="DateTime",
                                DefaultValue=""),
                EntityAttribute(Name="BirthDate", Type="DateTime",
                                DefaultValue="2023-12-31 21:01:13"),
                # HashString
                EntityAttribute(Name="Password", Type="HashString")
            ]
        )
    ]
    return CreateEntitiesToolInput(requests=demo_requests)


def _create_attribute(current_app, attr_info: EntityAttribute) -> Tuple[Optional[IAttribute], str]:
    """
    Helper function to create an IAttribute. Returns the attribute and a status message.
    """
    new_attribute = current_app.Create[IAttribute]()
    new_attribute.Name = attr_info.name
    if attr_info.description:
        new_attribute.Documentation = attr_info.description

    attribute_type: Optional[IAttributeType] = None
    attribute_value = current_app.Create[IStoredValue]()
    if attr_info.default_value is not None:
        attribute_value.DefaultValue = attr_info.default_value

    attr_type_lower = attr_info.type.lower()

    if attr_type_lower == "string":
        attribute_type = current_app.Create[IStringAttributeType]()
        # binary
    elif attr_type_lower == "binary":
        attribute_type = current_app.Create[IBinaryAttributeType]()
        # hashstring
    elif attr_type_lower == "hashstring":
        attribute_type = current_app.Create[IHashedStringAttributeType]()
    elif attr_type_lower == "integer":
        attribute_type = current_app.Create[IIntegerAttributeType]()
    elif attr_type_lower == "long":
        attribute_type = current_app.Create[ILongAttributeType]()
    elif attr_type_lower == "decimal":
        attribute_type = current_app.Create[IDecimalAttributeType]()
    elif attr_type_lower == "boolean":
        attribute_type = current_app.Create[IBooleanAttributeType]()
    elif attr_type_lower == "autonumber":
        attribute_type = current_app.Create[IAutoNumberAttributeType]()
    elif attr_type_lower == "datetime":
        attribute_type = current_app.Create[IDateTimeAttributeType]()
    elif attr_type_lower == "enumeration":
        if not attr_info.enumeration_qualified_name:
            return None, f"  - [ERROR] Attribute '{attr_info.name}': Type is Enumeration but 'EnumerationQualifiedName' is missing."
        enum = current_app.ToQualifiedName[IEnumeration](
            attr_info.enumeration_qualified_name).Resolve()
        if not enum:
            return None, f"  - [ERROR] Enumeration '{attr_info.enumeration_qualified_name}' not found for attribute '{attr_info.name}'."
        enum_type = current_app.Create[IEnumerationAttributeType]()
        enum_type.Enumeration = enum.QualifiedName
        attribute_type = enum_type
        if attr_info.default_value and not any(v.Name == attr_info.default_value for v in enum.GetValues()):
            msg = f"  - [WARNING] Default value '{attr_info.default_value}' not found in enum '{enum.Name}'. Default will not be set."
            attribute_value.DefaultValue = ""
            # Don't return here, just warn
    else:
        return None, f"  - [ERROR] Unsupported attribute type '{attr_info.type}' for attribute '{attr_info.name}'."

    new_attribute.Type = attribute_type
    if attribute_value.DefaultValue:
        new_attribute.Value = attribute_value

    return new_attribute, f"  - [SUCCESS] Attribute '{new_attribute.Name}' of type '{attr_info.type}' created."


async def create_entities(current_app, tool_input: CreateEntitiesToolInput) -> str:
    """
    Iterates through entity requests, creates/updates them, and returns a plain text report.
    """
    report_lines = ["Starting entity creation process..."]
    success_count = 0
    failure_count = 0

    for i, request in enumerate(tool_input.requests):
        report_lines.append(
            f"\n--- Processing Request {i+1}/{len(tool_input.requests)}: {request.qualified_name} ---")

        try:
            with TransactionManager(current_app, f"Create/Update Entity {request.qualified_name}"):
                # 1. Parse name and ensure module exists
                if '.' not in request.qualified_name:
                    raise ValueError(
                        "Invalid qualified name format. Must be 'ModuleName.EntityName'.")

                module_name, entity_name = request.qualified_name.split('.', 1)
                module = _module.ensure_module(current_app, module_name)
                report_lines.append(f"- Module '{module_name}' ensured.")
                domain_model = module.DomainModel

                # 2. Find or create the entity
                entity = next((e for e in domain_model.GetEntities()
                              if e.Name == entity_name), None)
                if not entity:
                    entity = current_app.Create[IEntity]()
                    entity.Name = entity_name
                    domain_model.AddEntity(entity)
                    report_lines.append(
                        f"- [SUCCESS] Entity '{entity.QualifiedName}' created.")
                else:
                    report_lines.append(
                        f"- [INFO] Entity '{entity.QualifiedName}' already exists. Updating...")

                # 3. Set generalization and persistability
                if request.generalization_qualified_name:
                    parent_entity = current_app.ToQualifiedName[IEntity](
                        request.generalization_qualified_name).Resolve()
                    if not parent_entity:
                        raise ValueError(
                            f"Parent entity '{request.generalization_qualified_name}' not found.")
                    generalization = current_app.Create[IGeneralization]()
                    generalization.Generalization = parent_entity.QualifiedName
                    entity.Generalization = generalization
                    report_lines.append(
                        f"  - [INFO] Set generalization to '{parent_entity.QualifiedName}'.")
                else:
                    no_generalization = current_app.Create[INoGeneralization]()
                    no_generalization.Persistable = request.is_persistable
                    entity.Generalization = no_generalization
                    report_lines.append(
                        f"  - [INFO] Set as non-generalized. Persistable: {request.is_persistable}.")

                # 4. Add attributes
                report_lines.append("- Processing attributes:")
                existing_attr_names = {a.Name.lower()
                                       for a in entity.GetAttributes()}
                for attr_info in request.attributes:
                    if attr_info.name.lower() in existing_attr_names:
                        report_lines.append(
                            f"  - [SKIPPED] Attribute '{attr_info.name}' already exists.")
                        continue
                    new_attribute, message = _create_attribute(
                        current_app, attr_info)
                    report_lines.append(message)
                    if new_attribute:
                        entity.AddAttribute(new_attribute)
                        existing_attr_names.add(new_attribute.Name.lower())

                # 5. Add associations
                report_lines.append("- Processing associations:")
                existing_assoc_names = {a.Association.Name.lower(
                ) for a in entity.GetAssociations(AssociationDirection.Parent)}
                for assoc_info in request.associations:
                    if assoc_info.name.lower() in existing_assoc_names:
                        report_lines.append(
                            f"  - [SKIPPED] Association '{assoc_info.name}' already exists.")
                        continue

                    target_entity = current_app.ToQualifiedName[IEntity](
                        assoc_info.target_entity_qualified_name).Resolve()
                    if not target_entity:
                        raise ValueError(
                            f"Association target entity '{assoc_info.target_entity_qualified_name}' not found.")

                    new_association = entity.AddAssociation(target_entity)
                    new_association.Name = assoc_info.name
                    new_association.Type = AssociationType.ReferenceSet if assoc_info.type == "ReferenceSet" else AssociationType.Reference
                    new_association.Owner = AssociationOwner.Both if assoc_info.owner == "Both" else AssociationOwner.Default
                    report_lines.append(
                        f"  - [SUCCESS] Association '{assoc_info.name}' ({entity.Name} -> {target_entity.Name}) created.")

            # If transaction commits without error
            report_lines.append(
                f"[SUCCESS] Transaction for '{request.qualified_name}' committed.")
            success_count += 1

        except Exception as e:
            # TransactionManager will auto-rollback
            report_lines.append(
                f"[ERROR] Failed to process '{request.qualified_name}': {e}")
            report_lines.append("[INFO] Transaction has been rolled back.")
            failure_count += 1
            continue  # Continue to the next request

    # Final Summary
    report_lines.append("\n\n--- Final Summary ---")
    report_lines.append(
        f"Total requests processed: {len(tool_input.requests)}")
    report_lines.append(f"Successful: {success_count}")
    report_lines.append(f"Failed: {failure_count}")
    report_lines.append("---------------------")

    return "\n".join(report_lines)
