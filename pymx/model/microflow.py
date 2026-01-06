import traceback
from typing import List, Literal, Optional, Union, Dict, Callable, Any
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

# System & Mendix Imports (Strictly limited to Reference Code)
from System import ValueTuple, String, Array
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows import (
    IMicroflow,
    IActionActivity,
    MicroflowReturnValue,
    IHead,
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

# --- 3. 业务逻辑构建器 ---

# ==========================================
# PART 2: Context & Utilities
# ==========================================


class BuilderContext:
    """持有构建过程中的所有必要服务和状态"""

    def __init__(self, global_ctx, folder):
        self.ctx = global_ctx  # 包含 microflowActivitiesService 等
        self.app = global_ctx.CurrentApp  # 当前 IModel (CurrentApp)
        self.folder = folder  # 目标文件夹
        self.utils = MendixUtils(global_ctx.CurrentApp, global_ctx.domainModelService)  # 辅助工具


class MendixUtils:
    """封装底层的 SDK 查找逻辑"""

    def __init__(self, model,domainModelService):
        self.model = model
        self.domainModelService = domainModelService

    def get_association(self, name: str) -> IAssociation: # System.UserRoles
        m = module.ensure_module(self.model, name.split('.')[0])
        a = name.split('.')[1]
        # https://github.com/mendix/ExtensionAPI-Samples/blob/7f7625c81d0e15664ad8bc0a3a4433e4f6223b93/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Services/IDomainModelService/GetAllAssociations.md  
        entityAssociations = self.domainModelService.GetAllAssociations(self.model, m)
        association = next((ea.Association for ea in entityAssociations
                  if ea.Association.Name == a), None)
        # f"{m.Name}.{a}")

        return association

    def get_entity(self, name: str) -> IEntity:
        obj = self.model.ToQualifiedName[IEntity](name).Resolve()
        if not obj:
            raise ValueError(f"Entity not found: {name}")
        return obj

    def get_attribute(self, entity: IEntity, attr_name: str) -> IAttribute:
        # 参考代码逻辑：遍历查找
        found = next((a for a in entity.GetAttributes() if a.Name == attr_name), None)
        if not found:
            raise ValueError(f"Attribute '{attr_name}' not found in '{entity.Name}'")
        return found


# ==========================================
# PART 3: Activity Handlers (Scalable)
# ==========================================

# 定义 Handler 函数签名: (context, activity_dto) -> List[IActionActivity]
# 返回 List 是为了处理 "One DTO -> Multiple SDK Activities" 的情况 (如 Change)
HandlerFunc = Callable[[BuilderContext, Any], List[IActionActivity]]


class ActivityDispatcher:
    """策略分发器：将 DTO 类型映射到具体的构建函数"""

    def __init__(self):
        self._handlers: Dict[str, HandlerFunc] = {}
        self._register_defaults()

    def register(self, key: str, handler: HandlerFunc):
        self._handlers[key] = handler

    def dispatch(
        self, ctx: BuilderContext, activity_dto: BaseActivity
    ) -> List[IActionActivity]:
        handler = self._handlers.get(activity_dto.activity_type)
        if not handler:
            raise NotImplementedError(
                f"No handler registered for activity type: {activity_dto.activity_type}"
            )
        return handler(ctx, activity_dto)

    def _register_defaults(self):
        # 在这里注册所有已实现的处理器
        self.register("Retrieve", self._handle_retrieve)
        self.register("Change", self._handle_change)
        self.register("Commit", self._handle_commit)
        # 扩展点：在此行下方添加 self.register("AggregateList", self._handle_aggregate)

    # --- Individual Handlers (Isolated Logic) ---

    def _handle_retrieve(
        self, ctx: BuilderContext, act: RetrieveActivity
    ) -> List[IActionActivity]:
        assoc = ctx.utils.get_association(act.association_name)

        # Strict adherence to Reference Code Service
        sdk_act = (
            # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Services/IMicroflowActivitiesService/CreateAssociationRetrieveSourceActivity.md
            ctx.ctx.microflowActivitiesService.CreateAssociationRetrieveSourceActivity(
                ctx.app, assoc, act.output_variable, act.source_variable
            )
        )
        return [sdk_act]

    def _handle_commit(
        self, ctx: BuilderContext, act: CommitActivity
    ) -> List[IActionActivity]:
        sdk_act = ctx.ctx.microflowActivitiesService.CreateCommitObjectActivity(
            ctx.app, act.variable_name, act.refresh_client, False
        )
        return [sdk_act]

    def _handle_change(
        self, ctx: BuilderContext, act: ChangeActivity
    ) -> List[IActionActivity]:
        # Logic: Convert 1 DTO into N Activities (because the Service handles 1 attr at a time)
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

            # Use Service from Reference Code
            sdk_act = ctx.ctx.microflowActivitiesService.CreateChangeAttributeActivity(
                ctx.app,
                attr,
                ChangeActionItemType.Set,
                val_expr,
                act.variable_name,
                commit_enum,
            )
            result_acts.append(sdk_act)

        return result_acts


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
        self.logs: List[str] = []  # Added for debugging

    def log(self, msg: str):
        """Helper to record internal logs"""
        self.logs.append(f"[Builder-{self.req.full_path}] {msg}")

    def _create_data_type(self, type_info: type_microflow.DataTypeDefinition) -> Optional[DataType]:
        type_name = type_info.type_name.lower()

        if type_name == "string":
            return DataType.String
        if type_name == "integer":
            return DataType.Integer
        if type_name == "long":
            return DataType.Long
        if type_name == "decimal":
            return DataType.Decimal
        if type_name == "boolean":
            return DataType.Boolean
        if type_name == "datetime":
            return DataType.DateTime
        if type_name == "binary":
            return DataType.Binary
        if type_name == "void":
            return DataType.Void
        if type_name == "object":
            return DataType.Object(self.ctx.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "list":
            return DataType.List(self.ctx.app.ToQualifiedName[IEntity](type_info.qualified_name))
        if type_name == "enumeration":
            return DataType.Enumeration(self.ctx.app.ToQualifiedName[IEnumeration](type_info.qualified_name))
        raise ValueError(f"不支持的数据类型 '{type_name}'。")

    def build(self):
        """Orchestrates the creation of the Microflow"""
        # 1. Shell (Header/Params)
        self.log("Starting build process...")
        try:
            self.mf = self._build_shell()
            self.log(f"Shell created/found: {self.mf.Name}")
        except Exception as e:
            self.log(f"Error building shell: {e}")
            raise

        # 2. Body (Activities)
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

        # 1. 准备参数和返回类型
        params = [
            ValueTuple.Create[String, DataType](p.name, self._create_data_type(p.type))
            for p in self.req.parameters
        ]
        return_type = self._create_data_type(self.req.return_type)

        # 2. 查找或创建
        existing = next(
            (m for m in self.ctx.folder.GetDocuments() if m.Name == mf_name), None
        )

        if existing:
            self.mf = self.ctx.app.ToQualifiedName[IMicroflow](
                f"{module_name}.{mf_name}"
            ).Resolve()
            self.mf.ReturnType = return_type
            # FIX: return exp lost
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
                    (
                        self.ctx.ctx.microflowExpressionService.CreateFromString(
                            "empty"
                        )
                        if self.req.return_type.type_name == "Void"
                        else self.ctx.ctx.microflowExpressionService.CreateFromString(
                            "empty"
                        )
                    ),
                )

            self.mf = self.ctx.ctx.microflowService.CreateMicroflow(
                self.ctx.app, self.ctx.folder, mf_name, ret_val, params
            )

        return self.mf

    def _build_body(self):
        self.log(f"Building body with {len(self.req.activities) if self.req.activities else 0} DTO activities.")
        if not self.req.activities:
            return

        # Container for all generated SDK activities
        all_sdk_activities: List[IActionActivity] = []

        # Loop through DTOs -> Delegate to Dispatcher -> Collect SDK Objects
        for i, act_dto in enumerate(self.req.activities):
            try:
                self.log(f"Dispatching Activity [{i}] Type: {act_dto.activity_type}")
                generated_acts = _dispatcher.dispatch(self.ctx, act_dto)
                self.log(f"  -> Generated {len(generated_acts)} SDK items.")
                all_sdk_activities.extend(generated_acts)
            except Exception as e:
                self.log(f"  -> ERROR in dispatch: {str(e)}")
                raise

        # Insertion Strategy (Reverse order for 'TryInsertAfterStart' based on RefCode)
        if all_sdk_activities:
            try:
                count = len(all_sdk_activities)
                self.log(f"Converting {count} activities to C# Array (Reversed).")
                csharp_array = Array[IActionActivity](all_sdk_activities[::-1])
                
                self.log("Calling TryInsertAfterStart...")
                is_inserted = self.ctx.ctx.microflowService.TryInsertAfterStart(self.mf, csharp_array)
                self.log(f"TryInsertAfterStart returned: {is_inserted}")
                
                if not is_inserted:
                    self.log("WARNING: Activities were NOT inserted. Check SDK logs/constraints.")
            except Exception as e:
                self.log(f"ERROR in TryInsertAfterStart: {str(e)}")
                raise
        else:
            self.log("No SDK activities collected, skipping insertion.")

# --- 4. 主入口 ---


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
    report.append(f"{req.full_path} {folder} {docName} {moduleName}")

    # Context initialization
    build_ctx = BuilderContext(ctx, folder)

    # Build execution
    builder = MicroflowBuilder(build_ctx, req)
    try:
        builder.build()
        report.append(f"Success: {req.full_path}")
    except Exception as e:
        report.append(f"Failed to build {req.full_path}: {e}")
        # 即使报错，也先把已有的 builder 日志打出来
    finally:
        # 将 builder 内部收集的详细日志合并到主报告中
        if builder.logs:
            report.append("--- Builder Logs ---")
            report.extend(builder.logs)
            report.append("--------------------")
