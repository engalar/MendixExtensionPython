# Mendix Python Extension

This project provides Python extensions for Mendix Studio Pro, allowing developers to interact with the IDE through Python scripts. It implements the MCP server to communicate with the Mendix Studio Pro extension API.

## Features

- Read and modify document content within Mendix Studio Pro
- Listen for document changes with event-driven architecture
- Extend Mendix Studio Pro functionality using Python
- MCP (Modular Command Protocol) based communication

## Installation

1. Install the [extension mcp server](https://marketplace.mendix.com/link/component/244441) from the Mendix Marketplace
2. [Optional(if you want to develop)] Install the [StudioPro Python Extension](https://marketplace.mendix.com/link/component/244625)
3. Install the required Python package:
   ```bash
   pip install pymx
   ```

## Development

For development setup, refer to [DEVELOPMENT.md](DEVELOPMENT.md):

1. Install Python 3.11 or higher
2. Install required dependencies:
   ```bash
   pip install -e .
   ```
3. For development, also install dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Project Structure

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

## Usage

For detailed usage instructions, see the following resources:

- [YouTube tutorial](https://www.youtube.com/watch?v=JHl0or4aRYU)
- [Bilibili tutorial](https://www.bilibili.com/video/BV1GNtJzfE3W)

## Adding New Tools

To add a new tool to the MCP server:

1. Create a new Python file in the `mxpy/mcp/tools/` directory (e.g., `mendix_yourtool.py`)
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

## Documentation

Use [kb.md](kb.md) as knowledge base for development.

Agent prompt: '用工具创建模型' (Use tools to create models)

## Contributing

Please read [DEVELOPMENT.md](DEVELOPMENT.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.