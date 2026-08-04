"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""
from .task4_chunking_indexing import get_collection, get_embedding_model



def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    try:
        model = get_embedding_model()
        collection = get_collection()
        if collection is None:
            return []
    except Exception as e:
        # This can happen if task4 hasn't run, or if there's an issue loading the model.
        print(f"Could not perform semantic search. Have you run the indexing pipeline (Task 4)?")
        print(f"Error: {e}")
        return []

    # get_embedding_model() trả về _Embedder — .encode() đã cho sẵn list[float],
    # không cần .tolist() như khi dùng trực tiếp SentenceTransformer.
    # Query BẮT BUỘC dùng cùng embedder với lúc index, nếu không vector nằm ở
    # hai không gian khác nhau và cosine similarity trở nên vô nghĩa.
    query_vector = model.encode(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    # Query results are a list of lists, one for each query vector. We have one.
    if not results or not results["documents"] or not results["documents"][0]:
        return []

    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        # QUAN TRỌNG: ChromaDB trả về cosine DISTANCE. Cần chuyển sang SIMILARITY.
        # Similarity = 1 - Distance.
        score = max(0.0, 1.0 - dist)
        output.append({"content": doc, "score": round(score, 4), "metadata": meta})

    # ChromaDB đã sắp xếp theo distance tăng dần, tương đương similarity giảm dần.
    # Sắp xếp lại ở đây để đảm bảo tính đúng đắn.
    output.sort(key=lambda x: x["score"], reverse=True)

    return output


if __name__ == "__main__":
    # Test
    results = semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
