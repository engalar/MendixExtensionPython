# AI Agent Instructions for MendixExtensionPython

This project provides Python-based tooling for Mendix development, enabling programmatic interaction with Mendix applications through a Python SDK.

## Core Architecture

The codebase is organized into three main packages:

### 1. Model Package (`pymx/model/`)
- Contains core domain models representing Mendix artifacts:
  - `entity.py` - Domain entities
  - `microflow.py` - Business logic flows  
  - `constant.py` - Configuration constants
  - `enum.py` - Enumerations
  - DTOs in `dto/` handle specialized type definitions

### 2. MCP (Mendix Connection Protocol) Package (`pymx/mcp/`)
- Handles communication with Mendix Studio Pro
- Key components:
  - `server.py` - Main communication server
  - `tool_registry.py` - Registry for available tools/commands
  - `tools/` - Individual tool implementations for Mendix operations
  - `mendix_context.py` - Maintains Studio Pro context

### 3. IDE Integration (`pymx/ide/`)
- Provides editor integration capabilities
- `editor.py` - Core editor interaction functionality

## Key Development Patterns

1. Tool Implementation Pattern
   All Mendix operations follow a consistent pattern in `pymx/mcp/tools/`:
   - One operation per file (e.g., `mendix_entity.py` for entity operations)
   - Each tool implements specific Mendix model modifications
   - Tools use typed models from `pymx/model/` for data validation

2. Data Flow
   - Models define structure (`pymx/model/`)
   - Tools implement operations (`pymx/mcp/tools/`)
   - MCP server handles communication
   - IDE integration provides user interface

## Common Operations

Most Mendix model modifications follow this pattern:
1. Define model structure using appropriate classes from `pymx/model/`
2. Use corresponding tool from `pymx/mcp/tools/` to execute changes
3. Handle communication through MCP server

## Important Notes

- The project uses strongly typed models for Mendix artifacts
- Tools are registered through `tool_registry.py` for discovery
- Communication with Mendix Studio Pro happens through a defined protocol
- Model changes should always use provided tools rather than direct modification

## Integration Points

1. Mendix Studio Pro Connection
   - Handled through MCP server
   - Requires Studio Pro to be running
   - Uses specific protocol for model modifications

2. Editor Integration
   - IDE features implemented in `pymx/ide/`
   - Provides direct editor interaction capabilities