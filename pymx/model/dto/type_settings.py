from typing import List, Optional
from pydantic import BaseModel, Field


class ConstantItem(BaseModel):
    """
    定义一个常量项。
    """
    qualified_name: str = Field(
        ...,
        alias="QualifiedName",
        description="常量的限定名。"
    )
    value: str = Field(
        ...,
        alias="Value",
        description="常量的值。"
    )

    class Config:
        validate_by_name = True


class CustomItem(BaseModel):
    """
    定义一个自定义项。
    """
    name: str = Field(
        ...,
        alias="Name",
        description="自定义项的名称。"
    )
    value: str = Field(
        ...,
        alias="Value",
        description="自定义项的值。"
    )

    class Config:
        validate_by_name = True


class SettingsRequest(BaseModel):
    """
    定义一个设置请求。
    """
    name: str = Field(
        ...,
        alias="Name",
        description="设置的名称。"
    )
    application_root_url: Optional[str] = Field(
        None,
        alias="ApplicationRootUrl",
        description="应用程序根URL。"
    )
    constants: List[ConstantItem] = Field(
        default=[],
        alias="Constants",
        description="常量项列表。"
    )
    customs: List[CustomItem] = Field(
        default=[],
        alias="Customs",
        description="自定义项列表。"
    )

    class Config:
        validate_by_name = True

def create_demo_input() -> SettingsRequest:
    """
    创建一个示例设置请求。
    """
    return SettingsRequest(
        name="DemoSettings",
        application_root_url="https://example.com",
        constants=[
            ConstantItem(QualifiedName="MyModule.MyConstant", Value="42"),
            ConstantItem(QualifiedName="MyModule.AnotherConstant", Value="'Hello, World!'")
        ],
        Customs=[
            CustomItem(Name="Name1", Value="true"),
            CustomItem(Name="Name2", Value="'Some Value'")
        ]
    )

if __name__ == "__main__":
    print(create_demo_input().model_dump_json(by_alias=True, indent=4))