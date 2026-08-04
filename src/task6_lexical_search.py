"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import re
import unicodedata

from rank_bm25 import BM25Okapi


CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}
_BM25_INDEX: BM25Okapi | None = None


def _normalize_text(text: str) -> str:
    """Chuẩn hóa chữ thường và bỏ dấu để query có/không dấu đều khớp."""
    text = text.casefold().replace("đ", "d")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _tokenize(text: str) -> list[str]:
    """Tokenize nhẹ, không cần thêm thư viện tách từ tiếng Việt."""
    return re.findall(r"\w+", _normalize_text(text), flags=re.UNICODE)


def _load_corpus() -> list[dict]:
    """Dùng chung corpus đã parse, chunk và lọc rác với dense retrieval.

    Import lười giúp ``build_bm25_index()`` vẫn có thể được kiểm thử độc lập bằng
    fixture. Task 4 cũng khởi tạo embedding model theo kiểu lazy nên thao tác này
    không cần API key, không tải model và không mở ChromaDB.
    """
    from .task4_chunking_indexing import chunk_documents, load_documents

    return chunk_documents(load_documents())


def _searchable_text(document: dict) -> str:
    """Ghép nội dung và metadata hữu ích để BM25 bắt được cả tên tài liệu."""
    metadata = document.get("metadata", {})
    metadata_text = " ".join(
        str(metadata.get(field, ""))
        for field in ("source", "title", "topic", "customer_role", "doc_type")
    )
    return f"{metadata_text}\n{document.get('content', '')}"


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    if not isinstance(corpus, list):
        raise TypeError("corpus phải là list")
    if not corpus:
        return None

    tokenized_corpus = []
    for index, document in enumerate(corpus):
        if not isinstance(document, dict) or not isinstance(
            document.get("content"), str
        ):
            raise ValueError(f"Document số {index} thiếu content dạng chuỗi")
        tokenized_corpus.append(_tokenize(_searchable_text(document)))

    # k1=1.5 tạo term-frequency saturation: một từ lặp quá nhiều không làm
    # điểm tăng vô hạn; b=0.75 chuẩn hóa độ dài để chunk dài không được ưu tiên.
    return BM25Okapi(tokenized_corpus, k1=1.5, b=0.75)


def _ensure_index() -> BM25Okapi | None:
    """Lazy-load corpus và cache BM25 index cho các lần tìm kiếm tiếp theo."""
    global CORPUS, _BM25_INDEX
    if not CORPUS:
        CORPUS = _load_corpus()
    if _BM25_INDEX is None and CORPUS:
        _BM25_INDEX = build_bm25_index(CORPUS)
    return _BM25_INDEX


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not isinstance(query, str):
        raise TypeError("query phải là chuỗi")
    if top_k <= 0 or not query.strip():
        return []

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    bm25 = _ensure_index()
    if bm25 is None:
        return []

    scores = bm25.get_scores(tokenized_query)
    ranked_indices = sorted(
        range(len(CORPUS)),
        key=lambda index: float(scores[index]),
        reverse=True,
    )

    results = []
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            break

        results.append(
            {
                "content": CORPUS[index]["content"],
                "score": score,
                "metadata": CORPUS[index].get("metadata", {}).copy(),
            }
        )
        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("phương thức thanh toán shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
