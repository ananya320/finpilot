import chromadb
from ..config import settings

_col = None
def collection():
    global _col
    if _col is None:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        _col = client.get_or_create_collection("documents")
    return _col

def index_text(doc_id: int, filename: str, text: str, size: int = 1000):
    chunks = [text[i:i + size] for i in range(0, len(text), size) if text[i:i + size].strip()]
    if not chunks:
        return
    collection().add(
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"doc_id": doc_id, "filename": filename}] * len(chunks),
    )

def search(query: str, k: int = 4):
    res = collection().query(query_texts=[query], n_results=k)
    return [{"filename": m["filename"], "text": d}
            for d, m in zip(res["documents"][0], res["metadatas"][0])]