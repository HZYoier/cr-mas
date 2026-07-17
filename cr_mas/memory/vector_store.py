"""ChromaDB 向量存储——语义检索历史裁决"""

import chromadb
from pathlib import Path

DB_DIR = str(Path(__file__).parent.parent.parent / "cr_mas_vectordb")

_client = None


def _get_collection():
    """懒加载 ChromaDB 集合"""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=DB_DIR)
    return _client.get_or_create_collection(
        name="verdict_history",
        metadata={"hnsw:space": "cosine"},
    )


def store_verdict(commit_hash: str, module: str, conflict_type: str, decision: str):
    """
    将一次审查的主编裁决向量化存入 ChromaDB
    后续相似场景可以语义检索
    """
    text = f"模块:{module} 冲突:{conflict_type} 裁决:{decision}"
    collection = _get_collection()
    collection.add(
        documents=[text],
        metadatas=[{
            "commit_hash": commit_hash,
            "module": module,
            "conflict_type": conflict_type,
            "decision": decision,
        }],
        ids=[commit_hash or f"verdict_{hash(text)}"],
    )


def retrieve_similar(query: str, k: int = 3) -> list[dict]:
    """
    语义检索：找到与当前场景最相似的 K 条历史裁决。
    返回: [{"document": "...", "metadata": {...}}, ...]
    """
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=k,
        )
        if results and results["documents"] and results["documents"][0]:
            return [
                {"document": doc, "metadata": meta}
                for doc, meta in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                )
            ]
    except Exception:
        pass
    return []
