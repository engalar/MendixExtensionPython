"""
DSL Generators for Mendix model elements.

This module provides read-only generators that produce human-readable
DSL representations of Mendix models (entities, microflows, pages, workflows).

All functions are synchronous and do NOT use TransactionManager.
"""

import clr
from typing import Optional, List, Set, Dict, Any
from collections import defaultdict

# Import DTOs
from pymx.model.dto.type_dsl import (
    DSLFormatOptions,
    DomainModelDSLInput,
    MicroflowDSLInput,
    PageDSLInput,
    WorkflowDSLInput,
    ModuleTreeDSLInput
)

# ==========================================
# 1. DomainModel DSL Generator
# ==========================================


class DomainModelAnalyzer:
    """Generates DSL documentation for domain models using Mendix untyped API.

    Key Untyped API Concepts:
    -------------------------
    1. All model elements are accessed via GetUnitsOfType("Module$TypeName")
    2. All properties are accessed via .GetProperty("name").Value
    3. List properties must be checked with .IsList before calling .GetValues()
    4. Object IDs are accessed via .ID.ToString()
    5. Type names use "Module$TypeName" format (e.g., "DomainModels$Entity")

    Example Pattern:
    ---------------
    # Get entities from domain model
    entities_prop = domain_model.GetProperty("entities")
    if entities_prop and entities_prop.IsList:
        entities = list(entities_prop.GetValues())
        for entity in entities:
            name = entity.GetProperty("name").Value
    """

    def __init__(self, app, untyped_module, options: DSLFormatOptions):
        """Initialize analyzer with untyped module object.

        Args:
            app: Mendix application instance
            untyped_module: Module from GetUnitsOfType("Projects$Module")
            options: DSL formatting options
        """
        self.app = app
        self.module = untyped_module  # Untyped module from GetUnitsOfType("Projects$Module")
        self.options = options
        self.lines = []

    def generate(self, entity_names: Optional[List[str]] = None) -> str:
        """Generate complete DSL for domain model using untyped API.

        Process:
        1. Find DomainModel unit using GetUnitsOfType("DomainModels$DomainModel")
        2. Get entities via GetProperty("entities").GetValues()
        3. Build ID mapping for association lookups
        4. Generate documentation for each entity
        5. Generate associations and cross-associations

        Args:
            entity_names: Optional list of specific entity names to process

        Returns:
            DSL string representation of the domain model
        """
        self.lines = [
            f"# Domain Model DSL: {self.module.Name}",
            f"# Generated from module {self.module.Name}",
            ""
        ]

        # Find domain model unit in module
        dm_units = self.module.GetUnitsOfType("DomainModels$DomainModel")
        domain_model = next((dm for dm in dm_units), None)

        if not domain_model:
            return f"Error: Module '{self.module.Name}' has no domain model."

        # Get entities using untyped API
        entities_prop = domain_model.GetProperty("entities")
        if not entities_prop or not entities_prop.IsList:
            return f"{self.lines[0]}\n{self.lines[1]}\n\nNo entities found."

        entities = list(entities_prop.GetValues())

        # Filter entities if specific names provided
        if entity_names:
            entities = [e for e in entities if e.Name in entity_names]

        if not entities:
            return f"{self.lines[0]}\n{self.lines[1]}\n\nNo entities found."

        # Build ID to qualified name mapping
        # Used for resolving entity references in associations
        id_map = {}
        for ent in entities:
            id_map[ent.ID.ToString()] = f"{self.module.Name}.{ent.Name}"

        # Generate entity documentation
        for entity in entities:
            self._generate_entity(entity, id_map)
            self.lines.append("")  # Blank separator

        # Generate associations section using untyped API
        associations_prop = domain_model.GetProperty("associations")
        if associations_prop and associations_prop.IsList:
            associations = list(associations_prop.GetValues())
            if associations:
                self.lines.append("## Associations (Internal)")
                for assoc in associations:
                    self._generate_association(assoc, id_map)
                self.lines.append("")

        # Generate cross-associations section using untyped API
        cross_assocs_prop = domain_model.GetProperty("crossAssociations")
        if cross_assocs_prop and cross_assocs_prop.IsList:
            cross_associations = list(cross_assocs_prop.GetValues())
            if cross_associations:
                self.lines.append("## Associations (Cross-Module)")
                for assoc in cross_associations:
                    self._generate_cross_association(assoc, id_map)
                self.lines.append("")

        return "\n".join(self.lines)

    def _generate_entity(self, entity, id_map: Dict[str, str]):
        """Generate DSL for single entity using untyped API"""
        # Check persistability
        is_persistable = self._check_is_persistable(entity)

        p_tag = " [Persistable]" if is_persistable else " [Non-Persistable]"
        gen_info = self._get_generalization_info(entity)

        # Get entity name
        name_prop = entity.GetProperty("name")
        entity_name = name_prop.Value if name_prop else "Unknown"

        self.lines.append(f"## Entity: {entity_name}{p_tag}{gen_info}")

        # Get documentation
        doc_prop = entity.GetProperty("documentation")
        if self.options.include_documentation and doc_prop and doc_prop.Value:
            self.lines.append(f"> {doc_prop.Value}")

        # Get location
        if self.options.include_location:
            loc_prop = entity.GetProperty("location")
            if loc_prop and loc_prop.Value:
                loc = loc_prop.Value
                self.lines.append(f"> Position: ({loc.X}, {loc.Y})")

        # Get attributes using untyped API
        attrs_prop = entity.GetProperty("attributes")
        if attrs_prop and attrs_prop.IsList:
            for attr in attrs_prop.GetValues():
                self._generate_attribute(attr)

        # Get event handlers using untyped API
        handlers_prop = entity.GetProperty("eventHandlers")
        if handlers_prop and handlers_prop.IsList and self.options.detail_level == "detailed":
            event_handlers = list(handlers_prop.GetValues())
            if event_handlers:
                self.lines.append("\n**Event Handlers:**")
                for handler in event_handlers:
                    # Get event type
                    event_prop = handler.GetProperty("event") if hasattr(handler, "GetProperty") else None
                    event_str = str(event_prop.Value).split(".")[-1] if event_prop and event_prop.Value else "Unknown"

                    # Get microflow name
                    mf_prop = handler.GetProperty("microflow") if hasattr(handler, "GetProperty") else None
                    mf_name = mf_prop.Value if mf_prop and mf_prop.Value else "None"
                    self.lines.append(f"  - {event_str}: {mf_name}")

    def _check_is_persistable(self, entity) -> bool:
        """Check if entity is persistable, considering generalization"""
        try:
            gen_prop = entity.GetProperty("generalization")
            if not gen_prop or not gen_prop.Value:
                return True  # No generalization = persistable by default

            gen = gen_prop.Value

            # Check for IGeneralization (has parent)
            if hasattr(gen, "GetProperty"):
                parent_qname_prop = gen.GetProperty("generalization")
                if parent_qname_prop and parent_qname_prop.Value:
                    # Has parent entity
                    # For untyped API, we can't easily resolve parent entities recursively
                    # Conservatively return True (parent entities typically persistable)
                    return True

                # Check for INoGeneralization.persistable
                persistable_prop = gen.GetProperty("persistable")
                if persistable_prop and persistable_prop.Value is not None:
                    return persistable_prop.Value

            return True  # Default to persistable
        except:
            return True

    def _get_generalization_info(self, entity) -> str:
        """Get generalization (inheritance) information using untyped API"""
        try:
            gen_prop = entity.GetProperty("generalization")
            if not gen_prop or not gen_prop.Value:
                return ""

            gen = gen_prop.Value
            if hasattr(gen, "GetProperty"):
                parent_qname_prop = gen.GetProperty("generalization")
                if parent_qname_prop and parent_qname_prop.Value:
                    return f" extends {parent_qname_prop.Value}"
            return ""
        except:
            return ""

    def _generate_attribute(self, attr):
        """Generate attribute DSL using untyped API"""
        type_name = self._get_attribute_type_string(attr)

        # Get attribute name
        name_prop = attr.GetProperty("name")
        attr_name = name_prop.Value if name_prop else "Unknown"

        # Get documentation
        doc_prop = attr.GetProperty("documentation")
        doc = f" // {doc_prop.Value}" if (self.options.include_documentation and doc_prop and doc_prop.Value) else ""

        self.lines.append(f"- {attr_name}: {type_name}{doc}")

        if self.options.detail_level == "detailed":
            # Add default value if present
            try:
                value_prop = attr.GetProperty("value")
                if value_prop and value_prop.Value:
                    default_val_prop = value_prop.Value.GetProperty("defaultValue") if hasattr(value_prop.Value, "GetProperty") else None
                    if default_val_prop and default_val_prop.Value:
                        self.lines.append(f"  Default: {default_val_prop.Value}")
            except:
                pass

    def _get_attribute_type_string(self, attr) -> str:
        """Get human-readable attribute type using untyped API.

        Untyped API Pattern:
        - All property access uses .GetProperty("name").Value
        - Always check if property exists before accessing .Value
        - Handle None values gracefully
        """
        try:
            type_prop = attr.GetProperty("type")
            if not type_prop or not type_prop.Value:
                return "Unknown"

            attr_type = type_prop.Value
            type_name = attr_type.Type if hasattr(attr_type, "Type") else type(attr_type).__name__

            if "StringAttributeType" in type_name:
                # Get length property - might be None or non-integer
                length_prop = attr_type.GetProperty("length") if hasattr(attr_type, "GetProperty") else None
                length = length_prop.Value if length_prop and length_prop.Value is not None else 0
                # Ensure length is an integer
                try:
                    length = int(length) if length else 0
                except (ValueError, TypeError):
                    length = 0
                return f"String({length if length > 0 else 'Unlimited'})"
            elif "IntegerAttributeType" in type_name:
                return "Integer"
            elif "LongAttributeType" in type_name:
                return "Long"
            elif "DecimalAttributeType" in type_name:
                return "Decimal"
            elif "BooleanAttributeType" in type_name:
                return "Boolean"
            elif "DateTimeAttributeType" in type_name:
                return "DateTime"
            elif "AutoNumberAttributeType" in type_name:
                return "AutoNumber"
            elif "EnumerationAttributeType" in type_name:
                enum_prop = attr_type.GetProperty("enumeration") if hasattr(attr_type, "GetProperty") else None
                enum_name = enum_prop.Value if enum_prop and enum_prop.Value else "?"
                return f"Enum({enum_name})"
            elif "BinaryAttributeType" in type_name:
                return "Binary"
            elif "HashedStringAttributeType" in type_name:
                return "HashString"
            else:
                return type_name
        except Exception:
            return "Unknown"

    def _generate_association(self, association, id_map: Dict[str, str]):
        """Generate association DSL using untyped API"""
        # Get parent and child via properties
        parent_id_prop = association.GetProperty("parent") if hasattr(association, "GetProperty") else None
        child_id_prop = association.GetProperty("child") if hasattr(association, "GetProperty") else None

        parent_id = str(parent_id_prop.Value.ID) if parent_id_prop and parent_id_prop.Value and hasattr(parent_id_prop.Value, "ID") else "Unknown"
        child_id = str(child_id_prop.Value.ID) if child_id_prop and child_id_prop.Value and hasattr(child_id_prop.Value, "ID") else "Unknown"

        parent_name = id_map.get(parent_id, "Unknown")
        child_name = id_map.get(child_id, "Unknown")

        # Simplify names (remove module prefix)
        parent_short = parent_name.split(".")[-1] if "." in parent_name else parent_name
        child_short = child_name.split(".")[-1] if "." in child_name else child_name

        # Get association name
        name_prop = association.GetProperty("name")
        assoc_name = name_prop.Value if name_prop else "Unknown"

        # Get owner and type
        owner_prop = association.GetProperty("owner")
        owner = str(owner_prop.Value).split(".")[-1] if owner_prop and owner_prop.Value else "Unknown"

        type_prop = association.GetProperty("type")
        assoc_type = str(type_prop.Value).split(".")[-1] if type_prop and type_prop.Value else "Unknown"

        self.lines.append(f"- [Assoc] {assoc_name}: {parent_short} -> {child_short} [Type:{assoc_type}, Owner:{owner}]")

    def _generate_cross_association(self, association, id_map: Dict[str, str]):
        """Generate cross-association DSL using untyped API"""
        # Get parent via properties
        parent_id_prop = association.GetProperty("parent") if hasattr(association, "GetProperty") else None
        parent_id = str(parent_id_prop.Value.ID) if parent_id_prop and parent_id_prop.Value and hasattr(parent_id_prop.Value, "ID") else "Unknown"

        parent_name = id_map.get(parent_id, "Unknown")
        parent_short = parent_name.split(".")[-1] if "." in parent_name else parent_name

        # Get child - for cross associations, child might be a qualified name string
        child_prop = association.GetProperty("child") if hasattr(association, "GetProperty") else None
        if child_prop and child_prop.Value:
            child_name = str(child_prop.Value)
        else:
            child_name = "Unknown"

        # Get association name
        name_prop = association.GetProperty("name")
        assoc_name = name_prop.Value if name_prop else "Unknown"

        # Get owner and type
        owner_prop = association.GetProperty("owner")
        owner = str(owner_prop.Value).split(".")[-1] if owner_prop and owner_prop.Value else "Unknown"

        type_prop = association.GetProperty("type")
        assoc_type = str(type_prop.Value).split(".")[-1] if type_prop and type_prop.Value else "Unknown"

        self.lines.append(f"- [Cross] {assoc_name}: {parent_short} -> {child_name} [Type:{assoc_type}, Owner:{owner}]")


