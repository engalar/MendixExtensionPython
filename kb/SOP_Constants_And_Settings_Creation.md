# SOP: 创建和配置应用常量 (Constants & Settings)

## 1. 核心理念与流程
Mendix中的配置管理是一个两步过程，旨在将配置的**定义**与其在不同环境中的**值**分离开来。

1.  **定义常量 (Define the Constant)**: 在模块中创建一个常量的“蓝图”。这仅仅是声明“存在这样一个配置项”，并定义它的名称和数据类型。
2.  **赋值 (Assign the Value)**: 在应用的设置（Settings）中，为这个常量在特定配置下（如`Default`、`Production`）赋予一个具体的运行时值。

这个流程确保了模型的可移植性，因为具体的值（如生产环境的API密钥）不会被硬编码在模型本身。

## 2. 步骤一：创建常量定义
这是创建常量的第一步。

- **工具**: `mcp__remote_studiopro__create_constants`
- **目的**: 在指定的模块中创建常量的定义。
- **关键参数**:
  - `FullPath`: 常量的完整路径，格式为 `ModuleName/FolderName/ConstantName`。推荐的做法是将其放在模块下的 `Constants` 文件夹中，例如 `MyModule/Constants/MyConstant`。
  - `DataType`: 常量的数据类型 (`String`, `Integer`, `Boolean` 等)。
  - `DefaultValue`: 在模型中为该常量设置的默认值。**注意**：这不一定是最终的运行时值。
  - `ExposedToClient`: 是否允许在客户端代码中访问此常量。

**示例**:
```json
{
  "requests": [
    {
      "FullPath": "GoogleGenai/Constants/ProxyHost",
      "DataType": "String",
      "DefaultValue": "",
      "ExposedToClient": false
    }
  ]
}
```

## 3. 步骤二：在应用设置中赋值
这一步为常量赋予了在特定配置下的实际运行时值。

- **工具**: `mcp__remote_studiopro__ensure_settings`
- **目的**: 在一个指定的配置（Configuration）中，为已定义的常量设置值。
- **关键参数**:
  - `Name`: 配置的名称，通常是 `Default`。
  - `Constants`: 一个列表，包含要设置值的常量。
    - `QualifiedName`: 常量的完全限定名，格式为 `ModuleName.ConstantName`。
    - `Value`: 要为该常量设置的具体值。

**示例**:
```json
{
  "data": {
    "Name": "Default",
    "Constants": [
      {
        "QualifiedName": "GoogleGenai.ProxyHost",
        "Value": "proxy.example.com"
      },
      {
        "QualifiedName": "GoogleGenai.ProxyPort",
        "Value": "8080"
      }
    ]
  }
}
```

## 4. 总结与最佳实践
- **先定义，后赋值**: 始终严格遵循这两个步骤。如果一个常量没有在设置中赋值，它将在运行时使用其在模型中定义的默认值。
- **环境分离**: 充分利用不同的配置（例如，通过Studio Pro手动创建`Test`、`Production`配置）来管理不同环境下的常量值，这是Mendix配置管理的最佳实践。
- **命名规范**: 在`FullPath`中使用`/`，在`QualifiedName`中使用`.`。
