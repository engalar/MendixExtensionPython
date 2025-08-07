# Mendix Python 扩展

本项目为 Mendix Studio Pro 提供 Python 扩展，允许开发者通过 Python 脚本与 IDE 进行交互。它实现了 MCP 服务器，用于与 Mendix Studio Pro 扩展 API 进行通信。
![扫码参与讨论](wechat.jpg)

## 功能特性

- 读取和修改 Mendix Studio Pro 中的文档内容
- 通过事件驱动架构监听文档变更
- 使用 Python 扩展 Mendix Studio Pro 功能
- 基于 MCP (Modular Command Protocol) 的通信机制

## 安装

1. 从 Mendix 市场安装 [extension mcp server](https://marketplace.mendix.com/link/component/244441)
2. 【可选，如果你需要开发验证】从 Mendix 市场安装 [StudioPro Python Extension](https://marketplace.mendix.com/link/component/244625)
3. 安装所需的 Python 包：
   ```bash
   pip install pymx
   ```

## 开发

开发环境搭建请参考 [DEVELOPMENT.md](DEVELOPMENT.md)：

1. 安装 Python 3.11 或更高版本，正常会自动检测，也可以用环境变量`PYTHONNET_PYDLL`来手动指定
2. 安装所需依赖：
   ```bash
   pip install -e .
   ```
3. 如需开发环境，还需安装开发依赖：
   ```bash
   pip install -e ".[dev]"
   ```

## troubleshooting

Help->Open Log File Directory-> log.txt
复制内容发给开发者定位问题

### 项目结构

```
pymx/
├── context.py              # 全局上下文访问
├── document.py             # 文档对象模型，用于内容读写和监听
├── ide/                    # IDE 交互核心逻辑
├── mcp/                    # MCP 服务器实现
│   ├── main.py             # C# 调用的主入口点
│   ├── server.py           # 核心服务器设置和运行逻辑
│   ├── mendix_context.py   # 存储从 C# 传入的全局 Mendix 服务对象
│   ├── tool_registry.py    # 共享的 MCP 实例和工具注册逻辑
│   └── tools/              # 单个工具实现
│       ├── __init__.py     # 工具的自动发现和注册
│       └── *.py            # 单个工具文件 (例如 mendix_constant.py)
└── model/                  # 数据模型和业务逻辑
```

## 使用方法

详细使用说明请参阅以下资源：

### 资源

- [YouTube 教程](https://www.youtube.com/watch?v=JHl0or4aRYU)
- [哔哩哔哩教程](https://www.bilibili.com/video/BV1GNtJzfE3W)

### 操作过程

- 打开项目(需要开启扩展--enable-extension-development)

```powershell
&"D:\Program Files\Mendix\10.24.1.74050\modeler\studiopro.exe" --enable-extension-development "D:\Users\Wengao.Liu\Mendix\App\App.mpr"
```

- 安装 python 3.11 或更高版本
- 安装依赖包 pip install pymx
- 安装 extension mcp server 扩展
- 启动 MCP 服务
- 配置 vscode mcp
- 使用

## 添加新工具

向 MCP 服务器添加新工具：

1. 在 `pymx/mcp/tools/` 目录下创建新的 Python 文件 (例如 `mendix_yourtool.py`)
2. 导入共享的 MCP 实例：
   ```python
   from ..tool_registry import mcp
   ```
3. 使用 `@mcp.tool()` 装饰器定义工具函数：
   ```python
   @mcp.tool(name="your_tool_name", description="工具描述")
   async def your_tool_function(parameters):
       # 工具实现
       return result
   ```
4. 工具将在服务器启动时自动发现和注册。

## 文档

使用 [kb.md](kb.md) 作为知识库进行开发。

Agent prompt: '用工具创建模型'

## 贡献

请阅读 [DEVELOPMENT.md](DEVELOPMENT.md) 了解我们的行为准则和提交拉取请求的流程。

## 许可证

该项目基于 MIT 许可证授权 - 有关详细信息，请参阅 [LICENSE](LICENSE) 文件。