def generate_domain_model_dsl(app, data: DomainModelDSLInput) -> str:
    try:
        from pymx.mcp import mendix_context as ctx
        untypedRoot = ctx.untypedModelAccessService.GetUntypedModel(app)
        # Find module
        modules = untypedRoot.GetUnitsOfType("Projects$Module")
        module = next((m for m in modules if m.Name == data.module_name), None)

        if not module:
            return f"Error: Module '{data.module_name}' not found."

        analyzer = DomainModelAnalyzer(app, module, data.format_options)
        return analyzer.generate(data.entity_names)
    except Exception as e:
        import traceback
        return f"Error generating domain model DSL: {e}\n{traceback.format_exc()}"


# ==========================================
# 2. Microflow DSL Generator
# ==========================================


class MicroflowAnalyzer:
    """Generates DSL visualization for microflows with ASCII art flow"""

    def __init__(self, app, microflow, options: DSLFormatOptions):
        self.app = app
        self.microflow = microflow
        self.options = options
        self.lines = []

    def generate(self, include_expressions: bool = True) -> str:
        """Generate microflow DSL with activity flow"""

        # Get module name from qualified name
        qname_prop = self.microflow.GetProperty("qualifiedName")
        module_name = qname_prop.Value.Module.Name if qname_prop else "Unknown"
        self.lines = [
            f"# Microflow DSL: {module_name}.{self.microflow.Name}",
            "",
            "```"
        ]

        try:
            # Get all objects using untyped API pattern
            model_prop = self.microflow.GetProperty("model")
            if not model_prop or not model_prop.Value:
                return f"{self.lines[0]}\n```No model found.```"

            model = model_prop.Value
            objects_prop = model.GetProperty("objectCollection")
            if not objects_prop:
                return f"{self.lines[0]}\n```No object collection found.```"

            obj_collection_prop = objects_prop.GetProperty("objects")
            if obj_collection_prop and obj_collection_prop.IsList:
                object_collection = obj_collection_prop.GetValues()
            else:
                object_collection = []

            nodes = {obj.ID.ToString(): obj for obj in object_collection}

            # Build adjacency list for flows using untyped API pattern
            flows_prop = model.GetProperty("flows")
            if not flows_prop or not flows_prop.IsList:
                flows = []
            else:
                flows = list(flows_prop.GetValues())

            adj = defaultdict(list)
            for flow in flows:
                origin_prop = flow.GetProperty("origin")
                destination_prop = flow.GetProperty("destination")
                if origin_prop and destination_prop:
                    origin_id_prop = origin_prop.Value.GetProperty("id") if hasattr(origin_prop.Value, "GetProperty") else None
                    dest_id_prop = destination_prop.Value.GetProperty("id") if hasattr(destination_prop.Value, "GetProperty") else None
                    if origin_id_prop and dest_id_prop:
                        src = str(origin_id_prop.Value)
                        dst = str(dest_id_prop.Value)
                        adj[src].append((flow, dst))

            # Find start node
            start_node = next((obj for obj in nodes.values() if "StartEvent" in type(obj).__name__), None)

            if not start_node:
                return f"{self.lines[0]}\n```No start event found.```"

            # Traverse flow
            visited = set()
            stack = [(start_node.ID.ToString(), 0, "")]

            while stack:
                node_id, indent, flow_label = stack.pop()
                node = nodes.get(node_id)

                if not node:
                    continue

                label_str = f"--({flow_label})--> " if flow_label else ""
                self.lines.append(f"{'  ' * indent}{label_str}{self._get_activity_summary(node, include_expressions)}")

                if node_id in visited:
                    self.lines.append(f"{'  ' * (indent + 1)}(Jump/Loop)")
                    continue
                visited.add(node_id)

                out_flows = adj.get(node_id, [])
                has_branches = len(out_flows) > 1

                for flow, target_id in reversed(out_flows):
                    case_val = ""
                    if has_branches:
                        # Use untyped API pattern to get case/condition value
                        case_prop = flow.GetProperty("case") if hasattr(flow, "GetProperty") else None
                        if case_prop and case_prop.Value:
                            val_prop = case_prop.Value.GetProperty("value") if hasattr(case_prop.Value, "GetProperty") else None
                            case_val = val_prop.Value if val_prop else ""
                        else:
                            condition_prop = flow.GetProperty("condition") if hasattr(flow, "GetProperty") else None
                            if condition_prop and condition_prop.Value:
                                val_prop = condition_prop.Value.GetProperty("value") if hasattr(condition_prop.Value, "GetProperty") else None
                                case_val = val_prop.Value if val_prop else ""

                    new_indent = indent + 1 if has_branches else indent
                    stack.append((target_id, new_indent, case_val))

            self.lines.append("```")
            return "\n".join(self.lines)

        except Exception as e:
            import traceback
            return f"{self.lines[0]}\n```Error generating microflow DSL: {e}\n{traceback.format_exc()}```"

    def _get_prop(self, obj, prop_name: str, default=None):
        """Helper to safely get property value from untyped object"""
        if not obj or not hasattr(obj, "GetProperty"):
            return default
        prop = obj.GetProperty(prop_name)
        return prop.Value if prop else default

    def _get_activity_summary(self, obj, include_expressions: bool) -> str:
        """Get human-readable summary of an activity using untyped API pattern"""
        # Get the Mendix type name (e.g., "Microflows$StartEvent" -> "StartEvent")
        obj_type = obj.Type.split("$")[-1] if hasattr(obj, "Type") else type(obj).__name__

        try:
            if "StartEvent" in obj_type:
                # Get parameters from microflow
                params_prop = self.microflow.GetProperty("parameters")
                if params_prop and params_prop.IsList:
                    params = list(params_prop.GetValues())
                    if params:
                        param_list = []
                        for p in params:
                            p_name = self._get_prop(p, "name", "?")
                            p_type = self._get_prop(p, "type", "?")
                            # Get type name
                            type_obj = p_type
                            if hasattr(type_obj, "Type"):
                                p_type_str = type_obj.Type.split("$")[-1]
                            elif hasattr(type_obj, "FullName"):
                                p_type_str = type_obj.FullName
                            else:
                                p_type_str = str(p_type)
                            param_list.append(f"{p_name}:{p_type_str}")
                        param_str = ", ".join(param_list)
                        return f"Start({param_str})"
                return "Start"

            elif "EndEvent" in obj_type:
                ret = self._get_prop(obj, "returnValue")
                if ret:
                    return f"End (Return: {ret})"
                return "End"

            elif "ActionActivity" in obj_type:
                action = self._get_prop(obj, "action")
                if not action:
                    return "[ActionActivity]"

                action_type = action.Type.split("$")[-1] if hasattr(action, "Type") else type(action).__name__

                if "MicroflowCallAction" in action_type:
                    mf_call = self._get_prop(action, "microflowCall")
                    if mf_call:
                        mf = self._get_prop(mf_call, "microflow")
                        mf_name = mf.FullName if hasattr(mf, "FullName") else self._get_prop(mf, "name", "Unknown")
                    else:
                        mf_name = "Unknown"
                    use_return = self._get_prop(obj, "useReturnVariable", False)
                    output_var = self._get_prop(obj, "outputVariableName", "")
                    out = f" -> ${output_var}" if use_return and output_var else ""
                    return f"Call: {mf_name}{out}"

                elif "CreateVariableAction" in action_type:
                    var_name = self._get_prop(action, "variableName", "")
                    var_type = self._get_prop(action, "variableType", "")
                    val = (self._get_prop(action, "initialValue", "") or "")[:50]
                    return f"Create: ${var_name} ({var_type}) = {val}"

                elif "ChangeVariableAction" in action_type:
                    var_name = self._get_prop(action, "variableName", "")
                    val = (self._get_prop(action, "value", "") or "")[:50]
                    return f"Change: ${var_name} = {val}"

                elif "DeleteObjectAction" in action_type:
                    obj_name = self._get_prop(action, "objectName", "")
                    return f"Delete: ${obj_name}"

                elif "CommitAction" in action_type:
                    obj_name = self._get_prop(action, "objectName", "")
                    return f"Commit: ${obj_name}"

                elif "RollbackAction" in action_type:
                    obj_name = self._get_prop(action, "objectName", "")
                    return f"Rollback: ${obj_name}"

                elif "RetrieveAction" in action_type:
                    source = self._get_prop(action, "retrieveSource")
                    if source:
                        entity = self._get_prop(source, "entity")
                        entity_name = entity.FullName if hasattr(entity, "FullName") else self._get_prop(entity, "name", "Unknown")
                        xpath = self._get_prop(source, "xPath", "")
                        xpath_str = f" [{xpath}]" if xpath and include_expressions else ""
                        output_var = self._get_prop(obj, "outputVariableName", "")
                        return f"Retrieve: {entity_name}{xpath_str} -> ${output_var}"
                    return "Retrieve"

                elif "CreateObjectAction" in action_type:
                    entity = self._get_prop(action, "entity")
                    entity_name = entity.FullName if hasattr(entity, "FullName") else self._get_prop(entity, "name", "Unknown")
                    output_var = self._get_prop(obj, "outputVariableName", "")
                    return f"CreateObject: {entity_name} -> ${output_var}"

                else:
                    return f"[{action_type}]"

            elif "ExclusiveSplit" in obj_type:
                condition = self._get_prop(obj, "splitCondition")
                if condition:
                    expr = self._get_prop(condition, "value", "")
                    caption = self._get_prop(obj, "caption", "")
                    if caption and caption != expr:
                        return f"Decision: {caption} [{expr[:50]}]"
                    return f"Decision: {expr[:50]}"
                return "Decision"

            elif "LoopBreak" in obj_type:
                return "Break"

            elif "LoopContinue" in obj_type:
                return "Continue"

            elif "SequenceFlow" in obj_type:
                return "→"

            elif "Java" in obj_type or "C#" in obj_type:
                return f"[{obj_type}]"

            else:
                return f"[{obj_type}]"

        except Exception as e:
            return f"[{obj_type}: Error: {e}]"


