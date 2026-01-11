# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python extension for Mendix Studio Pro that implements an Model Context Protocol (MCP, https://modelcontextprotocol.io/) server to enable Python scripts to interact with the Mendix IDE. It allows developers to programmatically create and modify Mendix models (entities, microflows, pages, etc.) through a Python interface.

## Key Architecture

- **MCP Server**: FastMCP-based server that exposes Mendix functionality as tools
- **C# Integration**: Python code is called from C# via pythonnet bridge
- **Auto-discovery**: Tools are automatically registered from `pymx/mcp/tools/` directory
- **Transaction Management**: All model modifications use `TransactionManager` for atomic operations, only one transaction in same time a.k.a. do not embed it.

## Core Components

- `pymx/mcp/tool_registry.py`: Global MCP instance (FastMCP) - the heart of the MCP server
- `pymx/mcp/mendix_context.py`: Global storage for 26 Mendix service objects passed from C#
- `pymx/mcp/tools/`: Individual MCP tool definitions (auto-discovered)
- `pymx/model/`: Business logic for creating/modifying Mendix models
- `pymx/ide/`: IDE interaction utilities

## Development Commands

```bash
# Install dependencies
pip install -e .

# Install dev dependencies (if needed)
pip install -e ".[dev]"

# Build package
python -m build

# Run tests (no test files currently exist in the project)
pytest
```

## How It Works

### C# to Python Bridge
1. C# extension calls Python via pythonnet
2. C# passes 26 Mendix service objects to Python via `set_mendix_services()`
3. Services are stored in `pymx/mcp/mendix_context.py` as global variables
4. FastMCP server starts and exposes tools via HTTP on port 8680

### Tool Auto-Discovery Pattern
Tools in `pymx/mcp/tools/` are automatically discovered via `pymx/mcp/tools/__init__.py`:
```python
for _, name, _ in pkgutil.iter_modules(__path__):
    importlib.reload(importlib.import_module(f".{name}", __name__))
```

Each tool:
1. Imports shared MCP instance: `from ..tool_registry import mcp`
2. Uses `@mcp.tool()` decorator to register
3. Delegates to business logic in `pymx/model/` layer

### Three-Layer Architecture

**Layer 1: MCP Tools** (`pymx/mcp/tools/`)
- Thin wrapper functions with `@mcp.tool()` decorators
- Handle input validation via Pydantic models
- Delegate to model layer

**Layer 2: Business Logic** (`pymx/model/`)
- Core implementation of Mendix operations
- Use `TransactionManager` for atomic operations
- Access Mendix services via global context

**Layer 3: Mendix Context** (`pymx/mcp/mendix_context.py`)
- Stores 26 Mendix services as global variables
- Accessed via `import pymx.mcp.mendix_context as ctx`

## Adding New Tools

1. Create file in `pymx/mcp/tools/mendix_[toolname].py`
2. Import shared MCP instance:
   ```python
   from ..tool_registry import mcp
   from pymx.mcp import mendix_context as ctx
   ```
3. Define async tool with decorator:
   ```python
   @mcp.tool(name="tool_name", description="description")
   async def tool_function(data: InputModel) -> str:
       return await logic.execute(ctx.CurrentApp, data)
   ```
4. Implement business logic in `pymx/model/[toolname].py`
5. Tool auto-registers when `pymx/mcp/tools/__init__.py` runs

## Mendix Services Access

Access Mendix services through `pymx.mcp.mendix_context`:

**Core Services:**
- `ctx.CurrentApp`: Main Mendix application object
- `ctx.domainModelService`: Domain model operations
- `ctx.entityService`: Entity operations
- `ctx.microflowService`: Microflow operations
- `ctx.moduleService`: Module operations

**Other Services:**
- `messageBoxService`, `extensionFileService`, `microflowActivitiesService`, `microflowExpressionService`, `untypedModelAccessService`, `dockingWindowService`, `backgroundJobService`, `configurationService`, `extensionFeaturesService`, `httpClientService`, `nameValidationService`, `navigationManagerService`, `pageGenerationService`, `appService`, `dialogService`, `findResultsPaneService`, `localRunConfigurationsService`, `notificationPopupService`, `runtimeService`, `selectorDialogService`, `versionControlService`

## Model Creation Pattern

All model modifications follow this pattern:

```python
from pymx.model.util import TransactionManager
from pymx.mcp import mendix_context as ctx

def create_model_elements(app, data):
    with TransactionManager(app, "Transaction Name") as transaction:
        # Check existence before creation
        # Use qualified names (ModuleName.EntityName)
        # Create elements via Mendix services
        # Return detailed status report
```

Key conventions:
1. **Qualified Names**: Use `ModuleName.EntityName` format for references
2. **Existence Checks**: Always check if element exists before creating
3. **Atomic Operations**: Wrap all modifications in `TransactionManager`
4. **Detailed Reports**: Return status strings for debugging

## Common Patterns

### Async Functions
All MCP tools must be async functions (required by FastMCP):
```python
@mcp.tool(name="example", description="...")
async def example_tool(data: InputModel) -> str:
    # Implementation
    return "result"
```

### Pydantic Validation
Use Pydantic models for input validation:
```python
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    name: str = Field(..., alias="Name", description="...")
    type: Literal["String", "Integer"] = Field(..., alias="Type")

    class Config:
        allow_population_by_field_name = True
```

### Error Handling
Return detailed error messages in tool responses:
```python
try:
    # Operation
    return f"Success: Created {name}"
except Exception as e:
    return f"Error: Failed to create {name}: {str(e)}"
```

### User Messages
Use Mendix message box for user-visible messages:
```python
ctx.messageBoxService.ShowInformation("Message")
ctx.messageBoxService.ShowError("Error message")
```

### Python Code Execution
The `execute_python` tool allows running arbitrary Python code within the Studio Pro process:
```python
# Execute Python code via MCP
code = '''
def get_module_count():
    import pymx.mcp.mendix_context as ctx
    modules = ctx.moduleService.GetAllModules()
    return f"Total modules: {len(modules)}"

result = get_module_count()
print("Execution complete")
'''
# This will return captured stdout and the 'result' variable value
```

## Development with Mendix

### Testing the Extension
1. Install "extension mcp server" from [Mendix Marketplace](https://marketplace.mendix.com/link/component/244441)
2. Enable extension development:
   ```powershell
   &"C:\Program Files\Mendix\version\modeler\studiopro.exe" --enable-extension-development "path/to/App.mpr"
   ```
3. Install Python dependencies: `pip install -e .`
4. Open Mendix project
5. Start MCP service via Extensions → StudioProMCP → Start
6. Configure VSCode/Claude Code MCP extension to connect to `http://127.0.0.1:8680/mcp`

### Troubleshooting
- View logs: Help → Open Log File Directory → log.txt
- Python version: Must be 3.11 or higher
- pythonnet: Automatically detects Python, or set `PYTHONNET_PYDLL` environment variable

## Code Organization

- **DTOs**: Pydantic models defined in model files (e.g., `pymx/model/entity.py` has `EntityAttribute`, `EntityAssociation`, etc.)
- **C# Interop**: All files that use Mendix API import via `clr.AddReference("Mendix.StudioPro.ExtensionsAPI")` and `# type: ignore` comments
- **Module Reloading**: Tools use `importlib.reload()` for development hot-reloading
- **Qualified Names**: Mendix uses `ModuleName.ElementName` format for all references
