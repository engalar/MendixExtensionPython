# file: services.py
import subprocess
import logging
import shutil
import json
import tarfile
from pathlib import Path
from typing import Dict, Any

# 配置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkspaceManager:
    """负责管理临时工作目录的创建和清理。"""
    def __init__(self, repo_path: str):
        self.base_dir = Path(repo_path) / Path(".mendix-cache/pymx_diff")
        logging.info(f"WorkspaceManager initialized with base directory: {self.base_dir}")

    def setup_diff_dirs(self, old_commit: str, new_commit: str) -> Dict[str, Path]:
        """为一次对比操作创建并返回所需的目录结构。"""
        # 使用 commit hash 的一部分创建唯一的会话目录，避免冲突
        session_dir = self.base_dir / f"diff_{old_commit[:7]}_vs_{new_commit[:7]}"
        
        # 清理旧的会话目录（如果存在）
        if session_dir.exists():
            logging.warning(f"Cleaning up existing session directory: {session_dir}")
            shutil.rmtree(session_dir)
        
        dir_a = session_dir / "version_A"
        dir_b = session_dir / "version_B"
        
        dir_a.mkdir(parents=True, exist_ok=True)
        dir_b.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Created temporary directories:\n  - Old: {dir_a}\n  - New: {dir_b}")

        return {
            "session": session_dir,
            "old_version": dir_a,
            "new_version": dir_b,
            "output_json": session_dir / "app_diff.json"
        }


