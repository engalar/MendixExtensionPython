import traceback
from typing import List, Literal, Optional, Union, Dict, Callable, Any
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

# System & Mendix Imports
from System import ValueTuple, String, Array
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows import (
    IMicroflow,
    IActionActivity,
    MicroflowReturnValue,
    IHead,
    ITail,
    IUnion,
    IIntersect,
    IContains,
    ISort,
    AttributeSorting
)
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions import (
    CommitEnum,
    ChangeActionItemType,
    AggregateFunctionEnum,
)
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType
from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration, IEnumerationValue
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import (
    IEntity,
    IAttribute,
    IAssociation,
)
from pymx.model.util import TransactionManager
from pymx.model import folder as _folder
from pymx.model import module
import importlib
from pymx.model.dto import type_microflow
importlib.reload(type_microflow)
from pymx.model.dto.type_microflow import (
    DataTypeDefinition,
    MicroflowParameter,
    BaseActivity,
    RetrieveActivity,
    AggregateListActivity,
    ListOperationActivity,
    CommitActivity,
    ChangeActivity,
    MicroflowRequest,
    CreateMicroflowsToolInput,
)

# ==========================================
# PART 2: Context & Utilities
# ==========================================

class BuilderContext:
    def __init__(self, global_ctx, folder):
        self.ctx = global_ctx
        self.app = global_ctx.CurrentApp
        self.folder = folder
        self.utils = MendixUtils(global_ctx.CurrentApp, global_ctx.domainModelService)

class MendixUtils:
    def __init__(self, model, domainModelService):
        self.model = model
        self.domainModelService = domainModelService

    def get_association(self, name: str) -> IAssociation:
        m = module.ensure_module(self.model, name.split('.')[0])
        a = name.split('.')[1]
        entityAssociations = self.domainModelService.GetAllAssociations(self.model, m)
        association = next((ea.Association for ea in entityAssociations
                  if ea.Association.Name == a), None)
        return association

    def get_entity(self, name: str) -> IEntity:
        obj = self.model.ToQualifiedName[IEntity](name).Resolve()
        if not obj:
            raise ValueError(f"Entity not found: {name}")
        return obj

    def get_attribute(self, entity: IEntity, attr_name: str) -> IAttribute:
        found = next((a for a in entity.GetAttributes() if a.Name == attr_name), None)
        if not found:
            raise ValueError(f"Attribute '{attr_name}' not found in '{entity.Name}'")
        return found


# ==========================================
# PART 3: Activity Handlers
# ==========================================

HandlerFunc = Callable[[BuilderContext, Any], List[IActionActivity]]