def generate_microflow_dsl(app, data: MicroflowDSLInput) -> str:
    """Generate DSL for microflow"""
    try:
        from pymx.mcp import mendix_context as ctx
        # Parse qualified name
        parts = data.qualified_name.split(".")
        if len(parts) < 2:
            return f"Error: Invalid qualified name '{data.qualified_name}'. Expected format: Module.MicroflowName"

        module_name = parts[0]
        mf_name = parts[-1]

        # Find module using untyped API (like generate_domain_model_dsl)
        untypedRoot = ctx.untypedModelAccessService.GetUntypedModel(app)
        modules = untypedRoot.GetUnitsOfType("Projects$Module")
        module = next((m for m in modules if m.Name == module_name), None)

        if not module:
            return f"Error: Module '{module_name}' not found."

        # Find microflow
        microflows = list(module.GetUnitsOfType("Microflows$Microflow"))
        microflow = next((mf for mf in microflows if mf.Name == mf_name), None)

        if not microflow:
            return f"Error: Microflow '{mf_name}' not found in module '{module_name}'."

        analyzer = MicroflowAnalyzer(app, microflow, data.format_options)
        return analyzer.generate(data.include_expressions)

    except Exception as e:
        import traceback
        return f"Error generating microflow DSL: {e}\n{traceback.format_exc()}"


