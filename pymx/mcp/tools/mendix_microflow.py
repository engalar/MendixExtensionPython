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
    Type: str = Field(description="参数数据类型，例如 'String', 'Integer', 'Boolean', 'MyModule.Customer'")

class SimpleChangeItem(BaseModel):
    """用于 Change 和 CreateObject 的赋值项"""
    AttributeName: Optional[str] = Field(None, description="要赋值的属性名 (例如 'Name', 'Age')")
    AssociationName: Optional[str] = Field(None, description="要设置的关联名 (例如 'MyModule.Customer_Order')")
    Action: Literal["Set", "Add", "Remove"] = Field("Set", description="操作类型，默认为 Set")
    ValueExpression: str = Field(..., description="值的微流表达式。注意：字符串值必须用单引号包裹 (例如 'Hello')，变量使用 $前缀 (例如 $MyVar)")

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
    ] = Field(..., description="必填。活动类型。根据此类型决定填写下方哪些字段。")

    # --- 1. 核心对象/变量相关 (Core) ---
    VariableName: Optional[str] = Field(None, description="[Change/Commit/Delete/Rollback 必填] 要操作的对象变量名。")
    EntityName: Optional[str] = Field(None, description="[CreateObject/CreateList/Retrieve(Database) 必填] 实体全名，格式: 'MyModule.EntityName'。")
    OutputVariable: Optional[str] = Field(None, description="[Retrieve/Create/ListOps/Aggregate 必填] 用于存储结果的变量名。")
    
    # --- 2. Retrieve (获取数据) 专用 ---
    SourceType: Literal["Association", "Database"] = Field("Association", description="[Retrieve] 数据源类型。'Association'(通过关联) 或 'Database'(查库)。")
    SourceVariable: Optional[str] = Field(None, description="[Retrieve-Association 必填] 拥有关联的源对象变量名。")
    AssociationName: Optional[str] = Field(None, description="[Retrieve-Association 必填] 关联名称，格式: 'MyModule.Assoc_Name'。")
    XPathConstraint: Optional[str] = Field(None, description="[Retrieve-Database 可选] XPath 约束，例如 '[Name = $Var]'。")
    RetrieveJustFirstItem: Optional[bool] = Field(False, description="[Retrieve] 是否只获取第一条。")
    Sorting: Optional[List[SimpleSortItem]] = Field(None, description="[Retrieve/SortList] 排序规则列表。")

    # --- 3. Change / CreateObject (修改/创建) 专用 ---
    Commit: Literal["No", "Yes", "YesWithoutEvents"] = Field("No", description="[Change/CreateObject] 是否提交到数据库。")
    RefreshClient: bool = Field(False, description="[Change/CreateObject] 是否刷新客户端。")
    Changes: Optional[List[SimpleChangeItem]] = Field(None, description="[Change] 变更项列表。")
    InitialValues: Optional[List[SimpleChangeItem]] = Field(None, description="[CreateObject] 初始值列表。结构同 Changes。")

    # --- 4. List Operations (列表操作) 专用 ---
    ListVariable: Optional[str] = Field(None, description="[ListOperation/Filter/Find/Sort/ChangeList] 输入列表的变量名。")
    InputListVariable: Optional[str] = Field(None, description="[Aggregate/ListOperation] 输入列表的变量名 (同 ListVariable，填其中一个即可)。")
    Operation: Optional[str] = Field(None, description="[ChangeList 必填] 操作类型: 'Set', 'Add', 'Remove', 'Clear'。")
    OperationType: Optional[str] = Field(None, description="[ListOperation 必填] 操作类型: 'Head', 'Tail', 'Union', 'Intersect', 'Contains'。")
    BinaryOperationListVariable: Optional[str] = Field(None, description="[ListOperation-Union/Intersect] 第二个列表的变量名。")
    
    # --- 5. Logic & Calculation (逻辑/计算) 专用 ---
    FilterBy: Optional[str] = Field(None, description="[FilterList] 'Attribute' 或 'Association'。")
    FindBy: Optional[str] = Field(None, description="[FindList] 'Expression', 'Attribute' 或 'Association'。")
    MemberName: Optional[str] = Field(None, description="[FilterList/FindList] 属性名或关联名。")
    Expression: Optional[str] = Field(None, description="[Find/Filter/ChangeList] 表达式。注意：字符串需加引号。")
    Function: Optional[str] = Field(None, description="[AggregateList 必填] 聚合函数: 'Sum', 'Count', 'Average', 'Minimum', 'Maximum'。")
    Attribute: Optional[str] = Field(None, description="[AggregateList] 要聚合的属性名 (Count除外)。")

class SimpleMicroflowRequest(BaseModel):
    FullPath: str = Field(..., description="微流完整路径，必须包含模块名，例如 'MyModule.SubFolder.MyMicroflow' 或 'MyModule/MyMicroflow'。")
    ReturnType: str = Field(..., description="返回值类型。简单字符串，例如 'String', 'Integer', 'Void', 'MyModule.Customer', 'List(MyModule.Order)'。")
    ReturnExp: Optional[str] = Field(None, description="返回值表达式。如果是 Void 类型则留空。注意：字符串值需加引号。")
    Parameters: List[SimpleParameter] = Field([], description="输入参数列表。")
    Activities: List[UnifiedActivity] = Field(..., description="活动列表，将按顺序执行。请确保引用变量前，该变量已在之前的步骤中定义。")


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