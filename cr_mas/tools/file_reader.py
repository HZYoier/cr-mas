"""统一读取文件并检测编码"""

import chardet


def read_source(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    return raw.decode(encoding)
