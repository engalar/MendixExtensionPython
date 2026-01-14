# MCP 工具开发 SOP 指导手册

## 1. 概述 (Overview)

本手册旨在提供在 Mendix 扩展项目中添加新 Model Context Protocol (MCP) 工具的标准操作流程 (SOP)。此过程严格遵循三层架构:
- **DTO 层**: 定义输入和输出数据模型 (Pydantic)。
- **业务逻辑层**: 实现核心功能,不直接与 MCP 交互。
- **工具层**: 暴露 MCP 端点 (`@mcp.tool` 和 `@mcp.resource`),调用业务逻辑层。

## 2. 详细步骤 (Detailed Steps)

### 步骤 2.1: 创建/修改 DTO (Data Transfer Object) 文件
- **文件**: `pymx/model/dto/type_dsl.py` (或类似的 DTO 文件)
- **目的**: 为新工具定义输入数据模型 (Pydantic `BaseModel`)。
- **示例**:
  ```python
  from pydantic import BaseModel, Field
  # ... (其他导入)

  class NewToolInput(BaseModel):
      model_config = {"populate_by_name": True}
      param1: str = Field(..., alias="Param1", description="参数1描述")
      param2: int = Field(0, alias="Param2", description="参数2描述")
      # ... 更多参数
  ```

### 步骤 2.2: 实现业务逻辑层
- **文件**: `pymx/model/dsl.py` (或与工具功能相关的业务逻辑文件)
- **目的**: 包含实现工具核心功能的函数。此函数应接收 DTO 作为输入。
- **关键点**:
  - **`_get_type_as_string`**: 如果涉及复杂类型解析,确保使用或修改此辅助函数以适应需求。
  - **`TransactionManager`**: DSL 生成是只读操作,通常**不使用** `TransactionManager`。
  - **错误处理**: 使用 `try-except` 块捕获异常并返回详细的错误信息。
  - **`@CORE` 锚点**: 在函数上方添加 `@CORE` 标签,例如 `# @CORE:DSL.NewTool - 新工具的核心逻辑`。
- **示例**:
  ```python
  # @CORE:DSL.NewTool - 生成新工具的 DSL.
  def generate_new_tool_dsl(app, data: type_dsl.NewToolInput) -> str:
      try:
          from pymx.mcp import mendix_context as ctx
          # ... (在此实现核心逻辑,例如通过 ctx.untypedModelAccessService 访问 Mendix 模型)
          # 格式化结果为字符串 DSL
          return "Formatted DSL output"
      except Exception as e:
          import traceback
          return f"Error generating DSL: {e}\n{traceback.format_exc()}"
  ```

### 步骤 2.3: 创建工具层端点
- **文件**: `pymx/mcp/tools/mendix_dsl.py` (或工具所在文件)
- **目的**: 注册 MCP 工具和资源端点,使其可通过 MCP 服务器访问。
- **关键点**:
  - **导入**: 导入新的 DTO (`NewToolInput`) 和业务逻辑函数 (`generate_new_tool_dsl`)。
  - **`importlib.reload`**: 确保在开发过程中使用 `importlib.reload()` 来热加载修改。
  - **`@mcp.tool`**: 定义一个异步函数作为 MCP 工具。
  - **`@mcp.resource`**: 定义一个用于 URL 访问的资源。
- **示例**:
  ```python
  # ... (其他导入)
  from pymx.model.dto.type_dsl import (
      # ..., NewToolInput
  )
  # ... (其他工具)

  @mcp.tool(
      name="generate_new_tool_dsl",
      description="新工具的描述"
  )
  async def tool_new_tool_dsl(data: NewToolInput) -> str:
      return dsl.generate_new_tool_dsl(ctx.CurrentApp, data)

  # ... (其他资源)

  @mcp.resource(
      "model://dsl/new_tool/{module_name}.mxnewtool.txt",
      description="新工具的资源描述",
      mime_type="text/plain"
  )
  def resource_new_tool_dsl(module_name: str) -> str:
      data = NewToolInput(ModuleName=module_name)
      return dsl.generate_new_tool_dsl(ctx.CurrentApp, data)
  ```

### 步骤 2.4: 删除临时脚本 (如果适用)
- **文件**: `scripts/test_python_code.py` (或任何临时测试脚本)
- **目的**: 当功能完全集成后,移除不再需要的临时脚本。
- **命令**: `rm scripts/test_python_code.py` (或 `del` for Windows)

## 3. 验证 (Verification)

1.  **启动 MCP 服务器**: 在 Mendix Studio Pro 中启动 MCP 服务。
2.  **调用工具**: 使用 MCP 客户端或测试脚本 (`scripts/test_mcp_studiopro.py`) 调用新的工具,例如:
    ```python
    client.call_tool("generate_new_tool_dsl", {"ModuleName": "MyModule"})
    ```
3.  **访问资源**: 尝试通过 URL 访问新的资源,例如:
    ```
    model://dsl/new_tool/MyModule.mxnewtool.txt
    ```
4.  **检查输出**: 确认输出格式正确,且包含预期的数据和信息。

通过遵循这些步骤,可以确保新 MCP 工具的顺利开发和集成。
