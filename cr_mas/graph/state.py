from typing import TypedDict, List, Optional

class ReviewState(TypedDict):
    '''审查过程中的共享状态'''
    changed_files: List[str] # 存储本次更改文件
    style_report: Optional[dict] # 风格警察的报告，在产出之前为None
    raw_diff: Optional[str] # 具体修改哪些行
    commit_hash: Optional[str] 
    security_report: Optional[dict] # 安全哨兵的报告
    performance_report: Optional[dict] # 性能顾问的报告
    readability_report: Optional[dict] # 可读性顾问的报告
    extension_report: Optional[dict]
    final_report: Optional[dict] # 主编的最终报告
    react_trace: Optional[dict] # ReAct推理链

