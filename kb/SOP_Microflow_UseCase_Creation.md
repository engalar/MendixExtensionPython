# SOP: 创建微流用例 (Microflow Use Case Creation)

## 1. 目标 (Objective)
本SOP旨在规范化创建微流用例（特别是封装Java Action）的流程，确保高效、准确地生成可用的微流框架。

## 2. 分析与发现 (Analysis & Discovery)
在创建微流之前，必须先了解其上下文和依赖。

### 2.1 分析核心逻辑 (如Java Action)
如果微流旨在调用一个Java Action，首先要明确其接口契约。
- **工具**: `mcp__remote_studiopro__generate_java_action_dsl`
- **目的**: 获取Java Action的完整签名，包括：
  - **输入参数**: 准确的参数名称和数据类型。
  - **返回值**: 了解返回的数据类型。

### 2.2 分析数据模型
了解与微流交互的实体是至关重要的。
- **工具**: `mcp__remote_studiopro__generate_domain_model_dsl`
- **目的**: 查看相关实体的属性和关联，确保微流的参数和后续活动能正确地读取和修改它们。

## 3. 设计与规划 (Design & Planning)
根据分析结果，规划微流的结构。

### 3.1 定义微流签名
- **名称**: 遵循项目命名规范，例如 `ACT_` 前缀表示功能性微流。
- **参数**: 定义清晰的输入参数，通常是操作的主要实体对象。
- **返回值**: 确定微流的返回类型 (`Void`, `String`, `Boolean`, 或某个实体/实体列表)。

### 3.2 规划活动流程
- **逻辑顺序**: 设计活动（Activities）的执行顺序。
- **数据流**: 规划数据如何在变量、参数和活动之间流转。
- **配置**: 检查是否需要使用常量（Constants）来管理API密钥、URL等配置项。
- **手动步骤**: 明确哪些部分可以自动生成，哪些必须手动添加（例如 `Call Java Action` 活动）。

## 4. 自动化实施 (Automated Implementation)
使用 `mcp__remote_studiopro__ensure_microflows` 工具生成微流框架。

### 4.1 构建请求负载
构造 `requests` JSON对象时，请参考 `kb/Mendix_Microflow_Creation_Guide.md` 文档。
- `FullPath`: 使用 `ModuleName/MicroflowName` 格式。
- `Parameters`: 定义参数列表，确保类型与实体匹配。
- `ReturnType` / `ReturnExp`: 定义返回值。
- `Activities`: 按顺序定义活动列表。
  - 使用 `Change` 活动来修改对象属性。
  - 使用 `Commit` 活动来持久化更改。
  - **最佳实践**: 为需要手动填入的变量预留占位符，例如: `ValueExpression: "'placeholder_for_manual_step'"`。

### 4.2 错误处理
- 如果工具返回内部错误（例如我们之前遇到的实体类型推断失败），尝试提供更明确的信息来帮助工具。
- **示例**: 在 `Change` 活动中显式添加 `EntityName` 字段，以指定正在操作的实体类型。

## 5. 手动补全与验证 (Manual Completion & Verification)
由于工具的限制，部分复杂活动需要手动添加。

### 5.1 打开微流
- **工具**: `mcp__remote_studiopro__open_document`
- **目的**: 任务完成后，在Studio Pro中为用户打开新创建的微流，方便后续操作。

### 5.2 添加缺失活动
- 在Studio Pro中，拖入 `Call Java Action` 等无法自动生成的活动。
- **配置参数**: 将活动的输入参数映射到微流的变量或参数。
- **定义输出**: 为活动定义一个清晰的输出变量名。

### 5.3 连接逻辑
- 将手动添加活动的输出（如 `UploadedFileUri` 变量）连接到后续自动化生成的活动中。
- **示例**: 修改 `Change` 活动，将其中的占位符值替换为上一步中定义的输出变量。

### 5.4 验证
- 在Studio Pro中，检查整个微流的逻辑流是否完整、参数映射是否正确。
- 确保没有错误或警告。
