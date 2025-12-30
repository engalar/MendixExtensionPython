# file: main.py
import sys
import pprint
from pymx.git.di import Container

def main():
    """应用主函数。"""
    container = Container()
    
    # 2. 加载配置 (可以来自文件、环境变量等)
    #    这里为了演示，直接使用字典
    container.config.from_dict({
        "git": {
            "repo_path": "D:/Users/Wengao.Liu/Mendix/CKODemo_AddressBook-main"
        },
        "mendix": {
            "mx_exe_path": "D:/Program Files/Mendix/10.24.4.77222/modeler/mx.exe" # 使用 D 盘路径
        }
    })

    # container.wire(modules=[__name__])

    # 定义要对比的 commit ID
    commit_old = "faf5a48891017d49b25bf00906db36b0134d9185"
    commit_new = "2cf83d7113511b69960be89d26b76350c7852278"
    
    # 【已改进】不再需要硬编码 mpr_file_name

    try:
        orchestrator = container.diff_orchestrator()
        
        # 【已改进】调用时不再需要传递 mpr_file_name
        diff_result = orchestrator.compare_commits(
            old_commit=commit_old,
            new_commit=commit_new
        )

        print("\n--- Diff Result ---")
        pprint.pprint(diff_result)
        print("\nComparison process completed successfully.")

    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 确保你的系统 PATH 中有 git.exe 和 tar.exe
    # (如果你安装了 Git for Windows，通常会自动添加)
    main()