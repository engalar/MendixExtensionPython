from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple

class EntityAttribute(BaseModel):
    """Defines the structure for an entity's attribute."""
    name: str = Field(..., alias="Name",
                      description="The name of the attribute.")
    type: Literal["String", "Integer", "Long", "Decimal", "Boolean", "DateTime", "AutoNumber",
                  "Enumeration", "HashString", "Binary"] = Field(..., alias="Type", description="The data type of the attribute.")
    description: Optional[str] = Field(
        None, alias="Description", description="A description for the attribute.")
    default_value: Optional[str] = Field(
        None, alias="DefaultValue", description="The default value. For Enumerations, this is the enum key/name.")
    enumeration_qualified_name: Optional[str] = Field(
        None, alias="EnumerationQualifiedName", description="The qualified name of the enumeration, required if type is 'Enumeration'.")

    class Config:
        allow_population_by_field_name = True


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
                EntityAttribute(Name="BirthDate", Type="DateTime",
                                DefaultValue="2023-01-01T00:00:00Z"),
                # HashString
                EntityAttribute(Name="Password", Type="HashString")
            ]
        )
    ]
    return CreateEntitiesToolInput(requests=demo_requests)

if __name__ == "__main__":
    demo_input = create_demo_input()
    print(demo_input.model_dump_json(by_alias=True, indent=4))
