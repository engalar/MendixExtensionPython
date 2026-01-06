import re
from typing import List, Literal, Optional, Set, Union, Any
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing_extensions import Self


# ==========================================
# 1. 基础配置与通用类型
# ==========================================

class DataTypeDefinition(BaseModel):
    """
    定义一个 Mendix 数据类型。
    """
    model_config = ConfigDict(populate_by_name=True)  # V2 兼容配置：允许通过别名(PascalCase)初始化

    type_name: Literal[
        "Enumeration", "Decimal", "Binary", "Boolean", "DateTime",
        "Integer", "Long", "String", "Void", "Object", "List",
    ] = Field(..., alias="TypeName", description="Mendix 数据类型的名称。")
    
    qualified_name: Optional[str] = Field(
        None,
        alias="QualifiedName",
        description="模块限定名 (例如 'MyModule.MyEntity')。",
    )

    @model_validator(mode="after")
    def check_qualified_name_is_present(self) -> Self:
        if self.type_name in ("Object", "List", "Enumeration") and not self.qualified_name:
            raise ValueError(f"'{self.type_name}' 类型需要一个 'QualifiedName'。")
        if self.type_name not in ("Object", "List", "Enumeration") and self.qualified_name:
            raise ValueError(f"'{self.type_name}' 类型不应提供 'QualifiedName'。")
        return self