class ActivityDispatcher:
    def __init__(self):
        self._handlers: Dict[str, HandlerFunc] = {}
        self._register_defaults()

    def register(self, key: str, handler: HandlerFunc):
        self._handlers[key] = handler

    def dispatch(self, ctx: BuilderContext, activity_dto: BaseActivity) -> List[IActionActivity]:
        handler = self._handlers.get(activity_dto.activity_type)
        if not handler:
            raise NotImplementedError(
                f"No handler registered for activity type: {activity_dto.activity_type}"
            )
        return handler(ctx, activity_dto)

    def _register_defaults(self):
        self.register("Retrieve", self._handle_retrieve)
        self.register("Change", self._handle_change)
        self.register("Commit", self._handle_commit)
        self.register("AggregateList", self._handle_aggregate)
        self.register("ListOperation", self._handle_list_operation)

    # --- Individual Handlers ---

    def _handle_retrieve(self, ctx: BuilderContext, act: RetrieveActivity) -> List[IActionActivity]:
        # 1. Association Retrieve
        if act.source_type == "Association":
            if not act.association_name or not act.source_variable:
                raise ValueError("Retrieve by Association requires 'AssociationName' and 'SourceVariable'.")

            assoc = ctx.utils.get_association(act.association_name)
            if not assoc:
                raise ValueError(f"Association '{act.association_name}' not found.")

            sdk_act = ctx.ctx.microflowActivitiesService.CreateAssociationRetrieveSourceActivity(
                ctx.app, assoc, act.output_variable, act.source_variable
            )
            return [sdk_act]

        # 2. Database Retrieve
        elif act.source_type == "Database":
            if not act.entity_name:
                raise ValueError("Retrieve by Database requires 'EntityName'.")

            entity = ctx.utils.get_entity(act.entity_name)

            # 构造 Range Tuple (StartIndex, Amount)
            range_tuple = None
            if act.range_index or act.range_amount:
                start_exp = ctx.ctx.microflowExpressionService.CreateFromString(
                    act.range_index if act.range_index else "0"
                )
                # 如果没有amount，通常传null或不做处理，但CreateDatabaseRetrieveSourceActivity签名可能需要
                # 根据API: (IMicroflowExpression startingIndex, IMicroflowExpression amount) range
                # 如果不需要limit，amount 应该是 null 吗？Python.NET 中 null 对应 None
                amount_exp = None
                if act.range_amount:
                    amount_exp = ctx.ctx.microflowExpressionService.CreateFromString(act.range_amount)

                # C# ValueTuple 构造
                range_tuple = ValueTuple.Create(start_exp, amount_exp)
            else:
                # 默认值
                range_tuple = ValueTuple.Create(
                    ctx.ctx.microflowExpressionService.CreateFromString("0"),
                    None # 无限制
                )
            if range_tuple == None and act.retrieve_just_first_item != None:
                range_tuple = act.retrieve_just_first_item

            if range_tuple == None:
                # FIX: 在RetrieveActivity加入DTO校验，而不是在此处
                raise Exception('RetrieveJustFirstItem and [RangeIndex RangeAmount]只能二选一')

            # 构造 Sorting
            sort_list = []
            if act.sorting:
                for s in act.sorting:
                    attr = ctx.utils.get_attribute(entity, s.attribute_name)
                    direction = False if s.ascending else True
                    sort_list.append(AttributeSorting(attr, direction))

            sort_array = Array[AttributeSorting](sort_list)

            # 调用 SDK
            # CreateDatabaseRetrieveSourceActivity(model, outputVar, entity, xPath, range, sortingAttributes)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateDatabaseRetrieveSourceActivity(
                ctx.app,
                act.output_variable,
                entity,
                act.xpath_constraint, # 可为 None
                range_tuple,
                sort_array
            )
            return [sdk_act]

        else:
            raise ValueError(f"Unknown Retrieve source type: {act.source_type}")

    def _handle_commit(self, ctx: BuilderContext, act: CommitActivity) -> List[IActionActivity]:
        # public IActionActivity CreateCommitObjectActivity(IModel model, string commitVariableName, bool withEvents = true, bool refreshInClient = false)
        # 按照用户提供的API签名，第四个参数是 refreshInClient
        sdk_act = ctx.ctx.microflowActivitiesService.CreateCommitObjectActivity(
            ctx.app, 
            act.variable_name, 
            True, # withEvents 默认为 True
            act.refresh_client # refreshInClient
        )
        return [sdk_act]

    def _handle_change(self, ctx: BuilderContext, act: ChangeActivity) -> List[IActionActivity]:
        entity = ctx.utils.get_entity(act.entity_name)
        result_acts = []

        commit_enum = CommitEnum.No
        if act.commit == "Yes":
            commit_enum = CommitEnum.Yes
        elif act.commit == "YesWithoutEvents":
            commit_enum = CommitEnum.YesWithoutEvents

        for item in act.changes:
            attr = ctx.utils.get_attribute(entity, item.attribute_name)
            val_expr = ctx.ctx.microflowExpressionService.CreateFromString(
                item.value_expression
            )

            # Map Action string to Enum
            action_map = {
                "Set": ChangeActionItemType.Set,
                "Add": ChangeActionItemType.Add,
                "Remove": ChangeActionItemType.Remove
            }
            change_type = action_map.get(item.action, ChangeActionItemType.Set)

            sdk_act = ctx.ctx.microflowActivitiesService.CreateChangeAttributeActivity(
                ctx.app,
                attr,
                change_type,
                val_expr,
                act.variable_name,
                commit_enum,
            )
            result_acts.append(sdk_act)

        return result_acts

    def _handle_aggregate(self, ctx: BuilderContext, act: AggregateListActivity) -> List[IActionActivity]:
        func_map = {
            "Count": AggregateFunctionEnum.Count,
            "Sum": AggregateFunctionEnum.Sum,
            "Average": AggregateFunctionEnum.Average,
            "Minimum": AggregateFunctionEnum.Minimum,
            "Maximum": AggregateFunctionEnum.Maximum,
        }
        if act.function not in func_map:
            raise ValueError(f"Unknown aggregate function: {act.function}")

        sdk_act = ctx.ctx.microflowActivitiesService.CreateAggregateListActivity(
            ctx.app,
            act.input_list_variable,
            act.output_variable,
            func_map[act.function]
        )
        return [sdk_act]

    def _handle_list_operation(self, ctx: BuilderContext, act: ListOperationActivity) -> List[IActionActivity]:
        op_instance = None
        op_type = act.operation_type

        if op_type == "Head":
            op_instance = ctx.app.Create[IHead]()
        elif op_type == "Tail":
            op_instance = ctx.app.Create[ITail]()
        elif op_type == "Union":
            op_instance = ctx.app.Create[IUnion]()
        elif op_type == "Intersect":
            op_instance = ctx.app.Create[IIntersect]()
        elif op_type == "Contains":
            op_instance = ctx.app.Create[IContains]()
        elif op_type == "Sort":
            op_instance = ctx.app.Create[ISort]()
        else:
            raise ValueError(f"Unsupported list operation: {op_type}")

        sdk_act = None
        if act.binary_operation_list_variable:
            # 目前不支持binary operation
            sdk_act = ctx.ctx.microflowActivitiesService.CreateListOperationActivity(
                ctx.app, act.input_list_variable, act.output_variable, op_instance#, act.binary_operation_list_variable
            )
        else:

            sdk_act = ctx.ctx.microflowActivitiesService.CreateListOperationActivity(
                ctx.app, act.input_list_variable, act.output_variable, op_instance
            )

        # 实际上 SDK Service 可能会处理 Binary Operation 的第二参数绑定
        # 如果 Service 没有暴露，需要手动设置，这里假设 Service 简化了流程
        # 或者是用户需要保证 BinaryOperationListVariable 被逻辑正确处理 (暂未实现深入的 List2 绑定，依赖 Service API 行为)

        return [sdk_act]

