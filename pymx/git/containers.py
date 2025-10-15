# file: containers.py
import importlib
import os
from dependency_injector import containers, providers
from pathlib import Path
from pymx.git import services as services2
importlib.reload(services2)
from pymx.git.services import (
    WorkspaceManager,
    GitService,
    MendixCliService,
    DiffOrchestrator
)

class Container(containers.DeclarativeContainer):
    """
    依赖注入容器，用于管理应用的所有服务和配置。
    """
    # 允许在运行时覆盖配置
    config = providers.Configuration()

    # --- 服务提供者 (Providers) ---

    # WorkspaceManager 的工厂，它依赖于配置中的 base_dir
    workspace_manager = providers.Factory(
        WorkspaceManager,
        repo_path=config.git.repo_path
    )

    # GitService 的工厂
    git_service = providers.Factory(
        GitService,
        repo_path=config.git.repo_path
    )

    # MendixCliService 的工厂
    mendix_cli_service = providers.Factory(
        MendixCliService,
        mx_exe_path=config.mendix.mx_exe_path
    )

    # DiffOrchestrator 的工厂，它依赖于其他服务
    # 容器会自动解决这些依赖关系
    diff_orchestrator = providers.Factory(
        DiffOrchestrator,
        workspace_manager=workspace_manager,
        git_service=git_service,
        mendix_cli_service=mendix_cli_service,
    )

def perform_pymx_diff(repo_path: str, old_commit: str, new_commit: str) -> dict:
    """
    Uses the pymx.git library to compare two commits and returns the diff result.
    This function is separated from the command handler for better SOC.
    """
    # Create a container for pymx's own dependency injection
    container = Container()

    # NOTE: In a real-world scenario, this Mendix executable path should be
    # discovered automatically or made configurable by the user.
    # From user example
    mendix_exe_path = "D:/Program Files/Mendix/10.24.4.77222/modeler/mx.exe"
    if not os.path.exists(mendix_exe_path):
        raise FileNotFoundError(
            f"Mendix executable not found at '{mendix_exe_path}'. Please configure the correct path in main.py.")

    # Configure the container for pymx
    container.config.from_dict({
        "git": {
            "repo_path": repo_path
        },
        "mendix": {
            "mx_exe_path": os.fspath(mendix_exe_path)
        }
    })
    # container.wire(modules=[__name__])
    # Run the comparison
    orchestrator = container.diff_orchestrator()
    diff_result = orchestrator.compare_commits(
        old_commit=old_commit,
        new_commit=new_commit
    )
    # The result from pymx should be a serializable dictionary
    return diff_result