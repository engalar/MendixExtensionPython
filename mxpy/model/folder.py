from Mendix.StudioPro.ExtensionsAPI.Model.Projects import IModule, IFolder, IFolderBase  # type: ignore
from typing import List, Literal, Tuple, Optional

import clr

from mxpy.model import module as _module
import importlib
importlib.reload(_module)
clr.AddReference("Mendix.StudioPro.ExtensionsAPI")


def ensure_folder(current_app, full_path: str) -> Tuple[Optional[IFolderBase], Optional[str], Optional[str]]:
    """
    确保指定完整路径中的文件夹结构存在。

    Args:
        current_app: 当前的 Mendix App 实例。
        full_path: 完整路径，例如 "MyModule/Folder1/Folder2/LastDocName"。

    Returns:
        一个元组 (parent_container, doc_name, module_name):
        - parent_container: 确保存在的父容器（IModule 或 IFolder）实例。
        - doc_name: 路径最后部分的文档名称。
        - module_name: 路径第一部分的模块名称。
        如果路径无效或模块不存在，则返回 (None, None, None)。
    """
    if not current_app or not full_path or not full_path.strip():
        return None, None, None

    parts = [part for part in full_path.split('/') if part]
    if not parts:
        return None, None, None

    module_name = parts[0]
    doc_name = parts[-1]

    if not current_app.Root:
        return None, None, None

    # 确保模块存在 (这里我们假设模块必须预先存在，不自动创建)
    module = _module.ensure_module(current_app, module_name)

    current_container: IFolderBase = module

    # 迭代中间的文件夹部分 (跳过模块名和文档名)
    # parts[1:-1] 等同于 C# 的 .Skip(1).Take(parts.Length - 2)
    for part in parts[1:-1]:
        folders = current_container.GetFolders()
        next_container = next((f for f in folders if f.Name == part), None)

        if next_container is None:
            # 文件夹不存在，创建它
            new_folder = current_app.Create[IFolder]()
            new_folder.Name = part

            current_container.AddFolder(new_folder)

            current_container = new_folder
        else:
            # 文件夹已存在，进入下一级
            current_container = next_container
    return current_container, doc_name, module_name