# Global Dispatcher Instance
_dispatcher = ActivityDispatcher()

# ==========================================
# PART 4: Main Builder Logic
# ==========================================

class MicroflowBuilder:
    def __init__(self, ctx: BuilderContext, request: MicroflowRequest):
        self.ctx = ctx
        self.req = request
        self.mf: Optional[IMicroflow] = None
        self.logs: List[str] = []

    def log(self, msg: str):
        self.logs.append(f"[Builder-{self.req.full_path}] {msg}")

    def _create_data_type(self, type_info: DataTypeDefinition) -> Optional[DataType]:
        type_name = type_info.type_name.lower()

        if type_name == "string": return DataType.String
        if type_name == "integer": return DataType.Integer
        if type_name == "long": return DataType.Long
        if type_name == "decimal": return DataType.Decimal
        if type_name == "boolean": return DataType.Boolean
        if type_name == "datetime": return DataType.DateTime
        if type_name == "binary": return DataType.Binary
        if type_name == "void": return DataType.Void
        
        if type_name == "object":
            return DataType.Object(self.ctx.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "list":
            return DataType.List(self.ctx.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "enumeration":
            return DataType.Enumeration(self.ctx.app.ToQualifiedName[IEnumeration](type_info.qualified_name))
        raise ValueError(f"不支持的数据类型 '{type_name}'。")

    def build(self):
        self.log("Starting build process...")
        try:
            self.mf = self._build_shell()
            self.log(f"Shell created/found: {self.mf.Name}")
        except Exception as e:
            self.log(f"Error building shell: {e}")
            raise

        try:
            self._build_body()
        except Exception as e:
            self.log(f"Error building body: {e}")
            self.log(traceback.format_exc())
            raise

        return self.mf

    def _build_shell(self) -> IMicroflow:
        mf_name = self.req.full_path.split("/")[-1]
        module_name = self.req.full_path.split("/")[0]

        params = [
            ValueTuple.Create[String, DataType](p.name, self._create_data_type(p.type))
            for p in self.req.parameters
        ]
        return_type = self._create_data_type(self.req.return_type)

        existing = next(
            (m for m in self.ctx.folder.GetDocuments() if m.Name == mf_name), None
        )

        if existing:
            self.mf = self.ctx.app.ToQualifiedName[IMicroflow](
                f"{module_name}.{mf_name}"
            ).Resolve()
            self.mf.ReturnType = return_type
            self.ctx.ctx.microflowService.Initialize(self.mf, params)
        else:
            if self.req.return_exp:
                ret_exp = self.ctx.ctx.microflowExpressionService.CreateFromString(
                    self.req.return_exp
                )
                ret_val = MicroflowReturnValue(return_type, ret_exp)
            else:
                ret_val = MicroflowReturnValue(
                    return_type,
                    (self.ctx.ctx.microflowExpressionService.CreateFromString("empty")
                     if self.req.return_type.type_name == "Void" else
                     self.ctx.ctx.microflowExpressionService.CreateFromString("empty"))
                )

            self.mf = self.ctx.ctx.microflowService.CreateMicroflow(
                self.ctx.app, self.ctx.folder, mf_name, ret_val, params
            )

        return self.mf

    def _build_body(self):
        self.log(f"Building body with {len(self.req.activities) if self.req.activities else 0} activities.")
        if not self.req.activities:
            return

        all_sdk_activities: List[IActionActivity] = []

        for i, act_dto in enumerate(self.req.activities):
            try:
                self.log(f"Dispatching Activity [{i}] Type: {act_dto.activity_type}")
                generated_acts = _dispatcher.dispatch(self.ctx, act_dto)
                all_sdk_activities.extend(generated_acts)
            except Exception as e:
                self.log(f"  -> ERROR in dispatch: {str(e)}")
                raise

        if all_sdk_activities:
            try:
                csharp_array = Array[IActionActivity](all_sdk_activities[::-1])
                self.ctx.ctx.microflowService.TryInsertAfterStart(self.mf, csharp_array)
            except Exception as e:
                self.log(f"ERROR in TryInsertAfterStart: {str(e)}")
                raise

def create_microflows(ctx, tool_input: CreateMicroflowsToolInput, tx=None) -> str:
    report = ["Starting..."]
    for req in tool_input.requests:
        if tx:
            _do_create(ctx, report, req)
            continue
        try:
            with TransactionManager(ctx.CurrentApp, f"MF: {req.full_path}"):
                _do_create(ctx, report, req)
        except Exception as e:
            report.append(f"Error {req.full_path}: {str(e)}")
            report.append(traceback.format_exc())

    return "\n".join(report)

def _do_create(ctx, report, req):
    folder, docName, moduleName = _folder.ensure_folder(ctx.CurrentApp, req.full_path)
    build_ctx = BuilderContext(ctx, folder)
    builder = MicroflowBuilder(build_ctx, req)
    try:
        builder.build()
        report.append(f"Success: {req.full_path}")
    except Exception as e:
        report.append(f"Failed to build {req.full_path}: {e}")
    finally:
        if builder.logs:
            report.append("--- Builder Logs ---")
            report.extend(builder.logs)
            report.append("--------------------")
