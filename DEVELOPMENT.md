# Mendix Python Extension Development Guide

## Project Overview

This project provides Python extensions for Mendix Studio Pro, allowing developers to interact with the IDE through Python scripts. It implements the MCP (Modular Command Protocol) server to communicate with the Mendix Studio Pro extension API.

## Project Structure

```
mxpy/
├── context.py              # Global context access
├── document.py             # Document object model for content read/write and listening
├── ide/                    # IDE interaction core logic
├── mcp/                    # MCP server implementation
│   ├── main.py             # Main entry point called by C#
│   ├── server.py           # Core server setup and running logic
│   ├── mendix_context.py   # Storage for global Mendix service objects from C#
│   ├── tool_registry.py    # Shared MCP instance and tool registration logic
│   └── tools/              # Individual tool implementations
│       ├── __init__.py     # Auto-discovery and registration of tools
│       └── *.py            # Individual tool files (e.g., mendix_constant.py)
└── model/                  # Data models and business logic
```

## Development Setup

1. Install Python 3.11 or higher
2. Install required dependencies:
   ```bash
   pip install -e .
   ```
3. For development, also install dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Adding New Tools

To add a new tool to the MCP server:

1. Create a new Python file in [mxpy/mcp/tools/](file:///d:/gh/MendixExtensionPython/mxpy/mcp/tools) directory (e.g., `mendix_yourtool.py`)
2. Import the shared MCP instance:
   ```python
   from ..tool_registry import mcp
   ```
3. Define your tool function with the `@mcp.tool()` decorator:
   ```python
   @mcp.tool(name="your_tool_name", description="Tool description")
   async def your_tool_function(parameters):
       # Tool implementation
       return result
   ```
4. The tool will be automatically discovered and registered when the server starts.

## Code Style and Standards

- Follow PEP 8 coding standards
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use relative imports within the package (e.g., `from ..tool_registry import mcp`)

## Testing

Run tests with pytest:
```bash
pytest
```

## Building and Packaging

To build the package:
```bash
python -m build
```

To install in development mode:
```bash
pip install -e .
```

## Architecture Notes

1. **MCP Server**: Based on Starlette and Uvicorn for asynchronous operation
2. **Tool Registration**: Tools are automatically discovered and registered at startup
3. **Context Management**: Mendix services are passed from C# and stored in a global context
4. **Transaction Management**: Use `TransactionManager` for operations that modify the model

## Debugging

To enable more verbose logging, modify the logging configuration in [server.py](file:///d:/gh/MendixExtensionPython/mxpy/mcp/server.py).