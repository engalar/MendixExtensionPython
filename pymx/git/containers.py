# file: containers.py
from dependency_injector import containers, providers
from pathlib import Path

from services import (
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
        base_dir=providers.Factory(Path, config.workspace.base_dir)
    )

    # GitService 的工厂
    git_service = providers.Factory(
        GitService,
        repo_path=providers.Factory(Path, config.git.repo_path)
    )

    # MendixCliService 的工厂
    mendix_cli_service = providers.Factory(
        MendixCliService,
        mx_exe_path=providers.Factory(Path, config.mendix.mx_exe_path)
    )

    # DiffOrchestrator 的工厂，它依赖于其他服务
    # 容器会自动解决这些依赖关系
    diff_orchestrator = providers.Factory(
        DiffOrchestrator,
        workspace_manager=workspace_manager,
        git_service=git_service,
        mendix_cli_service=mendix_cli_service,
    )