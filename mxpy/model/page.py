import traceback
import clr
import importlib
from mxpy.model.util import TransactionManager
from mxpy.model import folder as _folder
from Mendix.StudioPro.ExtensionsAPI.Model.Pages import IPage  # type: ignore
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")

# 确保所有依赖的模块都是最新的
importlib.reload(_folder)


async def ensure_pages(ctx, fullPaths: list[str]) -> str:
    """
    遍历页面创建请求，创建或更新它们，并返回一个纯文本报告。
    """
    report_lines = ["开始页面创建流程..."]
    success_count = 0
    failure_count = 0
    current_app = ctx.CurrentApp

    for i, full_path in enumerate(fullPaths):
        report_lines.append(
            f"\n--- 处理请求 {i+1}/{len(fullPaths)}: {full_path} ---")

        try:
            with TransactionManager(current_app, f"创建/更新页面 {full_path}"):
                # 1. 确保文件夹路径存在并获取父容器和页面名称
                parent_container, page_name, module_name = _folder.ensure_folder(
                    current_app, full_path)

                if not parent_container or not page_name or not module_name:
                    raise ValueError(f"无效的路径: '{full_path}'")

                report_lines.append(f"- 模块 '{module_name}' 和文件夹路径已确保存在。")

                # 2. 查找或创建页面
                page = next((p for p in parent_container.GetDocuments()
                             if p.Name == page_name), None)

                if not page:
                    # 创建页面
                    page = current_app.Create[IPage]()
                    page.Name = page_name
                    parent_container.AddDocument(page)
                    report_lines.append(
                        f"- [SUCCESS] 页面 '{module_name}.{page_name}' 已创建。")
                else:
                    report_lines.append(
                        f"- [INFO] 页面 '{page.Name}' 已存在。")

            # 如果事务成功提交
            report_lines.append(
                f"[SUCCESS] 针对 '{full_path}' 的事务已提交。")
            success_count += 1

        except Exception as e:
            # TransactionManager 会自动回滚
            report_lines.append(
                f"[ERROR] 处理 '{full_path}' 失败: {e}")
            # traceback
            report_lines.append(traceback.format_exc())
            report_lines.append("[INFO] 事务已回滚。")
            failure_count += 1
            continue  # 继续处理下一个请求

    # 最终总结
    report_lines.append("\n\n--- 最终总结 ---")
    report_lines.append(
        f"总共处理请求数: {len(fullPaths)}")
    report_lines.append(f"成功: {success_count}")
    report_lines.append(f"失败: {failure_count}")
    report_lines.append("---------------------")

    return "\n".join(report_lines)