# ==========================================
# 3. Page DSL Generator
# ==========================================


class PageAnalyzer:
    """Generates DSL for page widget tree structure"""

    def __init__(self, app, page, options: DSLFormatOptions):
        self.app = app
        self.page = page
        self.options = options
        self.lines = []

    def generate(self, include_widget_properties: bool = False) -> str:
        """Generate page widget tree DSL"""
        # Get module name from qualified name using untyped API pattern
        qname_prop = self.page.GetProperty("qualifiedName")
        module_name = qname_prop.Value.Module.Name if qname_prop else "Unknown"
        self.lines = [
            f"# Page DSL: {module_name}.{self.page.Name}",
            ""
        ]

        try:
            # Get layout call using untyped API pattern
            layout_call_prop = self.page.GetProperty("layoutCall")
            if layout_call_prop and layout_call_prop.Value:
                layout_call = layout_call_prop.Value
                arguments_prop = layout_call.GetProperty("arguments")
                if arguments_prop and arguments_prop.IsList:
                    for arg in arguments_prop.GetValues():
                        parameter_prop = arg.GetProperty("parameter")
                        param_name = parameter_prop.Value if parameter_prop else "Unknown"
                        self.lines.append(f"## Placeholder: {param_name}")
                        widgets_prop = arg.GetProperty("widgets")
                        if widgets_prop and widgets_prop.IsList:
                            for widget in widgets_prop.GetValues():
                                self._render_widget(widget, 1, include_widget_properties)
                        self.lines.append("")
            else:
                # No layout call, try to get widgets directly
                self.lines.append("## Widgets:")
                try:
                    widgets_prop = self.page.GetProperty("widgets")
                    if widgets_prop and widgets_prop.IsList:
                        for widget in widgets_prop.GetValues():
                            self._render_widget(widget, 1, include_widget_properties)
                    else:
                        self.lines.append("(No widgets found)")
                except:
                    self.lines.append("(No widgets found or page uses legacy format)")

            return "\n".join(self.lines)

        except Exception as e:
            import traceback
            return f"{self.lines[0]}\n\nError generating page DSL: {e}\n{traceback.format_exc()}"

    def _render_widget(self, widget, indent: int, include_properties: bool):
        """Render widget with indentation using untyped API pattern"""
        # Get widget type from the raw object
        widget_type = widget.Type.split("$")[-1] if hasattr(widget, "Type") else type(widget).__name__

        # Get widget name using untyped API pattern
        name_prop = widget.GetProperty("name") if hasattr(widget, "GetProperty") else None
        widget_name = name_prop.Value if name_prop else ""

        name_str = f" ({widget_name})" if widget_name else ""
        self.lines.append(f"{'  ' * indent}- [{widget_type}]{name_str}")

        if include_properties:
            # Add caption property using untyped API pattern
            caption_prop = widget.GetProperty("caption") if hasattr(widget, "GetProperty") else None
            if caption_prop and caption_prop.Value:
                self.lines.append(f"{'  ' * (indent + 1)}Caption: {caption_prop.Value}")

        # Recursively render child widgets using untyped API pattern
        if hasattr(widget, "GetProperty"):
            widgets_prop = widget.GetProperty("widgets")
            if widgets_prop and widgets_prop.IsList:
                for child in widgets_prop.GetValues():
                    self._render_widget(child, indent + 1, include_properties)
            else:
                # Try rows pattern (for LayoutGrid)
                rows_prop = widget.GetProperty("rows")
                if rows_prop and rows_prop.IsList:
                    for row in rows_prop.GetValues():
                        columns_prop = row.GetProperty("columns")
                        if columns_prop and columns_prop.IsList:
                            for col in columns_prop.GetValues():
                                col_widgets_prop = col.GetProperty("widgets")
                                if col_widgets_prop and col_widgets_prop.IsList:
                                    for child in col_widgets_prop.GetValues():
                                        self._render_widget(child, indent + 1, include_properties)


