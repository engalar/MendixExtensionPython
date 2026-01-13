# 对于 LLM（特别是能力稍弱的模型），Schema 中的 description 字段就是它的“操作手册”。如果不写清楚字段在什么情况下必填、格式是什么，模型很容易瞎填。

from typing import List, Literal, Optional, Any, Union
from pydantic import BaseModel, Field
from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

# 导入后端逻辑和复杂 DTO
from pymx.model import microflow
from pymx.model.dto import type_microflow as complex_dto

# 重新加载以确保开发时的更新生效
importlib.reload(microflow)
importlib.reload(complex_dto)


# ==========================================
# 1. 极简前端模型 (Super Simple DTOs for LLM)
# ==========================================

class SimpleParameter(BaseModel):
    Name: str = Field(description="参数变量名")
    Type: str = Field(description="参数数据类型。支持基本类型 (例如 'String', 'Integer', 'Boolean')，以及引用类型。引用类型可以是单一实体 (例如 'MyModule.Customer') 或实体列表 (例如 'List(MyModule.Order)')。")

class SimpleChangeItem(BaseModel):
    """用于 Change 和 CreateObject 的赋值项"""
    AttributeName: Optional[str] = Field(None, description="要赋值的属性名 (格式: 'AttributeName')。与 AssociationName 互斥，只能提供其中之一。")
    AssociationName: Optional[str] = Field(None, description="要设置的关联名 (格式: 'MyModule.AssociationName')。与 AttributeName 互斥，只能提供其中之一。")
    Action: Literal["Set", "Add", "Remove"] = Field("Set", description="操作类型，默认为 Set。Set 用于一对一或多对一，Add/Remove 用于一对多或多对多。")
    ValueExpression: str = Field(..., description="值的微流表达式。规则：字符串值必须用单引号包裹 (例如 'Hello World')；变量引用使用 $ 前缀 (例如 $MyVar)；通过 / 访问对象属性 (例如 $MyObject/Attribute)；枚举值使用完全限定名 (例如 MyModule.MyEnumeration.EnumValue)。")

class SimpleSortItem(BaseModel):
    AttributeName: str = Field(..., description="排序依据的属性名")
    Ascending: bool = Field(True, description="是否升序 (True/False)")