class MicroflowParameter(BaseModel):
    """
    定义一个微流的输入参数。
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="Name")
    type: DataTypeDefinition = Field(..., alias="Type")


# ==========================================
# 2. Activity DTOs (活动定义)
# ==========================================

class BaseActivity(BaseModel):
    model_config = ConfigDict(populate_by_name=True) # 关键：让所有子类支持 Alias 初始化
    activity_type: str = Field(..., alias="ActivityType")


class RetrieveActivity(BaseActivity):
    """通过关联获取"""
    activity_type: Literal["Retrieve"] = Field("Retrieve", alias="ActivityType")
    source_variable: str = Field(..., alias="SourceVariable")
    association_name: str = Field(..., alias="AssociationName")
    output_variable: str = Field(..., alias="OutputVariable")


class AggregateListActivity(BaseActivity):
    """聚合列表"""
    activity_type: Literal["AggregateList"] = Field("AggregateList", alias="ActivityType")
    input_variable: str = Field(..., alias="InputVariable")
    output_variable: str = Field(..., alias="OutputVariable")
    function: Literal["Count", "Sum", "Average", "Minimum", "Maximum"] = Field(..., alias="Function")
    attribute_name: Optional[str] = Field(None, alias="AttributeName")
    entity_name: Optional[str] = Field(None, alias="EntityName")


class ListOperationActivity(BaseActivity):
    """列表操作"""
    activity_type: Literal["ListOperation"] = Field("ListOperation", alias="ActivityType")
    operation: Literal["Head"] = Field("Head", alias="Operation")
    input_variable: str = Field(..., alias="InputVariable")
    output_variable: str = Field(..., alias="OutputVariable")


class ChangeItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True) # ChangeItem 也需要支持 Alias
    attribute_name: str = Field(..., alias="AttributeName")
    value_expression: str = Field(..., alias="ValueExpression")


class ChangeActivity(BaseActivity):
    """修改属性"""
    activity_type: Literal["Change"] = Field("Change", alias="ActivityType")
    variable_name: str = Field(..., alias="VariableName")
    entity_name: str = Field(..., alias="EntityName")
    changes: List[ChangeItem] = Field(default=[], alias="Changes")
    commit: Literal["No", "Yes", "YesWithoutEvents"] = Field("No", alias="Commit")


class CommitActivity(BaseActivity):
    """提交对象"""
    activity_type: Literal["Commit"] = Field("Commit", alias="ActivityType")
    variable_name: str = Field(..., alias="VariableName")
    refresh_client: bool = Field(False, alias="RefreshClient")


# 注册所有活动类型 Union
ActivityUnion = Union[
    RetrieveActivity,
    AggregateListActivity,
    ListOperationActivity,
    ChangeActivity,
    CommitActivity,
]


# ==========================================
# 3. Request DTO (请求定义)
# ==========================================

class MicroflowRequest(BaseModel):
    """
    定义一个创建微流的完整请求。
    """
    model_config = ConfigDict(populate_by_name=True)

    full_path: str = Field(..., alias="FullPath")
    return_type: DataTypeDefinition = Field(..., alias="ReturnType")
    return_exp: Optional[str] = Field(None, alias="ReturnExp")
    parameters: List[MicroflowParameter] = Field(default=[], alias="Parameters")
    activities: List[ActivityUnion] = Field(default=[], alias="Activities")

    @field_validator("full_path")
    def validate_full_path(cls, v: str):
        if not v or len(v.split("/")) < 2:
            raise ValueError("FullPath 必须至少包含 'ModuleName/MicroflowName'。")
        return v

    @model_validator(mode="after")
    def validate_return_logic(self) -> Self:
        return_type_name = self.return_type.type_name
        exp = self.return_exp

        if exp is not None:
            if return_type_name == "Void":
                raise ValueError("当 ReturnType 为 'Void' 时，'ReturnExp' 必须为空。")

            if exp.startswith("$"):
                if len(exp) < 2 or not re.match(r"^\$[a-zA-Z_][a-zA-Z0-9_]*$", exp):
                    raise ValueError(f"无效的变量名格式: '{exp}'。")
                return self

            if exp == "empty":
                if return_type_name in ("Object", "List"):
                    return self
                else:
                    raise ValueError(f"'empty' 对 '{return_type_name}' 无效。")

            LITERAL_SUPPORTING_PRIMITIVES: Set[str] = {
                "String", "Integer", "Long", "Decimal", "Boolean",
            }

            if return_type_name not in LITERAL_SUPPORTING_PRIMITIVES:
                raise ValueError(f"类型 '{return_type_name}' 不支持字面量返回值。")

            if return_type_name == "Boolean":
                if exp not in ("true", "false"):
                    raise ValueError(f"Boolean 字面量必须是 'true' 或 'false'。")

            elif return_type_name in ("Integer", "Long"):
                try:
                    int(exp)
                except (ValueError, TypeError):
                    raise ValueError(f"无法将 '{exp}' 解析为 Integer/Long。")

            elif return_type_name == "Decimal":
                try:
                    float(exp)
                except (ValueError, TypeError):
                    raise ValueError(f"无法将 '{exp}' 解析为 Decimal。")

            elif return_type_name == "String":
                if not ((exp.startswith("'") and exp.endswith("'")) or 
                        (exp.startswith('"') and exp.endswith('"'))):
                    raise ValueError(f"String 字面量必须被引号包围: {exp}")

        return self


class CreateMicroflowsToolInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    requests: List[MicroflowRequest]


# ==========================================
# 4. Demo Data Generator
# ==========================================

def create_demo_input() -> CreateMicroflowsToolInput:
    """创建一个包含实际 Retrieve 和 Change 活动的示例输入。"""
    
    # 构造 Retrieve 活动 (现在可以通过 Alias 初始化了)
    act_retrieve = RetrieveActivity(
        ActivityType="Retrieve",
        SourceVariable="CurrentUser",
        AssociationName="System.UserRoles",
        OutputVariable="RetrievedRoleList"
    )

    # 构造 Change 活动
    act_change = ChangeActivity(
        ActivityType="Change",
        EntityName="System.User",
        VariableName="CurrentUser",
        Commit="Yes",
        Changes=[
            ChangeItem(
                AttributeName="Name",
                ValueExpression="'New_Admin_Name'"
            )
        ]
    )

    # 构造请求
    demo_request = MicroflowRequest(
        FullPath="MyFirstModule/Folder1/Folder2/MyMicroflow",
        ReturnType=DataTypeDefinition(TypeName="String"),
        ReturnExp="'Success'",
        Parameters=[
            MicroflowParameter(
                Name="CurrentUser", 
                Type=DataTypeDefinition(TypeName="Object", QualifiedName="System.User")
            )
        ],
        Activities=[act_retrieve, act_change]
    )

    return CreateMicroflowsToolInput(requests=[demo_request])


if __name__ == "__main__":
    print(create_demo_input().model_dump_json(by_alias=True, indent=4))
    # 合法：返回 String 类型，但不指定返回表达式。
    # 这意味着生成微流的逻辑需要自己处理默认返回值。
    valid_optional_exp = {
        "FullPath": "MyModule/GetStatusMessage",
        "ReturnType": {"TypeName": "String"},
        "ReturnExp": None,  # 明确为 None 或直接不提供此字段
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
        "ReturnExp": "100",
    }

    request = MicroflowRequest.model_validate(valid_provided_exp)
    print("✅ 合法请求 (提供了正确的ReturnExp) - 验证通过!")

    # 非法：返回 Integer，但提供了格式错误的字面量
    invalid_provided_exp = {
        "FullPath": "MyModule/CountItems",
        "ReturnType": {"TypeName": "Integer"},
        "ReturnExp": "one hundred",  # 错误：无法解析为整数
    }

    try:
        MicroflowRequest.model_validate(invalid_provided_exp)
    except ValueError as e:
        print(f"❌ 非法请求 (提供了错误的ReturnExp) - 验证按预期失败: {e}")
