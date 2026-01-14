# This script is for the execute_python tool in Mendix Studio Pro.
# You can copy and paste the function body below into the tool to execute it.

def query_google_genai_java_actions():
    """
    Analyzes all 'JavaAction' in the 'GoogleGenai' module and extracts their parameters and return types.
    Returns the result in JSON format.
    """
    import json

    def get_type_as_string(type_obj):
        """Converts a type object from the Untyped API to a readable string."""
        if not type_obj:
            return "Void"
        try:
            # Prioritize handling entity types and list types
            type_name_raw = str(type_obj.Type) if hasattr(type_obj, 'Type') else str(type(type_obj).__name__)

            if "EntityType" in type_name_raw:
                 entity_prop = type_obj.GetProperty("entity")
                 if entity_prop and entity_prop.Value:
                     return f"Object({entity_prop.Value.QualifiedName})"
            elif "ListType" in type_name_raw:
                 entity_prop = type_obj.GetProperty("entity")
                 if entity_prop and entity_prop.Value:
                     return f"List({entity_prop.Value.QualifiedName})"

        except:
            pass

        # Handle basic data types
        type_name = str(type_obj.Type) if hasattr(type_obj, 'Type') else str(type(type_obj).__name__)
        return type_name.split('.')[-1].replace("DataType", "")

    # --- Main logic starts ---
    try:
        from pymx.mcp import mendix_context as ctx

        results = []
        current_app = ctx.CurrentApp
        untyped_model = ctx.untypedModelAccessService.GetUntypedModel(current_app)

        module_name = 'GoogleGenai'
        modules = untyped_model.GetUnitsOfType("Projects$Module")

        # Robustness fix: Ensure the Name property exists before accessing .Value
        module = next((m for m in modules if m.Name == module_name), None)
        if not module:
            return json.dumps({"error": f"Module '{module_name}' not found."}, indent=2)

        java_actions = list(module.GetUnitsOfType("JavaActions$JavaAction"))
        if not java_actions:
            return json.dumps({"info": f"No JavaAction found in module '{module_name}'."}, indent=2)

        for action in java_actions:
            action_name_prop = action.GetProperty("name")
            if not action_name_prop: continue

            action_name = action_name_prop.Value

            return_type_prop = action.GetProperty("returnType")
            return_type_obj = return_type_prop.Value if return_type_prop else None

            action_info = {
                "name": action_name,
                "parameters": [],
                "return_type": get_type_as_string(return_type_obj)
            }

            params_prop = action.GetProperty("parameters")
            if params_prop and params_prop.IsList:
                for param in params_prop.GetValues():
                    param_name_prop = param.GetProperty("name")
                    param_type_prop = param.GetProperty("type")
                    if not (param_name_prop and param_type_prop and param_type_prop.Value): continue

                    param_name = param_name_prop.Value
                    param_type_obj = param_type_prop.Value
                    action_info["parameters"].append({"name": param_name, "type": get_type_as_string(param_type_obj)})

            results.append(action_info)

        return json.dumps(results, indent=2, ensure_ascii=False)

    except Exception as e:
        # Import the traceback module to get more detailed error information
        import traceback
        return json.dumps({
            "critical_error": f"An unexpected error occurred while executing the script: {e}",
            "traceback": traceback.format_exc()
        }, indent=2, ensure_ascii=False)

# The `execute_python` tool looks for a local variable named 'result' as the return value
result = query_google_genai_java_actions()