def generate_page_dsl(app, data: PageDSLInput) -> str:
    """Generate DSL for page"""
    try:
        from pymx.mcp import mendix_context as ctx
        # Parse qualified name
        parts = data.qualified_name.split(".")
        if len(parts) < 2:
            return f"Error: Invalid qualified name '{data.qualified_name}'. Expected format: Module.PageName or Module.Folder.PageName"

        module_name = parts[0]
        page_name = parts[-1]

        # Find module using untyped API (like generate_domain_model_dsl)
        untypedRoot = ctx.untypedModelAccessService.GetUntypedModel(app)
        modules = untypedRoot.GetUnitsOfType("Projects$Module")
        module = next((m for m in modules if m.Name == module_name), None)

        if not module:
            return f"Error: Module '{module_name}' not found."

        # Find page
        pages = list(module.GetUnitsOfType("Pages$Page"))
        page = next((p for p in pages if p.Name == page_name), None)

        if not page:
            return f"Error: Page '{page_name}' not found in module '{module_name}'."

        analyzer = PageAnalyzer(app, page, data.format_options)
        return analyzer.generate(data.include_widget_properties)

    except Exception as e:
        import traceback
        return f"Error generating page DSL: {e}\n{traceback.format_exc()}"


# ==========================================
# 4. Workflow DSL Generator
# ==========================================


