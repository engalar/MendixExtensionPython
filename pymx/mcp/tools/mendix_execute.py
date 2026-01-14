"""
Python 代码执行工具
允许在 Studio Pro 环境中执行 Python 代码片段
"""
from pymx.mcp.tool_registry import mcp
from pymx.mcp import mendix_context as ctx
from typing import Annotated
from pydantic import Field
import sys
from io import StringIO


# TODO: 描述中添加更明确的提示词引导LLM使用
@mcp.tool(
    name="execute_python",
    description="执行 Python 代码并返回输出结果。代码在 Studio Pro 进程中运行，可以访问所有 Mendix 服务。"
)
async def execute_python(
    code: Annotated[str, Field(description="要执行的 Python 代码，通常是一个无参函数，返回字符串")]
) -> str:
    """
    执行 Python 代码并捕获输出

    Args:
        code: Python 代码字符串

    Returns:
        执行结果或错误的字符串表示
    """
    # 保存原始 stdout 和 stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        # 重定向 stdout 和 stderr 以捕获 print 输出
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        # 执行代码
        # 使用 exec 而不是 eval，因为我们需要支持多行语句
        exec_globals = {
            "__builtins__": __builtins__,
            "ctx": ctx,  # 提供对 Mendix 服务的访问
        }

        exec_locals = {}
        exec(code, exec_globals, exec_locals)

        # 获取捕获的输出
        stdout_output = sys.stdout.getvalue()
        stderr_output = sys.stderr.getvalue()

        # 检查是否有返回值
        # 如果代码中定义了函数并调用，或者有 return 语句，结果会在 exec_locals 中
        result_parts = []

        if stdout_output:
            result_parts.append(f"标准输出:\n{stdout_output}")

        if stderr_output:
            result_parts.append(f"标准错误:\n{stderr_output}")

        # 如果代码有返回值（最后一个表达式的结果）
        if 'result' in exec_locals:
            result_parts.append(f"返回值:\n{str(exec_locals['result'])}")

        if result_parts:
            return "\n".join(result_parts)
        else:
            return "代码执行成功（无输出）"

    except Exception as e:
        # 捕获执行错误
        import traceback
        error_details = traceback.format_exc()
        return f"执行错误:\n{error_details}"

    finally:
        # 恢复原始 stdout 和 stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
