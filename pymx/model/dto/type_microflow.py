import re
from typing import List, Literal, Optional, Set
from pydantic import BaseModel, Field, model_validator, field_validator
from typing_extensions import Self


class DataTypeDefinition(BaseModel):
    """
    定义一个 Mendix 数据类型。
    它封装了 Mendix 中所有可能的数据类型，包括基础类型、对象、列表和枚举。
    """
    type_name: Literal[
        "Enumeration", "Decimal", "Binary", "Boolean", "DateTime",
        "Integer", "Long", "String", "Void", "Object", "List"
    ] = Field(
        ...,
        alias="TypeName",
        description="Mendix 数据类型的名称。"
    )
    qualified_name: Optional[str] = Field(
        None,
        alias="QualifiedName",
        description="当类型为 Object, List 或 Enumeration 时，必须提供其模块限定名 (例如 'MyModule.MyEntity' 或 'MyModule.MyEnumeration')。"
    )

    class Config:
        validate_by_name = True

    @model_validator(mode='after')
    def check_qualified_name_is_present(self) -> Self:
        """验证需要限定名的类型是否已提供。"""
        if self.type_name in ("Object", "List", "Enumeration") and not self.qualified_name:
            raise ValueError(
                f"'{self.type_name}' 类型需要一个 'QualifiedName'。")
        if self.type_name not in ("Object", "List", "Enumeration") and self.qualified_name:
            raise ValueError(
                f"'{self.type_name}' 类型不应提供 'QualifiedName'。")
        return self


class MicroflowParameter(BaseModel):
    """
    定义一个微流的输入参数。
    每个参数都有一个在微流中唯一的名称和明确的数据类型。
    """
    name: str = Field(
        ...,
        alias="Name",
        description="参数的名称，在微流中必须是唯一的有效标识符。"
    )
    type: DataTypeDefinition = Field(
        ...,
        alias="Type",
        description="参数的数据类型定义。"
    )

    class Config:
        allow_population_by_field_name = True


class MicroflowRequest(BaseModel):
    """
    定义一个创建微流的完整请求。
    它包含了创建微流所需的所有关键元数据，如路径、参数、返回类型和可选的返回表达式。
    """
    full_path: str = Field(
        ...,
        alias="FullPath",
        description="微流的完整路径，格式为 'ModuleName/SubFolderName/MicroflowName'。"
    )
    return_type: DataTypeDefinition = Field(
        ...,
        alias="ReturnType",
        description="微流执行完毕后返回的数据类型。"
    )
    return_exp: Optional[str] = Field(
        None,
        alias="ReturnExp",
        description="可选的返回表达式。如果省略，表示微流可能返回该类型的默认值。如果提供，其格式必须正确：可以是以'$'开头的变量名，或与返回类型匹配的字面量（如 'true', 123, 'some text')。"
    )
    parameters: List[MicroflowParameter] = Field(
        default=[],
        alias="Parameters",
        description="微流的输入参数列表。"
    )

    class Config:
        allow_population_by_field_name = True

    @field_validator('full_path')
    def validate_full_path(cls, v: str):
        if not v or len(v.split('/')) < 2:
            raise ValueError("FullPath 必须至少包含 'ModuleName/MicroflowName'。")
        return v

    @model_validator(mode='after')
    def validate_return_logic(self) -> Self:
        """
        验证 ReturnType 和 ReturnExp 之间的一致性。
        该验证仅在 ReturnExp 被提供时触发。
        """
        return_type_name = self.return_type.type_name
        exp = self.return_exp

        if exp is not None:
            if return_type_name == "Void":
                raise ValueError(
                    "当 ReturnType 为 'Void' 时，'ReturnExp' 必须为空 (None)。")

            if exp.startswith('$'):
                if len(exp) < 2 or not re.match(r'^\$[a-zA-Z_][a-zA-Z0-9_]*$', exp):
                    raise ValueError(f"无效的变量名格式: '{exp}'。必须以$开头，后跟有效的标识符。")
                return self

            if exp == 'empty':
                if return_type_name in ('Object', 'List'):
                    return self
                else:
                    raise ValueError(
                        f"'empty' 字面量只对 'Object' 或 'List' 类型的返回值有效，而不是 '{return_type_name}'。")

            LITERAL_SUPPORTING_PRIMITIVES: Set[str] = {
                "String", "Integer", "Long", "Decimal", "Boolean"
            }

            if return_type_name not in LITERAL_SUPPORTING_PRIMITIVES:
                raise ValueError(
                    f"类型 '{return_type_name}' 不支持除 'empty' 之外的字面量返回值。请使用一个以'$'开头的变量名。"
                )

            if return_type_name == "Boolean":
                if exp not in ('true', 'false'):
                    raise ValueError(
                        f"Boolean 字面量必须是 'true' 或 'false'，而不是 '{exp}'。")

            elif return_type_name in ("Integer", "Long"):
                try:
                    int(exp)
                except (ValueError, TypeError):
                    raise ValueError(f"无法将字面量 '{exp}' 解析为 Integer/Long。")

            elif return_type_name == "Decimal":
                try:
                    float(exp)
                except (ValueError, TypeError):
                    raise ValueError(f"无法将字面量 '{exp}' 解析为 Decimal。")

            elif return_type_name == "String":
                if not ((exp.startswith("'") and exp.endswith("'")) or (exp.startswith('"') and exp.endswith('"'))):
                    raise ValueError(f"String 字面量必须被单引号或双引号包围。收到的值是: {exp}")
                if len(exp) < 2:
                    raise ValueError("空的 String 字面量应表示为 '' 或 \"\"。")

        return self