class WorkflowAnalyzer:
    """Generates DSL for workflow activity flows (Mendix 9.24+)"""

    def __init__(self, app, workflow, options: DSLFormatOptions):
        self.app = app
        self.workflow = workflow
        self.options = options
        self.lines = []

    def generate(self) -> str:
        """Generate workflow DSL"""
        # Get module name from qualified name using untyped API pattern
        qname_prop = self.workflow.GetProperty("qualifiedName")
        module_name = qname_prop.Value.Module.Name if qname_prop else "Unknown"
        self.lines = [
            f"# Workflow DSL: {module_name}.{self.workflow.Name}",
            ""
        ]

        try:
            # Get workflow flow using untyped API pattern
            flow_prop = self.workflow.GetProperty("flow")
            if flow_prop and flow_prop.Value:
                self.lines.append("```")
                self._render_flow(flow_prop.Value, 0)
                self.lines.append("```")
            else:
                self.lines.append("(No flow found)")

            return "\n".join(self.lines)

        except Exception as e:
            import traceback
            return f"{self.lines[0]}\n```Error generating workflow DSL: {e}\n{traceback.format_exc()}```"

    def _render_flow(self, flow, indent: int):
        """Render workflow flow recursively using untyped API pattern"""
        if not flow:
            return

        # Get activities using untyped API pattern
        activities_prop = flow.GetProperty("activities")
        if not activities_prop or not activities_prop.IsList:
            return

        activities = activities_prop.GetValues()
        for act in activities:
            # Get activity type from the raw object
            act_type = act.Type.split("$")[-1] if hasattr(act, "Type") else type(act).__name__

            # Get properties using untyped API pattern
            caption_prop = act.GetProperty("caption") if hasattr(act, "GetProperty") else None
            caption = caption_prop.Value if caption_prop else ""

            name_prop = act.GetProperty("name") if hasattr(act, "GetProperty") else None
            name = name_prop.Value if name_prop else ""

            caption_str = f" {caption}" if caption else ""
            name_str = f" ({name})" if name else ""

            self.lines.append(f"{'  ' * indent}- [{act_type}]{caption_str}{name_str}")

            # Handle outcomes (branches) using untyped API pattern
            outcomes_prop = act.GetProperty("outcomes") if hasattr(act, "GetProperty") else None
            if outcomes_prop and outcomes_prop.IsList:
                for outcome in outcomes_prop.GetValues():
                    # Get value using untyped API pattern
                    value_prop = outcome.GetProperty("value") if hasattr(outcome, "GetProperty") else None
                    val = value_prop.Value if value_prop else "Outcome"
                    self.lines.append(f"{'  ' * (indent + 1)}└─ Case: {val}")

                    # Recursively render outcome flow using untyped API pattern
                    flow_prop = outcome.GetProperty("flow") if hasattr(outcome, "GetProperty") else None
                    if flow_prop and flow_prop.Value:
                        self._render_flow(flow_prop.Value, indent + 2)