class UnifiedActivity(BaseModel):
    """
    【统一活动模型】
    这是一个包含所有活动可能用到字段的扁平大对象。
    LLM 只需要设置 ActivityType，然后根据 ActivityType 的含义填充对应的字段。
    """
    ActivityType: Literal[
        "Retrieve", "Change", "CreateObject", "Commit", "Delete", "Rollback",
        "CreateList", "ChangeList", "SortList", "FilterList", "FindList",
        "AggregateList", "ListOperation"
    ] = Field(..., description="必填。活动类型。根据此类型决定填写下方哪些字段。例如：'Retrieve' (获取数据，需要 EntityName, OutputVariable, SourceType)；'Change' (修改对象，需要 VariableName, Changes)；'CreateObject' (创建对象，需要 EntityName, OutputVariable)。")

    # --- 1. 核心对象/变量相关 (Core) ---
    VariableName: Optional[str] = Field(None, description="要操作的对象变量名。在 Change, Commit, Delete, Rollback 活动中是必填项。在 Retrieve, CreateObject, CreateList, ChangeList, ListOperation, FilterList, FindList, AggregateList 活动中，它作为输入或输出变量名。")
    EntityName: Optional[str] = Field(None, description="实体全名，格式: 'MyModule.EntityName'。在 CreateObject, CreateList, Retrieve (当 SourceType 为 Database) 活动中是必填项。")
    OutputVariable: Optional[str] = Field(None, description="用于存储活动结果的变量名。在 Retrieve, CreateObject, CreateList, ListOperation, FilterList, FindList, AggregateList 活动中是必填项。")
    
    # --- 2. Retrieve (获取数据) 专用 ---
    SourceType: Literal["Association", "Database"] = Field("Association", description="[Retrieve 必填] 数据检索的源类型。'Association' (通过关联) 或 'Database' (查库)。若为 'Database'，EntityName 必填；若为 'Association'，SourceVariable 和 AssociationName 必填。")
    SourceVariable: Optional[str] = Field(None, description="[Retrieve-Association 必填] 当 SourceType 为 'Association' 时，指定作为关联源的变量名称 (例如 $myObject)。")
    AssociationName: Optional[str] = Field(None, description="[Retrieve-Association 必填] 当 SourceType 为 'Association' 时，关联的完全限定名称 (格式: 'MyModule.AssociationName')。")
    XPathConstraint: Optional[str] = Field(None, description="[Retrieve-Database 可选] XPath 约束表达式，用于过滤结果。例如 `[Attribute = 'Value']`。遵循 Mendix 表达式语法：字符串值必须用单引号包裹；变量引用使用 $ 前缀；通过 / 访问对象属性。")
    RetrieveJustFirstItem: Optional[bool] = Field(False, description="[Retrieve] 是否只获取第一条。")
    Sorting: Optional[List[SimpleSortItem]] = Field(None, description="[Retrieve/SortList] 排序规则列表。在 SortList 活动中，Sorting 列表不能为空。例如：`[{'AttributeName': 'Name', 'Ascending': True}]`。")

    # --- 3. Change / CreateObject (修改/创建) 专用 ---
    Commit: Literal["No", "Yes", "YesWithoutEvents"] = Field("No", description="[Change/CreateObject 可选] 是否提交更改到数据库。默认为 No。'Yes' (提交并触发事件), 'YesWithoutEvents' (提交但不触发事件)。")
    RefreshClient: bool = Field(False, description="[Change/CreateObject/Rollback 可选] 是否在活动执行后刷新客户端用户界面。默认为 False。")
    Changes: Optional[List[SimpleChangeItem]] = Field(None, description="[Change 必填] 要应用的更改列表，每个项是一个 SimpleChangeItem。此列表不能为空。")
    InitialValues: Optional[List[SimpleChangeItem]] = Field(None, description="[CreateObject 可选] 用于新创建对象的初始值列表，每个项包含 AttributeName 和 ValueExpression。例如：`[{'AttributeName': 'Name', 'ValueExpression': ''New Item''}]`。")

    # --- 4. List Operations (列表操作) 专用 ---
    ListVariable: Optional[str] = Field(None, description="[ListOperation/Filter/Find/Sort/ChangeList/Aggregate 必填] 列表变量的名称 (例如 $myList)。ListVariable 和 InputListVariable 这两个字段是互斥的，用于指定操作的目标列表或输入列表，填其中一个即可。")
    InputListVariable: Optional[str] = Field(None, description="[Aggregate/ListOperation/Filter/Find/Sort/ChangeList 必填] 列表变量的名称 (例如 $myList)。ListVariable 和 InputListVariable 这两个字段是互斥的，用于指定操作的目标列表或输入列表，填其中一个即可。")
    Operation: Optional[Literal["Set", "Add", "Remove", "Clear"]] = Field(None, description="[ChangeList 必填] 对列表执行的操作类型，例如 'Set' (替换), 'Add' (添加), 'Remove' (移除), 'Clear' (清空)。")
    OperationType: Optional[Literal["Head", "Tail"]] = Field(None, description="[ListOperation 必填] 具体操作类型，例如 'Head' (获取列表第一个元素), 'Tail' (获取列表除第一个元素外的所有元素)。目前仅支持 Head 和 Tail。")
    BinaryOperationListVariable: Optional[str] = Field(None, description="[ListOperation-Union/Intersect 必填] 当 OperationType 为 'Union' 或 'Intersect' 时，第二个列表的变量名 (例如 $anotherList)。")
    
    # --- 5. Logic & Calculation (逻辑/计算) 专用 ---
    FilterBy: Optional[Literal["Attribute", "Association"]] = Field(None, description="[FilterList 必填] 过滤依据: 'Attribute' (按属性过滤) 或 'Association' (按关联过滤)。")
    FindBy: Optional[Literal["Expression", "Attribute", "Association"]] = Field(None, description="[FindList 必填] 查找依据: 'Expression' (按表达式查找), 'Attribute' (按属性查找) 或 'Association' (按关联查找)。")
    MemberName: Optional[str] = Field(None, description="[FilterList/FindList 必填 (当 FilterBy/FindBy 为 Attribute/Association)] 属性名或关联名。")
    Expression: Optional[str] = Field(None, description="[FindList (当 FindBy 为 Expression)/FilterList 必填] 表达式。在 ChangeList 中也可用作 ValueExpression。规则：字符串值必须用单引号包裹；变量引用使用 $ 前缀；通过 / 访问对象属性；枚举值使用完全限定名。")
    Function: Optional[Literal["Sum", "Average", "Count", "Minimum", "Maximum", "All", "Any", "Reduce"]] = Field(None, description="[AggregateList 必填] 聚合函数: 'Sum', 'Average', 'Count', 'Minimum', 'Maximum', 'All', 'Any', 'Reduce'。")
    Attribute: Optional[str] = Field(None, description="[AggregateList 必填 (当 Function 为 Sum/Average/Minimum/Maximum)] 要进行计算的属性名。必需是数字属性。")