class CreateMicroflowsToolInput(BaseModel):
    """该工具的根输入模型，包含一个请求列表。"""
    requests: List[MicroflowRequest]


def create_demo_input() -> CreateMicroflowsToolInput:
    """创建一个示例输入对象，用于演示。"""
    demo_requests = [
        MicroflowRequest(
            FullPath="MyFirstModule/Folder1/Folder2/MyMicroflow",
            ReturnType=DataTypeDefinition(TypeName="String"),
            ReturnExp="'Hello, World!'",
            Parameters=[
                MicroflowParameter(
                    Name="param1", Type=DataTypeDefinition(TypeName="String")),
                MicroflowParameter(Name="param2", Type=DataTypeDefinition(
                    TypeName="Enumeration", QualifiedName="System.DeviceType")),
                MicroflowParameter(
                    Name="param3", Type=DataTypeDefinition(TypeName="DateTime")),
                MicroflowParameter(Name="param4", Type=DataTypeDefinition(
                    TypeName="List", QualifiedName="System.User"))
            ]
        ),
        MicroflowRequest(
            FullPath="MySecondModule/MyMicroflow",
            ReturnType=DataTypeDefinition(TypeName="Void"),
            Parameters=[
                MicroflowParameter(
                    Name="param1", Type=DataTypeDefinition(TypeName="Integer"))
            ]
        ),
    ]
    return CreateMicroflowsToolInput(requests=demo_requests)


if __name__ == "__main__":
    print(create_demo_input().model_dump_json(by_alias=True, indent=4))
    # 合法：返回 String 类型，但不指定返回表达式。
    # 这意味着生成微流的逻辑需要自己处理默认返回值。
    valid_optional_exp = {
        "FullPath": "MyModule/GetStatusMessage",
        "ReturnType": {"TypeName": "String"},
        "ReturnExp": None  # 明确为 None 或直接不提供此字段
    }

    try:
        request = MicroflowRequest.model_validate(valid_optional_exp)
        print("✅ 合法请求 (非Void类型，无ReturnExp) - 验证通过!")
    except ValueError as e:
        print(f"❌ 验证失败: {e}")

    # 合法：返回 Integer，并提供了正确的字面量表达式
    valid_provided_exp = {
        "FullPath": "MyModule/CountItems",
        "ReturnType": {"TypeName": "Integer"},
        "ReturnExp": "100"
    }

    request = MicroflowRequest.model_validate(valid_provided_exp)
    print("✅ 合法请求 (提供了正确的ReturnExp) - 验证通过!")

    # 非法：返回 Integer，但提供了格式错误的字面量
    invalid_provided_exp = {
        "FullPath": "MyModule/CountItems",
        "ReturnType": {"TypeName": "Integer"},
        "ReturnExp": "one hundred"  # 错误：无法解析为整数
    }

    try:
        MicroflowRequest.model_validate(invalid_provided_exp)
    except ValueError as e:
        print(f"❌ 非法请求 (提供了错误的ReturnExp) - 验证按预期失败: {e}")