def generate_workflow_dsl(app, data: WorkflowDSLInput) -> str:
    """Generate DSL for workflow"""
    try:
        from pymx.mcp import mendix_context as ctx
        # Parse qualified name
        parts = data.qualified_name.split(".")
        if len(parts) < 2:
            return f"Error: Invalid qualified name '{data.qualified_name}'. Expected format: Module.WorkflowName"

        module_name = parts[0]
        wf_name = parts[-1]

        # Find module using untyped API (like generate_domain_model_dsl)
        untypedRoot = ctx.untypedModelAccessService.GetUntypedModel(app)
        modules = untypedRoot.GetUnitsOfType("Projects$Module")
        module = next((m for m in modules if m.Name == module_name), None)

        if not module:
            return f"Error: Module '{module_name}' not found."

        # Find workflow
        try:
            workflows = list(module.GetUnitsOfType("Workflows$Workflow"))
            workflow = next((wf for wf in workflows if wf.Name == wf_name), None)

            if not workflow:
                return f"Error: Workflow '{wf_name}' not found in module '{module_name}'. Note: Workflows require Mendix 9.24+."
        except Exception:
            return f"Error: Workflows are not supported in this Mendix version (requires 9.24+)."

        analyzer = WorkflowAnalyzer(app, workflow, data.format_options)
        return analyzer.generate()

    except Exception as e:
        import traceback
        return f"Error generating workflow DSL: {e}\n{traceback.format_exc()}"