class SimpleMicroflowRequest(BaseModel):
    FullPath: str = Field(..., description="微流完整路径，必须包含模块名，例如 'MyModule/SubFolder/MyMicroflow' 或 'MyModule/MyMicroflow'。")
    ReturnType: str = Field(..., description="返回值类型。支持基本类型 (例如 'String', 'Integer', 'Boolean')，实体类型 (例如 'MyModule.Customer')，实体列表 (例如 'List(MyModule.Order)')，或 'Void' (表示不返回任何值)。")
    ReturnExp: Optional[str] = Field(None, description="返回值表达式。如果 ReturnType 为 'Void'，则此字段应为 null 或空字符串。规则：字符串值必须用单引号包裹；变量引用使用 $ 前缀；通过 / 访问对象属性；枚举值使用完全限定名。")
    Parameters: List[SimpleParameter] = Field([], description="输入参数列表。")
    Activities: List[UnifiedActivity] = Field(..., description="活动列表，将按顺序执行。请注意，任何变量在使用之前都必须先通过上游活动 (如 CreateObject 或 Retrieve) 进行定义。")


# ==========================================
# 2. 适配器逻辑 (Simple -> Complex)
# ==========================================

def _parse_data_type(type_str: str) -> complex_dto.DataTypeDefinition:
    """将简单字符串类型转换为后端复杂的 DataTypeDefinition"""
    if not type_str:
        return complex_dto.DataTypeDefinition(TypeName="Void")
        
    type_str = type_str.strip()
    
    # 处理 List 类型: "List(MyModule.Entity)"
    if type_str.startswith("List(") and type_str.endswith(")"):
        inner_type = type_str[5:-1]
        return complex_dto.DataTypeDefinition(TypeName="List", QualifiedName=inner_type)
    
    # 基本类型映射
    primitives = ["String", "Integer", "Long", "Decimal", "Boolean", "DateTime", "Binary", "Void"]
    if type_str in primitives:
        return complex_dto.DataTypeDefinition(TypeName=type_str)
    
    # 枚举或对象 (包含点号通常是对象或枚举)
    if "." in type_str:
        return complex_dto.DataTypeDefinition(TypeName="Object", QualifiedName=type_str)
    
    # 默认为 Object
    return complex_dto.DataTypeDefinition(TypeName="Object", QualifiedName=type_str)

