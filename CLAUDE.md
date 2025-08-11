# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python extension for Mendix Studio Pro that implements an MCP (Modular Command Protocol) server to enable Python scripts to interact with the Mendix IDE. It allows developers to programmatically create and modify Mendix models (entities, microflows, pages, etc.) through a Python interface.

## Key Architecture

- **MCP Server**: FastMCP-based server that exposes Mendix functionality as tools
- **C# Integration**: Python code is called from C# via pythonnet bridge
- **Auto-discovery**: Tools are automatically registered from `pymx/mcp/tools/` directory
- **Transaction Management**: All model modifications use `TransactionManager` for atomic operations

## Core Components

- `pymx/mcp/main.py`: C# entry point, receives Mendix services and starts server
- `pymx/mcp/server.py`: Async server setup using Starlette/Uvicorn
- `pymx/mcp/tool_registry.py`: Global MCP instance and tool registration
- `pymx/mcp/tools/`: Individual MCP tools (auto-discovered)
- `pymx/model/`: Business logic for creating/modifying Mendix models
- `pymx/ide/`: IDE interaction utilities

## Development Commands

```bash
# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Build package
python -m build

# Start MCP server (development)
python -m pymx.mcp.main
```

## Adding New Tools

1. Create new file in `pymx/mcp/tools/mendix_[toolname].py`
2. Import shared MCP instance: `from ..tool_registry import mcp`
3. Define tool with decorator: `@mcp.tool(name="tool_name", description="description")`
4. Tool auto-registers on server restart

## Mendix Services Access

Tools access Mendix services through global context in `pymx.mcp.mendix_context`:
- `ctx.current_app`: Main Mendix application object
- `ctx.domainModelService`: Domain model operations
- `ctx.entityService`: Entity operations
- `ctx.microflowService`: Microflow operations
- And 20+ other services (see `main.py` for full list)

## Model Creation Pattern

All model creation follows this pattern:
1. Use `TransactionManager` for atomic operations
2. Use qualified names (`ModuleName.EntityName`) for references
3. Check existence before creation to avoid duplicates
4. Return detailed status reports for debugging

## Testing with Mendix

1. Install extension from Mendix Marketplace: "extension mcp server"
2. Enable extension development: `studiopro.exe --enable-extension-development "path/to/App.mpr"`
3. Start Python MCP server
4. Configure VSCode MCP extension to connect to server

## Common Patterns

- **Async/await**: All tools must be async functions
- **Pydantic validation**: Use Pydantic models for input validation
- **Error handling**: Return detailed error messages in tool responses
- **Logging**: Use `ctx.messageBoxService.ShowInformation()` for user-visible messages