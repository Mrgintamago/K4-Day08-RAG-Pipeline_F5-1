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
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Dùng cùng cấu hình 800/100 đã chốt cho Task 4 để BM25 và dense retrieval
# xếp hạng trên các đơn vị văn bản tương đương nhau. F5-6 tự chunk trong RAM vì
# lexical search không cần embedding, API key hay ChromaDB.
CORPUS_CHUNK_SIZE = 800
CORPUS_CHUNK_OVERLAP = 100

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


def _parse_document(md_file: Path) -> dict | None:
    """Đọc một file Markdown chuẩn hóa và tách header khỏi nội dung thật."""
    raw_text = md_file.read_text(encoding="utf-8")
    parts = re.split(r"\r?\n---\r?\n", raw_text, maxsplit=1)
    if len(parts) != 2:
        return None

    header, content = parts
    metadata = {"source": md_file.name}

    title_match = re.search(r"^#\s+(.+)$", header, flags=re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()

    for key, value in re.findall(r"\*\*(.*?):\*\*\s*(.*)", header):
        normalized_key = key.strip().casefold().replace(" ", "_")
        # Header dùng nhãn Source cho URL; giữ source là tên file để citation và
        # deduplicate ổn định, đồng thời lưu địa chỉ web ở trường url riêng.
        if normalized_key == "source":
            metadata["url"] = value.strip()
        else:
            metadata[normalized_key] = value.strip()

    return {"content": content.strip(), "metadata": metadata}


def _load_corpus() -> list[dict]:
    """Tạo corpus chunk từ toàn bộ ``data/standardized/**/*.md``."""
    if not STANDARDIZED_DIR.exists():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CORPUS_CHUNK_SIZE,
        chunk_overlap=CORPUS_CHUNK_OVERLAP,
        separators=["\n\n", "\n", "##", "#", ". ", " ", ""],
        length_function=len,
    )

    corpus = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        document = _parse_document(md_file)
        if document is None or not document["content"]:
            continue

        for chunk_index, chunk_text in enumerate(
            splitter.split_text(document["content"])
        ):
            metadata = document["metadata"].copy()
            metadata["chunk_index"] = chunk_index
            corpus.append({"content": chunk_text, "metadata": metadata})

    return corpus


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