def _adapt_activity(simple: UnifiedActivity) -> Any:
    """将 UnifiedActivity 转换为具体的 pymx Activity 对象"""
    at = simple.ActivityType
    
    # 1. Retrieve
    if at == "Retrieve":
        return complex_dto.RetrieveActivity(
            SourceType=simple.SourceType,
            OutputVariable=simple.OutputVariable,
            SourceVariable=simple.SourceVariable,
            AssociationName=simple.AssociationName,
            EntityName=simple.EntityName,
            XPathConstraint=simple.XPathConstraint,
            RetrieveJustFirstItem=simple.RetrieveJustFirstItem,
            Sorting=[complex_dto.SortItem(**s.model_dump()) for s in (simple.Sorting or [])]
        )
    
    # 2. Change
    elif at == "Change":
        changes = []
        if simple.Changes:
            for c in simple.Changes:
                changes.append(complex_dto.ChangeItem(
                    AttributeName=c.AttributeName,
                    AssociationName=c.AssociationName,
                    Action=c.Action,
                    ValueExpression=c.ValueExpression
                ))
        return complex_dto.ChangeActivity(
            VariableName=simple.VariableName,
            EntityName=simple.EntityName or "", 
            Commit=simple.Commit,
            Changes=changes
        )

    # 3. CreateObject
    elif at == "CreateObject":
        init_values = []
        # 优先使用 InitialValues，如果没有则尝试读取 Changes (以防 LLM 填错字段)
        source_values = simple.InitialValues or simple.Changes or []
        for iv in source_values:
            if iv.AttributeName and iv.ValueExpression:
                init_values.append(complex_dto.InitialValueItem(
                    AttributeName=iv.AttributeName,
                    ValueExpression=iv.ValueExpression
                ))
        return complex_dto.CreateObjectActivity(
            EntityName=simple.EntityName,
            OutputVariable=simple.OutputVariable,
            Commit=simple.Commit,
            RefreshClient=simple.RefreshClient,
            InitialValues=init_values
        )

    # 4. Commit
    elif at == "Commit":
        return complex_dto.CommitActivity(VariableName=simple.VariableName, RefreshClient=simple.RefreshClient)
        
    # 5. Delete
    elif at == "Delete":
        return complex_dto.DeleteActivity(VariableName=simple.VariableName)
        
    # 6. Rollback
    elif at == "Rollback":
        return complex_dto.RollbackActivity(VariableName=simple.VariableName, RefreshClient=simple.RefreshClient)
    
    # 7. CreateList
    elif at == "CreateList":
        return complex_dto.CreateListActivity(EntityName=simple.EntityName, OutputVariable=simple.OutputVariable)
        
    # 8. AggregateList
    elif at == "AggregateList":
        return complex_dto.AggregateListActivity(
            InputListVariable=simple.InputListVariable or simple.ListVariable, # 容错
            OutputVariable=simple.OutputVariable,
            Function=simple.Function,
            Attribute=simple.Attribute,
            Expression=simple.Expression
        )
        
    # 9. ListOperation
    elif at == "ListOperation":
        return complex_dto.ListOperationActivity(
            OperationType=simple.OperationType or "Head",
            InputListVariable=simple.InputListVariable or simple.ListVariable,
            OutputVariable=simple.OutputVariable,
            BinaryOperationListVariable=simple.BinaryOperationListVariable
        )
    
    # 10. FilterList
    elif at == "FilterList":
        return complex_dto.FilterListActivity(
            FilterBy=simple.FilterBy,
            ListVariable=simple.ListVariable,
            OutputVariable=simple.OutputVariable,
            MemberName=simple.MemberName,
            Expression=simple.Expression
        )
    
    # 11. FindList
    elif at == "FindList":
        return complex_dto.FindListActivity(
            FindBy=simple.FindBy,
            ListVariable=simple.ListVariable,
            OutputVariable=simple.OutputVariable,
            MemberName=simple.MemberName,
            Expression=simple.Expression
        )
        
    # 12. ChangeList
    elif at == "ChangeList":
        return complex_dto.ChangeListActivity(
            Operation=simple.Operation,
            ListVariable=simple.ListVariable,
            ValueExpression=simple.Expression 
        )
        
    # 13. SortList
    elif at == "SortList":
        return complex_dto.SortListActivity(
            ListVariable=simple.ListVariable,
            OutputVariable=simple.OutputVariable,
            Sorting=[complex_dto.SortItem(**s.model_dump()) for s in (simple.Sorting or [])]
        )

    return None

def adapt_requests(simple_requests: List[SimpleMicroflowRequest]) -> List[complex_dto.MicroflowRequest]:
    """将简单请求列表转换为后端请求列表"""
    complex_requests = []
    
    for req in simple_requests:
        # 1. 转换参数
        params = []
        for p in req.Parameters:
            params.append(complex_dto.MicroflowParameter(
                Name=p.Name,
                Type=_parse_data_type(p.Type)
            ))
            
        # 2. 转换活动
        activities = []
        for act in req.Activities:
            try:
                converted_act = _adapt_activity(act)
                if converted_act:
                    activities.append(converted_act)
            except Exception as e:
                raise ValueError(f"Failed to adapt activity {act.ActivityType}: {str(e)}")
                
        # 3. 构造复杂对象
        complex_req = complex_dto.MicroflowRequest(
            FullPath=req.FullPath,
            ReturnType=_parse_data_type(req.ReturnType),
            ReturnExp=req.ReturnExp,
            Parameters=params,
            Activities=activities
        )
        complex_requests.append(complex_req)
        
    return complex_requests


# ==========================================
# 3. 工具定义
# ==========================================

@mcp.tool(
    name="ensure_microflows",
    description="在 Mendix 中创建或更新微流。简化模式：所有 Activity 属性都在同一级，请根据 ActivityType 选择性填写对应的字段。字符串值请务必加引号。"
)
async def create_mendix_microflows(requests: List[SimpleMicroflowRequest]) -> str:
    """
    创建微流的入口点。
    
    Args:
        requests: 简化的微流定义列表
    """
    try:
        # 1. 适配数据
        complex_reqs = adapt_requests(requests)
        
        # 2. 调用核心逻辑
        report = microflow.create_microflows(ctx, complex_reqs)
        return report
        
    except Exception as e:
        import traceback
        return f"Error creating microflows: {str(e)}\n{traceback.format_exc()}"