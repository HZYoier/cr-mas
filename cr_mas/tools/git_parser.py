import git


def parse_staged_diff(repo_path: str = ".") -> dict:
    """读取 Git 暂存区（git diff --cached），返回变更文件列表和 diff 文本"""
    # 打开仓库
    try:
        repo = git.Repo(repo_path)
    except git.InvalidGitRepositoryError:
        raise RuntimeError(
            "❌ 当前目录不是 Git 仓库。请在 Git 项目根目录运行 cr commit。"
        )
    
    try:
        head_commit = repo.head.commit
        commit_hash = head_commit.hexsha[:8] 
    except ValueError:
        # 空仓库(没有commit)，HEAD不存在，从暂存区获取文件列表
        staged_output = repo.git.diff("--cached", "--name-only")
        changed_files = [f for f in staged_output.strip().split("\n") if f]
        raw_diff = repo.git.diff("--cached") if changed_files else ""
        return {
            "changed_files": changed_files,
            "raw_diff": raw_diff,
            "commit_hash": None
        }
    
    diff_index = repo.index.diff(head_commit) # 变更文件清单
    changed_files = []
    for item in diff_index:
        if item.a_path:
            changed_files.append(item.a_path)

    changed_files = list(set(changed_files))

    raw_diff = repo.git.diff("--cached")

    return {
        "changed_files": changed_files,
        "raw_diff": raw_diff,
        "commit_hash": commit_hash
    }



