import chardet


def read_source(file_path: str) -> str:
    """读取文件内容，自动检测编码（chardet）"""
    with open(file_path, "rb") as f:
        raw = f.read()
    encoding = chardet.detect(raw)["encoding"] or "utf-8"
    return raw.decode(encoding)