# ==========================================
# 5. ModuleTree DSL Generator
# ==========================================


class ModuleTreeAnalyzer:
    """Generates DSL for module file/folder structure"""

    def __init__(self, app, module, options: DSLFormatOptions):
        self.app = app
        self.module = module
        self.options = options
        self.lines = []
        self.alias_map = {
            "Microflows$Microflow": "Microflow",
            "Pages$Page": "Page",
            "Workflows$Workflow": "Workflow",
            "Nanoflows$Nanoflow": "Nanoflow",
            "Constants$Constant": "Constant",
            "Enumerations$Enumeration": "Enumeration",
            "Documents$Document": "Document",
            "Images$Image": "Image",
            "Resources$Resource": "Resource",
        }

    def generate(self, include_system_elements: bool = False) -> str:
        """Generate module tree DSL"""
        self.lines = [
            f"# Module Tree DSL: {self.module.Name}",
            "```"
        ]

        try:
            # Start from module root
            self._render_container(self.module, 0, include_system_elements)

            self.lines.append("```")
            return "\n".join(self.lines)

        except Exception as e:
            import traceback
            return f"{self.lines[0]}\n```Error generating module tree DSL: {e}\n{traceback.format_exc()}```"

    def _render_container(self, container, indent: int, include_system: bool):
        """Render container (module or folder) contents using untyped API pattern"""
        try:
            all_units = list(container.GetUnits())
        except:
            all_units = []

        # Track descendant IDs to avoid duplicates
        descendant_ids: Set[str] = set()

        # First, collect all descendant IDs
        for unit in all_units:
            unit_type = unit.Type
            if unit_type == "Projects$Folder":
                self._collect_descendant_ids(unit, descendant_ids)

        # Filter direct units (not descendants of folders) using untyped API pattern
        direct_units = []
        for u in all_units:
            if u.ID.ToString() not in descendant_ids:
                name_prop = u.GetProperty("name") if hasattr(u, "GetProperty") else None
                if name_prop and name_prop.Value:
                    direct_units.append(u)

        # Separate folders from documents
        direct_folders = [u for u in direct_units if u.Type == "Projects$Folder"]
        direct_docs = [u for u in direct_units if u.Type != "Projects$Folder"]

        # Render documents using untyped API pattern
        for doc in sorted(direct_docs, key=lambda x: x.GetProperty("name").Value if hasattr(x, "GetProperty") and x.GetProperty("name") else ""):
            # Filter system elements if needed
            name_prop = doc.GetProperty("name") if hasattr(doc, "GetProperty") else None
            doc_name = name_prop.Value if name_prop else ""
            if not include_system and doc_name.startswith("_"):
                continue

            full_type = doc.Type
            type_label = self.alias_map.get(full_type, full_type.split("$")[-1])
            self.lines.append(f"{'  ' * indent}[{type_label}] {doc_name}")

        # Render folders recursively using untyped API pattern
        for folder in sorted(direct_folders, key=lambda x: x.GetProperty("name").Value if hasattr(x, "GetProperty") and x.GetProperty("name") else ""):
            folder_name_prop = folder.GetProperty("name") if hasattr(folder, "GetProperty") else None
            folder_name = folder_name_prop.Value if folder_name_prop else ""
            self.lines.append(f"{'  ' * indent}[Folder] {folder_name}")
            self._render_container(folder, indent + 1, include_system)

    def _collect_descendant_ids(self, folder, id_set: Set[str]):
        """Recursively collect all descendant unit IDs"""
        try:
            for unit in folder.GetUnits():
                id_set.add(unit.ID.ToString())
                if unit.Type == "Projects$Folder":
                    self._collect_descendant_ids(unit, id_set)
        except:
            pass


def generate_module_tree_dsl(app, data: ModuleTreeDSLInput) -> str:
    """Generate DSL for module file/folder tree"""
    try:
        from pymx.mcp import mendix_context as ctx
        # Find module using untyped API (like generate_domain_model_dsl)
        untypedRoot = ctx.untypedModelAccessService.GetUntypedModel(app)
        modules = untypedRoot.GetUnitsOfType("Projects$Module")
        module = next((m for m in modules if m.Name == data.module_name), None)

        if not module:
            return f"Error: Module '{data.module_name}' not found."

        analyzer = ModuleTreeAnalyzer(app, module, data.format_options)
        return analyzer.generate(data.include_system_elements)

    except Exception as e:
        import traceback
        return f"Error generating module tree DSL: {e}\n{traceback.format_exc()}"
