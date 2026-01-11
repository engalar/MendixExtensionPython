# server.py
from fastmcp import FastMCP

# 1. 初始化 FastMCP 服务
mcp = FastMCP("MathServer")

# 2. 定义工具
@mcp.tool()
def add(a: int, b: int) -> int:
    """两数相加"""
    print(f"Server received request: {a} + {b}")
    return a + b

@mcp.tool()
def greet(name: str) -> str:
    """打招呼"""
    return f"Hello, {name}! This message came over HTTP."

# 3. 运行服务 (修正部分)
if __name__ == "__main__":
    print("Starting MCP Server...")
    # 指定 transport='sse' 来启动 HTTP 服务
    # 默认端口是 8000，SSE 端点默认为 /sse
    mcp.run(transport="http")