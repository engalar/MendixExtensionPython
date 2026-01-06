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
    AttributeSorting,
    IListOperation
)
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions import (
    CommitEnum,
    ChangeActionItemType,
    AggregateFunctionEnum,
    ChangeListActionOperation,
)
from Mendix.StudioPro.ExtensionsAPI.Model.DataTypes import DataType
from Mendix.StudioPro.ExtensionsAPI.Model.Enumerations import IEnumeration, IEnumerationValue
from Mendix.StudioPro.ExtensionsAPI.Model.DomainModels import (
    IEntity,
    IAttribute,
    IAssociation,
)
from Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions import IMicroflowExpression

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
    CreateObjectActivity,
    DeleteActivity,
    RollbackActivity,
    CreateListActivity,
    ChangeListActivity,
    SortListActivity,
    FilterListActivity,
    FindListActivity,
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
    

    def _create_data_type(self, type_info: DataTypeDefinition) -> Optional[DataType]:
        type_name = type_info.type_name.lower()

        if type_name == "string": return DataType.String
        if type_name == "integer": return DataType.Integer
        if type_name == "long": return DataType.Long
        if type_name == "decimal": return DataType.Decimal
        if type_name == "boolean": return DataType.Boolean
        if type_name == "datetime": return DataType.DateTime

        # 
        if type_name == "binary": return DataType.Binary
        if type_name == "void": return DataType.Void
        
        if type_name == "object":
            return DataType.Object(self.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "list":
            return DataType.List(self.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "enumeration":
            return DataType.Enumeration(self.app.ToQualifiedName[IEnumeration](type_info.qualified_name))
        raise ValueError(f"不支持的数据类型 '{type_name}'。")

class MendixUtils:
    def __init__(self, model, domainModelService):
        self.model = model
        self.domainModelService = domainModelService

    def get_association(self, name: str) -> IAssociation:
        # 支持 "Module.Association" 格式
        parts = name.split('.')
        if len(parts) != 2:
             # 尝试直接查找
             assoc = self.model.ToQualifiedName[IAssociation](name)
             if assoc: return assoc
             raise ValueError(f"Invalid association format: {name}")
             
        m = module.ensure_module(self.model, parts[0])
        a = parts[1]
        entityAssociations = self.domainModelService.GetAllAssociations(self.model, m)
        association = next((ea.Association for ea in entityAssociations
                  if ea.Association.Name == a), None)
        if not association:
             # Fallback
             association = self.model.ToQualifiedName[IAssociation](name)
        
        if not association:
            raise ValueError(f"Association not found: {name}")
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
    
    def get_attribute2(self, name: str) -> IAttribute:
        # Parse Module.Entity.Attribute
        parts = name.split('.')
        if len(parts) < 3:
             raise ValueError(f"Attribute qualified name too short: {name}")
        
        entity_qname = f"{parts[0]}.{parts[1]}"
        attr_name = parts[2]
        entity = self.get_entity(entity_qname)
        return self.get_attribute(entity, attr_name)


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
        self.register("CreateObject", self._handle_create_object)
        self.register("Delete", self._handle_delete)
        self.register("Rollback", self._handle_rollback)
        self.register("CreateList", self._handle_create_list)
        self.register("ChangeList", self._handle_change_list)
        self.register("SortList", self._handle_sort_list)
        self.register("FilterList", self._handle_filter_list)
        self.register("FindList", self._handle_find_list)

    # --- Helper ---
    
    def _create_expr(self, ctx, val: str) -> IMicroflowExpression:
        if val is None: return None
        return ctx.ctx.microflowExpressionService.CreateFromString(val)

    # --- Individual Handlers ---

    def _handle_create_object(self, ctx: BuilderContext, act: CreateObjectActivity) -> List[IActionActivity]:
        entity = ctx.utils.get_entity(act.entity_name)
        
        commit_enum = CommitEnum.No
        if act.commit == "Yes": commit_enum = CommitEnum.Yes
        elif act.commit == "YesWithoutEvents": commit_enum = CommitEnum.YesWithoutEvents

        # Prepare initial values params: (string attribute, IMicroflowExpression valueExpression)[]
        init_vals_array = [ValueTuple.Create[str, IMicroflowExpression](iv.attribute_name, self._create_expr(ctx, iv.value_expression)) for iv in act.initial_values]
        
        sdk_act = ctx.ctx.microflowActivitiesService.CreateCreateObjectActivity(
            ctx.app,
            entity,
            act.output_variable,
            commit_enum,
            act.refresh_client,
            init_vals_array
        )
        return [sdk_act]

    def _handle_delete(self, ctx: BuilderContext, act: DeleteActivity) -> List[IActionActivity]:
        sdk_act = ctx.ctx.microflowActivitiesService.CreateDeleteObjectActivity(
            ctx.app, act.variable_name
        )
        return [sdk_act]

    def _handle_rollback(self, ctx: BuilderContext, act: RollbackActivity) -> List[IActionActivity]:
        sdk_act = ctx.ctx.microflowActivitiesService.CreateRollbackObjectActivity(
            ctx.app, act.variable_name, act.refresh_client
        )
        return [sdk_act]

    def _handle_create_list(self, ctx: BuilderContext, act: CreateListActivity) -> List[IActionActivity]:
        entity = ctx.utils.get_entity(act.entity_name)
        sdk_act = ctx.ctx.microflowActivitiesService.CreateCreateListActivity(
            ctx.app, entity, act.output_variable
        )
        return [sdk_act]

    def _handle_change_list(self, ctx: BuilderContext, act: ChangeListActivity) -> List[IActionActivity]:
        op_map = {
            "Set": ChangeListActionOperation.Set,
            "Add": ChangeListActionOperation.Add,
            "Remove": ChangeListActionOperation.Remove,
            "Clear": ChangeListActionOperation.Clear
        }
        op = op_map.get(act.operation, ChangeListActionOperation.Set)
        
        expr = self._create_expr(ctx, act.value_expression) if act.operation != "Clear" else None
        
        # Note: CreateChangeListActivity requires expression even for clear? 
        # API Doc: IMicroflowExpression changeValueExpression. 
        # If clear, maybe pass empty/null? Let's assume null is fine for Clear or Empty string.
        if expr is None and act.operation != "Clear":
             raise ValueError("ValueExpression is required for Set/Add/Remove list operations.")
        
        if expr is None:
             # Workaround if service requires non-null
             expr = self._create_expr(ctx, "empty")

        sdk_act = ctx.ctx.microflowActivitiesService.CreateChangeListActivity(
            ctx.app, op, act.list_variable, expr
        )
        return [sdk_act]

    def _handle_sort_list(self, ctx: BuilderContext, act: SortListActivity) -> List[IActionActivity]:
        # 构造 Sorting Params
        # CreateSortListActivity(model, listVar, outputVar, params AttributeSorting[])
        
        # We need to know the Entity to resolve attributes. 
        # The API doesn't take Entity, so it implies we need to resolve attributes based on context or just string?
        # AttributeSorting constructor takes IAttribute.
        # So we must infer entity from the list variable? The BuilderContext doesn't track variable types easily.
        # FIX: The SortListActivity DTO should probably include EntityName to help resolution, 
        # or we rely on the user providing fully qualified attribute names (Module.Entity.Attr).
        
        sort_list = []
        for s in act.sorting:
            # Try to resolve attribute using full name or partial if we knew entity
            # For now, assume s.attribute_name is Qualified (Module.Entity.Attr)
            attr = ctx.utils.get_attribute2(s.attribute_name)
            direction = False if s.ascending else True
            sort_list.append(AttributeSorting(attr, direction))

        sort_array = Array[AttributeSorting](sort_list)
        
        sdk_act = ctx.ctx.microflowActivitiesService.CreateSortListActivity(
            ctx.app, act.list_variable, act.output_variable, sort_array
        )
        return [sdk_act]

    def _handle_filter_list(self, ctx: BuilderContext, act: FilterListActivity) -> List[IActionActivity]:
        expr = self._create_expr(ctx, act.expression)
        
        if act.filter_by == "Association":
            assoc = ctx.utils.get_association(act.member_name)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateFilterListByAssociationActivity(
                ctx.app, assoc, act.list_variable, act.output_variable, expr
            )
            return [sdk_act]
        else: # Attribute
            attr = ctx.utils.get_attribute2(act.member_name)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateFilterListByAttributeActivity(
                ctx.app, attr, act.list_variable, act.output_variable, expr
            )
            return [sdk_act]

    def _handle_find_list(self, ctx: BuilderContext, act: FindListActivity) -> List[IActionActivity]:
        expr = self._create_expr(ctx, act.expression)
        
        if act.find_by == "Expression":
            sdk_act = ctx.ctx.microflowActivitiesService.CreateFindByExpressionActivity(
                ctx.app, act.list_variable, act.output_variable, expr
            )
        elif act.find_by == "Attribute":
            attr = ctx.utils.get_attribute2(act.member_name)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateFindByAttributeActivity(
                ctx.app, attr, act.list_variable, act.output_variable, expr
            )
        elif act.find_by == "Association":
            assoc = ctx.utils.get_association(act.member_name)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateFindByAssociationActivity(
                ctx.app, assoc, act.list_variable, act.output_variable, expr
            )
        else:
            raise ValueError(f"Unknown FindType: {act.find_by}")
            
        return [sdk_act]

    def _handle_retrieve(self, ctx: BuilderContext, act: RetrieveActivity) -> List[IActionActivity]:
        # 1. Association Retrieve
        if act.source_type == "Association":
            if not act.association_name or not act.source_variable:
                raise ValueError("Retrieve by Association requires 'AssociationName' and 'SourceVariable'.")

            assoc = ctx.utils.get_association(act.association_name)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateAssociationRetrieveSourceActivity(
                ctx.app, assoc, act.output_variable, act.source_variable
            )
            return [sdk_act]

        # 2. Database Retrieve
        elif act.source_type == "Database":
            if not act.entity_name:
                raise ValueError("Retrieve by Database requires 'EntityName'.")

            entity = ctx.utils.get_entity(act.entity_name)

            # 构造 Sorting
            sort_list = []
            if act.sorting:
                for s in act.sorting:
                    attr = ctx.utils.get_attribute(entity, s.attribute_name)
                    direction = False if s.ascending else True
                    sort_list.append(AttributeSorting(attr, direction))
            sort_array = Array[AttributeSorting](sort_list)

            # Two overloads: one with Range Tuple, one with retrieveJustFirstItem bool
            
            if act.retrieve_just_first_item is not None:
                # Use overload with bool
                sdk_act = ctx.ctx.microflowActivitiesService.CreateDatabaseRetrieveSourceActivity(
                    ctx.app,
                    act.output_variable,
                    entity,
                    act.xpath_constraint, 
                    act.retrieve_just_first_item,
                    sort_array
                )
            else:
                # Use overload with Range
                start_str = act.range_index if act.range_index else "0"
                start_exp = self._create_expr(ctx, start_str)
                
                amount_exp = None
                if act.range_amount:
                     amount_exp = self._create_expr(ctx, act.range_amount)
                else:
                     # CreateDatabaseRetrieveSourceActivity signature expects Tuple(Expr, Expr)
                     # If infinite, what to pass? Assuming API handles None or we pass -1?
                     # Usually for infinite list retrieve, amount is not constrained.
                     # If the API requires the tuple, we probably shouldn't use this overload if we want 'All' without limit.
                     # But CreateDatabaseRetrieveSourceActivity(..., range, ...) is the only one for list with range.
                     pass 
                
                # C# ValueTuple 构造
                range_tuple = ValueTuple.Create[IMicroflowExpression, IMicroflowExpression](start_exp, amount_exp)
                
                sdk_act = ctx.ctx.microflowActivitiesService.CreateDatabaseRetrieveSourceActivity(
                    ctx.app,
                    act.output_variable,
                    entity,
                    act.xpath_constraint,
                    range_tuple,
                    sort_array
                )
                
            return [sdk_act]

        else:
            raise ValueError(f"Unknown Retrieve source type: {act.source_type}")

    def _handle_commit(self, ctx: BuilderContext, act: CommitActivity) -> List[IActionActivity]:
        sdk_act = ctx.ctx.microflowActivitiesService.CreateCommitObjectActivity(
            ctx.app, 
            act.variable_name, 
            True, # withEvents 默认为 True
            act.refresh_client
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
            val_expr = self._create_expr(ctx, item.value_expression)

            # Map Action string to Enum
            action_map = {
                "Set": ChangeActionItemType.Set,
                "Add": ChangeActionItemType.Add,
                "Remove": ChangeActionItemType.Remove
            }
            change_type = action_map.get(item.action, ChangeActionItemType.Set)

            if item.attribute_name:
                attr = ctx.utils.get_attribute(entity, item.attribute_name)
                sdk_act = ctx.ctx.microflowActivitiesService.CreateChangeAttributeActivity(
                    ctx.app,
                    attr,
                    change_type,
                    val_expr,
                    act.variable_name,
                    commit_enum,
                )
                result_acts.append(sdk_act)
            elif item.association_name:
                assoc = ctx.utils.get_association(item.association_name)
                sdk_act = ctx.ctx.microflowActivitiesService.CreateChangeAssociationActivity(
                    ctx.app,
                    assoc,
                    change_type,
                    val_expr,
                    act.variable_name,
                    commit_enum,
                )
                result_acts.append(sdk_act)
            else:
                raise ValueError("ChangeItem must have either AttributeName or AssociationName")

        return result_acts

    def _handle_aggregate(self, ctx: BuilderContext, act: AggregateListActivity) -> List[IActionActivity]:
        func_map = {
            "Sum": AggregateFunctionEnum.Sum,
            "Average": AggregateFunctionEnum.Average,
            "Count": AggregateFunctionEnum.Count,
            "Minimum": AggregateFunctionEnum.Minimum,
            "Maximum": AggregateFunctionEnum.Maximum,
            "All": AggregateFunctionEnum.All,
            "Any": AggregateFunctionEnum.Any,
            "Reduce": AggregateFunctionEnum.Reduce,
        }
        sdk_act = None
        if act.function not in func_map:
            raise ValueError(f"Unknown aggregate function: {act.function}")
        
        enum_val = func_map[act.function]

        if act.function in ['Count']:
            sdk_act = ctx.ctx.microflowActivitiesService.CreateAggregateListActivity(
                ctx.app,
                act.input_list_variable,
                act.output_variable,
                enum_val
            )
        elif act.function in ['Sum', 'Average','Minimum', 'Maximum']:
            if act.expression:
                exp = self._create_expr(ctx, act.expression)
                sdk_act = ctx.ctx.microflowActivitiesService.CreateAggregateListByExpressionActivity(
                    ctx.app,
                    exp,
                    act.input_list_variable,
                    act.output_variable,
                    enum_val,
                )
            elif act.attribute:
                attribute = ctx.utils.get_attribute2(act.attribute)
                sdk_act = ctx.ctx.microflowActivitiesService.CreateAggregateListByAttributeActivity(
                    ctx.app,
                    attribute,
                    act.input_list_variable,
                    act.output_variable,
                    enum_val,
                )
            else:
                raise ValueError(f"Function {act.function} requires either Attribute or Expression.")

        elif act.function in ['All', 'Any']:
            if not act.expression: raise ValueError(f"{act.function} requires Expression.")
            exp = self._create_expr(ctx, act.expression)
            sdk_act = ctx.ctx.microflowActivitiesService.CreateAggregateListByExpressionActivity(
                ctx.app,
                exp,
                act.input_list_variable,
                act.output_variable,
                enum_val
            )
        elif act.function in ['Reduce']:
            if not act.expression or not act.init_expression or not act.result_type:
                raise ValueError("Reduce requires Expression, InitExpression, and ResultType.")
            
            dataType = ctx._create_data_type(act.result_type)
            initialValueExpression = self._create_expr(ctx, act.init_expression)
            exp = self._create_expr(ctx, act.expression)
            
            sdk_act = ctx.ctx.microflowActivitiesService.CreateReduceAggregateActivity(
                ctx.app,
                act.input_list_variable,
                act.output_variable,
                initialValueExpression,
                exp,
                dataType
            )
        
        if sdk_act is None:
            raise ValueError("Failed to create aggregate activity.")
        return [sdk_act]

    def _handle_list_operation(self, ctx: BuilderContext, act: ListOperationActivity) -> List[IActionActivity]:
        # Legacy support for Head/Tail, mapped to generic list operation interface if possible,
        # but the provided service 'CreateListOperationActivity' takes IListOperation.
        # We need to instantiate specific classes implementing IListOperation (IHead, ITail, etc.)
        
        op_instance = None
        op_type = act.operation_type

        if op_type == "Head":
            op_instance = ctx.app.Create[IHead]()
        elif op_type == "Tail":
            op_instance = ctx.app.Create[ITail]()
        # Other types like Union/Intersect are not in the provided DTO Literal yet, but logic is here:
        elif op_type == "Union":
            op_instance = ctx.app.Create[IUnion]()
        elif op_type == "Intersect":
            op_instance = ctx.app.Create[IIntersect]()
        elif op_type == "Contains":
            op_instance = ctx.app.Create[IContains]()
        else:
            raise ValueError(f"Unsupported list operation: {op_type}")

        sdk_act = ctx.ctx.microflowActivitiesService.CreateListOperationActivity(
            ctx.app, act.input_list_variable, act.output_variable, op_instance
        )
        
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
            ValueTuple.Create[String, DataType](p.name, self.ctx._create_data_type(p.type))
            for p in self.req.parameters
        ]
        return_type = self.ctx._create_data_type(self.req.return_type)

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