class GitService:
    """封装所有 Git 相关操作。"""
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        if not (self.repo_path / ".git").is_dir():
            raise FileNotFoundError(f"'{self.repo_path}' is not a valid Git repository.")
        logging.info(f"GitService initialized for repository: {self.repo_path}")

    def get_mpr_file_name(self, commit_id: str) -> str:
        """
        从指定 commit 的 'mprcontents/mprname' 文件中动态获取 .mpr 文件名。
        """
        file_path_in_repo = "mprcontents/mprname"
        command = [
            "git",
            "-C", str(self.repo_path),
            "show",
            f"{commit_id}:{file_path_in_repo}"
        ]
        logging.info(f"Attempting to read '{file_path_in_repo}' from commit '{commit_id[:7]}'")
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            mpr_name = result.stdout.strip()
            if not mpr_name.endswith(".mpr"):
                raise ValueError(f"Content of 'mprname' ('{mpr_name}') is not a valid .mpr file name.")
            logging.info(f"Discovered MPR file name: '{mpr_name}'")
            return mpr_name
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to read '{file_path_in_repo}' from commit '{commit_id}'. It might not exist in this commit.")
            logging.error(f"Stderr: {e.stderr}")
            raise FileNotFoundError(f"Could not find '{file_path_in_repo}' in commit '{commit_id}'.")

    def extract_model_files(self, commit_id: str, target_dir: Path, mpr_file_name: str):
        """
        【已修复】从指定的 commit 高效地检出 Mendix 模型文件。
        使用 Popen 和 tarfile 库，避免 shell 依赖，确保只检出指定文件。
        """
        paths_to_extract = [mpr_file_name, "mprcontents/"]
        
        command = [
            "git",
            "-C", str(self.repo_path),
            "archive",
            commit_id,
            "--" # 明确告知 git 后续都是路径参数
        ] + paths_to_extract
        
        logging.info(f"Executing git archive for commit '{commit_id[:7]}' into '{target_dir}'...")
        try:
            # 启动 git archive 进程，并将其标准输出重定向到管道
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 使用 tarfile 库直接从进程的输出流中解压
            with tarfile.open(fileobj=process.stdout, mode='r|*') as tar:
                tar.extractall(path=target_dir)

            # 等待进程结束并检查错误
            stderr = process.communicate()[1]
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)
                
            logging.info(f"Successfully extracted model files for commit '{commit_id[:7]}'.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"Failed to extract files from git for commit {commit_id}.")
            if hasattr(e, 'stderr') and e.stderr:
                 logging.error(f"Stderr: {e.stderr.decode('utf-8', errors='ignore')}")
            raise

class MendixCliService:
    """封装 Mendix mx.exe 命令行工具的操作。"""
    def __init__(self, mx_exe_path: str):
        self.mx_exe_path = Path(mx_exe_path)
        if not self.mx_exe_path.is_file():
            raise FileNotFoundError(f"Mendix executable not found at '{self.mx_exe_path}'")
        logging.info(f"MendixCliService initialized with mx.exe path: {self.mx_exe_path}")

    def diff(self, mpr_old_path: Path, mpr_new_path: Path, output_path: Path) -> None:
        """
        执行 mx.exe diff 命令。
        关键：包含了 '-l' 参数以处理项目版本转换。
        """
        command = [
            str(self.mx_exe_path),
            "diff",
            str(mpr_old_path),
            str(mpr_new_path),
            str(output_path),
            "-l"  # 自动进行项目版本转换
        ]
        
        logging.info(f"Executing Mendix diff command...")
        logging.debug(f"Command: {' '.join(command)}")
        try:
            # 不使用 shell=True，因为命令和参数是列表形式，更安全
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
            logging.info("Mendix diff command completed successfully.")
            logging.info(f"Diff output saved to: {output_path}")
            if result.stdout:
                logging.debug(f"Mendix CLI STDOUT:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            logging.error("Mendix diff command failed.")
            logging.error(f"Stderr: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            logging.error("Mendix diff command timed out after 300 seconds.")
            raise

class DiffOrchestrator:
    """
    业务流程编排器 (控制反转 IoC)。
    它不关心 Git 或 mx.exe 如何工作，只负责调用相应的服务来完成对比任务。
    依赖通过构造函数注入 (依赖倒置 DIP)。
    """
    def __init__(self,
                 workspace_manager: WorkspaceManager,
                 git_service: GitService,
                 mendix_cli_service: MendixCliService,
                 ):
        self.workspace_manager = workspace_manager
        self.git_service = git_service
        self.mendix_cli_service = mendix_cli_service

    def compare_commits(self, old_commit: str, new_commit: str) -> Dict[str, Any]:
        """
        【已改进】执行完整流程，自动发现 MPR 文件名。
        """
        logging.info(f"Starting comparison between commits '{old_commit[:7]}' and '{new_commit[:7]}'.")
        
        # 1. 动态获取 MPR 文件名（使用较新的 commit 作为参考）
        mpr_file_name = self.git_service.get_mpr_file_name(new_commit)

        # 2. 准备工作区
        dirs = self.workspace_manager.setup_diff_dirs(old_commit, new_commit)
        dir_old = dirs["old_version"]
        dir_new = dirs["new_version"]
        output_file = dirs["output_json"]

        try:
            # 3. 从 Git 检出模型文件
            self.git_service.extract_model_files(old_commit, dir_old, mpr_file_name)
            self.git_service.extract_model_files(new_commit, dir_new, mpr_file_name)

            mpr_old = dir_old / mpr_file_name
            mpr_new = dir_new / mpr_file_name

            if not mpr_old.exists() or not mpr_new.exists():
                raise FileNotFoundError("MPR file was not found after git extraction.")

            # 4. 执行 Mendix diff
            self.mendix_cli_service.diff(mpr_old, mpr_new, output_file)
            
            # 5. 【已修复】读取并返回结果，使用 'utf-8-sig' 编码处理 BOM
            if output_file.exists() and output_file.stat().st_size > 0:
                logging.info("Comparison successful. Reading JSON result.")
                with open(output_file, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            else:
                logging.error("Diff process finished, but the output file is missing or empty.")
                raise RuntimeError("Failed to generate diff file.")
        except Exception as e:
            logging.error(f"An error occurred during the orchestration: {e}")
            raise