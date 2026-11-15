from ..config import settings

_col = None


def collection():
    global _col
    if not settings.enable_vector_search:
        raise RuntimeError("Document search is turned off on this server.")
    if _col is None:
        import chromadb   # imported here so a disabled server never loads it
        client = chromadb.PersistentClient(path="./chroma_data")
        _col = client.get_or_create_collection("documents")
    return _col


def index_text(doc_id: int, business_id: int, filename: str, text: str, size: int = 1000):
    if not settings.enable_vector_search:
        return
    chunks = [text[i:i + size] for i in range(0, len(text), size) if text[i:i + size].strip()]
    if not chunks:
        return
    collection().add(
        ids=[f"{doc_id}-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"doc_id": doc_id, "business_id": business_id, "filename": filename}] * len(chunks),
    )


def search(query: str, business_id: int, k: int = 4):
    res = collection().query(query_texts=[query], n_results=k, where={"business_id": business_id})
    return [{"filename": m["filename"], "text": d}
            for d, m in zip(res["documents"][0], res["metadatas"][0])]


def delete_document(doc_id: int):
    if settings.enable_vector_search:
        collection().delete(where={"doc_id": doc_id})


def delete_business(business_id: int):
    if settings.enable_vector_search:
        collection().delete(where={"business_id": business_id})