import re
from typing import List, Literal, Optional, Set, Union, Any, Annotated
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing_extensions import Self


# ==========================================
# 1. 基础配置与通用类型
# ==========================================

class DataTypeDefinition(BaseModel):
    """
    定义一个 Mendix 数据类型。
    """
    model_config = ConfigDict(populate_by_name=True)

    type_name: Literal[
        "Enumeration", "Decimal", "Binary", "Boolean", "DateTime",
        "Integer", "Long", "String", "Void", "Object", "List",
    ] = Field(..., alias="TypeName", description="Mendix 数据类型的名称 (例如 'String', 'Object', 'List')。")
    
    qualified_name: Optional[str] = Field(
        None,
        alias="QualifiedName",
        description="模块限定名 (例如 'MyModule.MyEntity')。当类型为 Object, List 或 Enumeration 时必填。",
    )

    @model_validator(mode="after")
    def check_qualified_name_is_present(self) -> Self:
        if self.type_name in ("Object", "List", "Enumeration") and not self.qualified_name:
            raise ValueError(f"'{self.type_name}' 类型需要一个 'QualifiedName'。")
        return self


class MicroflowParameter(BaseModel):
    """
    定义微流的输入参数。
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="Name", description="参数变量名称。")
    type: DataTypeDefinition = Field(..., alias="Type", description="参数的数据类型。")


# ==========================================
# 2. Activity DTOs (活动定义)
# ==========================================

class BaseActivity(BaseModel):
    model_config = ConfigDict(populate_by_name=True) 
    activity_type: str = Field(..., alias="ActivityType", description="活动的类型标识符。")


class SortItem(BaseModel):
    """数据库检索时的排序规则"""
    model_config = ConfigDict(populate_by_name=True)
    attribute_name: str = Field(..., alias="AttributeName", description="用于排序的属性名称。")
    ascending: bool = Field(True, alias="Ascending", description="是否升序排列。默认为 True。")


class RetrieveActivity(BaseActivity):
    """
    获取数据活动 (Retrieve)。
    支持两种模式：
    1. ByAssociation: 从关联获取 (需要 SourceVariable 和 AssociationName)。
    2. Database: 从数据库获取 (需要 EntityName，可选 XPath, Range, Sorting)。
    """
    activity_type: Literal["Retrieve"] = Field("Retrieve", alias="ActivityType")
    
    source_type: Literal["Association", "Database"] = Field(
        "Association", 
        alias="SourceType", 
        description="获取源类型：'Association' (通过关联) 或 'Database' (直接查询数据库)。"
    )

    # Output
    output_variable: str = Field(..., alias="OutputVariable", description="存储结果的变量名。")

    # Mode: Association
    source_variable: Optional[str] = Field(
        None, 
        alias="SourceVariable", 
        description="[Association模式必填] 持有关联对象的变量名。"
    )
    association_name: Optional[str] = Field(
        None, 
        alias="AssociationName", 
        description="[Association模式必填] 关联名称 (例如 'Module.Entity_Association')。"
    )

    # Mode: Database
    entity_name: Optional[str] = Field(
        None, 
        alias="EntityName", 
        description="[Database模式必填] 要检索的实体名称 (例如 'Module.Entity')。"
    )
    xpath_constraint: Optional[str] = Field(
        None, 
        alias="XPathConstraint", 
        description="[Database模式可选] XPath 过滤条件 (例如 '[Name = $Variable]')。"
    )
    # Range
    range_index: Optional[str] = Field(
        None, 
        alias="RangeIndex", 
        description="[Database模式可选] 分页起始索引的表达式 (默认 '0')。"
    )
    range_amount: Optional[str] = Field(
        None, 
        alias="RangeAmount", 
        description="[Database模式可选] 检索数量的表达式 (如果不填则检索全部/默认行为)。"
    )
    retrieve_just_first_item: Optional[bool] = Field(
        None,
        alias="RetrieveJustFirstItem",
        description="If true, only the first item matching is returned. If false, all items are returned."
    )
    sorting: List[SortItem] = Field(
        default=[], 
        alias="RetrieveJustFirstItem", 
        description="[Database模式可选] 排序规则列表。"
    )


class AggregateListActivity(BaseActivity):
    """聚合列表活动 (Aggregate List)，用于计算 Count, Sum, Average 等。"""
    activity_type: Literal["AggregateList"] = Field("AggregateList", alias="ActivityType")
    
    input_list_variable: str = Field(..., alias="InputListVariable", description="要聚合的列表变量名。")
    output_variable: str = Field(..., alias="OutputVariable", description="存储结果的变量名。")
    function: Literal["Count", "Sum", "Average", "Minimum", "Maximum"] = Field(
        ..., 
        alias="Function", 
        description="聚合函数类型。"
    )
    attribute_name: Optional[str] = Field(
        None, 
        alias="AttributeName", 
        description="[Sum/Avg/Min/Max 必填] 要进行计算的属性名。"
    )


class ListOperationActivity(BaseActivity):
    """列表操作活动 (List Operation)，如 Head, Tail, Union, Sort 等。"""
    activity_type: Literal["ListOperation"] = Field("ListOperation", alias="ActivityType")
    # 目前不支持binary operation e.g. "Union",  "Intersect", "Contains",
    # 也不支持需要排序属性的操作 e.g. "Sort"
    operation_type: Literal["Head", "Tail"] = Field(
        "Head", 
        alias="OperationType", 
        description="操作类型。"
    )
    input_list_variable: str = Field(..., alias="InputListVariable", description="主要输入列表变量。")
    output_variable: str = Field(..., alias="OutputVariable", description="存储结果的变量名。")
    
    binary_operation_list_variable: Optional[str] = Field(
        None, 
        alias="BinaryOperationListVariable", 
        description="[Union/Intersect/Contains 必填] 第二个列表变量名。"
    )


class ChangeItem(BaseModel):
    """定义单个属性的修改操作。"""
    model_config = ConfigDict(populate_by_name=True)
    
    attribute_name: str = Field(..., alias="AttributeName", description="要修改的属性名。")
    action: Literal["Set", "Add", "Remove"] = Field(
        "Set", 
        alias="Action", 
        description="操作类型：'Set' (赋值), 'Add' (添加到引用集), 'Remove' (从引用集移除)。默认为 'Set'。"
    )
    value_expression: str = Field(..., alias="ValueExpression", description="值的微流表达式 (例如 string 需加引号)。")


class ChangeActivity(BaseActivity):
    """
    修改对象活动 (Change Object)。
    可以修改属性或关联，并选择是否提交。
    """
    activity_type: Literal["Change"] = Field("Change", alias="ActivityType")
    
    variable_name: str = Field(..., alias="VariableName", description="要修改的对象变量名。")
    entity_name: str = Field(..., alias="EntityName", description="对象的实体类型 (用于解析属性)。")
    changes: List[ChangeItem] = Field(default=[], alias="Changes", description="属性变更列表。")
    commit: Literal["No", "Yes", "YesWithoutEvents"] = Field(
        "No", 
        alias="Commit", 
        description="是否提交对象到数据库。"
    )


class CommitActivity(BaseActivity):
    """提交对象活动 (Commit Object)。"""
    activity_type: Literal["Commit"] = Field("Commit", alias="ActivityType")
    
    variable_name: str = Field(..., alias="VariableName", description="要提交的对象变量名。")
    refresh_client: bool = Field(
        False, 
        alias="RefreshClient", 
        description="是否刷新客户端显示 (默认为 False)。"
    )


# Discriminated Union
ActivityUnion = Annotated[
    Union[
        RetrieveActivity,
        AggregateListActivity,
        ListOperationActivity,
        ChangeActivity,
        CommitActivity,
    ],
    Field(discriminator="activity_type")
]


# ==========================================
# 3. Request DTO
# ==========================================

class MicroflowRequest(BaseModel):
    """创建微流的请求体。"""
    model_config = ConfigDict(populate_by_name=True)

    full_path: str = Field(..., alias="FullPath", description="微流的完整路径 (ModuleName/Folder/Name)。")
    return_type: DataTypeDefinition = Field(..., alias="ReturnType", description="微流返回值类型。")
    return_exp: Optional[str] = Field(None, alias="ReturnExp", description="返回值表达式 (如果是 Void 则不填)。")
    parameters: List[MicroflowParameter] = Field(default=[], alias="Parameters", description="微流输入参数列表。")
    activities: List[ActivityUnion] = Field(default=[], alias="Activities", description="微流活动列表，按顺序执行。")

    @field_validator("full_path")
    def validate_full_path(cls, v: str):
        if not v or len(v.split("/")) < 2:
            raise ValueError("FullPath 必须至少包含 'ModuleName/MicroflowName'。")
        return v


class CreateMicroflowsToolInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    requests: List[MicroflowRequest] = Field(..., description="要创建的微流请求列表。")