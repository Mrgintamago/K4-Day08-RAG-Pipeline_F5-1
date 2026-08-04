"""
Task 6 — Lexical Search Module (BM25 + TF-IDF).

Module cung cấp HAI thuật toán sparse retrieval:
    lexical_search()  — BM25, dùng chính thức trong pipeline Task 9
    tfidf_search()    — TF-IDF + cosine, giữ để đối chứng  ⭐ BONUS

Xem docstring của ``tfidf_search()`` để biết TF-IDF khác BM25 ở 3 điểm nào và
vì sao nhóm chọn BM25 cho corpus này.
So sánh trực tiếp: ``python -X utf8 -m src.task6_lexical_search --compare``

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


# =============================================================================
# BONUS — TF-IDF song song BM25
# =============================================================================

_TFIDF_VECTORIZER = None
_TFIDF_MATRIX = None


def build_tfidf_index(corpus: list[dict]):
    """Xây dựng ma trận TF-IDF từ corpus, dùng chung tokenizer với BM25."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not isinstance(corpus, list):
        raise TypeError("corpus phải là list")
    if not corpus:
        return None, None

    # Dùng lại _tokenize() của BM25 để so sánh hai thuật toán được công bằng:
    # cùng cách bỏ dấu, cùng cách tách từ, chỉ khác công thức tính điểm.
    vectorizer = TfidfVectorizer(
        analyzer=lambda text: _tokenize(text),
        sublinear_tf=False,   # giữ TF tuyến tính đúng định nghĩa TF-IDF gốc
        norm="l2",            # chuẩn hoá vector, xem giải thích ở tfidf_search()
    )
    matrix = vectorizer.fit_transform(_searchable_text(doc) for doc in corpus)
    return vectorizer, matrix


def _ensure_tfidf():
    """Lazy-load, cache giống BM25."""
    global CORPUS, _TFIDF_VECTORIZER, _TFIDF_MATRIX
    if not CORPUS:
        CORPUS = _load_corpus()
    if _TFIDF_VECTORIZER is None and CORPUS:
        _TFIDF_VECTORIZER, _TFIDF_MATRIX = build_tfidf_index(CORPUS)
    return _TFIDF_VECTORIZER, _TFIDF_MATRIX


def tfidf_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Lexical search bằng TF-IDF + cosine similarity, thay cho BM25.

    ─────────────────────────────────────────────────────────────────────────
    TF-IDF KHÁC BM25 Ở ĐÂU — 3 điểm cốt lõi
    ─────────────────────────────────────────────────────────────────────────

    Cả hai cùng xuất phát từ ý tưởng "từ hiếm thì quan trọng hơn" (IDF) và
    "từ xuất hiện nhiều trong tài liệu thì tài liệu đó liên quan hơn" (TF).
    Khác nhau ở CÁCH xử lý hai đại lượng đó.

    ① BÃO HOÀ TẦN SUẤT (term frequency saturation)

        TF-IDF : điểm tăng TUYẾN TÍNH theo số lần xuất hiện.
                 score ∝ tf
                 Từ "thuế" lặp 40 lần cho điểm gấp 4 lần khi lặp 10 lần.

        BM25   : có tham số k1 làm điểm BÃO HOÀ.
                 score ∝ tf·(k1+1) / (tf + k1·(...))
                 Với k1=1.5, chênh lệch giữa lặp 10 và lặp 40 lần rất nhỏ.

        Vì sao quan trọng: một chunk nhắc "thuế" 40 lần chưa chắc trả lời câu
        hỏi về thuế tốt hơn chunk nhắc 10 lần nhưng đúng điều khoản. TF-IDF dễ
        bị "keyword stuffing" đánh lừa, BM25 thì không.

    ② CHUẨN HOÁ ĐỘ DÀI TÀI LIỆU

        TF-IDF : chuẩn hoá bằng norm L2 trên toàn vector — chia đều cho độ dài
                 vector, KHÔNG so sánh với độ dài trung bình của corpus.

        BM25   : tham số b=0.75 phạt tài liệu dài hơn trung bình, dựa trực tiếp
                 vào tỉ lệ |d|/avgdl.

    ③ HỆ QUẢ TRÊN CORPUS CỦA NHÓM — điểm khác biệt rõ nhất

        Corpus này lệch độ dài rất mạnh:
            luat-doanh-nghiep-2020.md          ~328.000 ký tự
            article_07_track-international...  ~300 ký tự
        chênh nhau hơn 1.000 lần.

        Chuẩn hoá L2 của TF-IDF không "biết" corpus có độ dài trung bình bao
        nhiêu, nên các chunk cắt ra từ văn bản luật dài — vốn lặp lại nhiều
        thuật ngữ pháp lý giống nhau — dễ được đẩy lên cao một cách máy móc.
        BM25 với b=0.75 so trực tiếp với avgdl nên công bằng hơn giữa hai loại
        tài liệu.

        Đó là lý do nhóm chọn BM25 làm nhánh sparse chính thức trong Task 9,
        còn TF-IDF giữ lại để đối chứng.

    ─────────────────────────────────────────────────────────────────────────
    SỐ ĐO THỰC TẾ trên index 1.216 chunk (`--compare`)
    ─────────────────────────────────────────────────────────────────────────

    Query 1: "Điều 33 Luật Doanh nghiệp quy định gì"

        BM25    #1 [15.91]  "Điều 33. Cung cấp thông tin về nội dung đăng ký..."  ✅ đúng
        TF-IDF  #1 [0.2467] "phải thông báo công khai trên Cổng thông tin..."     ❌ lệch
                #3 [0.2380] "Điều 33. Cung cấp thông tin..."                      (tụt hạng 3)

        → BM25 đưa đúng điều luật lên #1, TF-IDF đẩy xuống #3. Với câu hỏi có
          số hiệu điều luật, bão hoà TF của BM25 giúp token hiếm "33" giữ trọng
          số cao thay vì bị các chunk lặp nhiều thuật ngữ pháp lý chung lấn át.

    Query 2: "phương thức thanh toán shopee"

        BM25    top-3 đều từ article_04_available-payment-methods.md   ✅ đúng tài liệu
        TF-IDF  #1 từ article_03_change-payment-method-prepaid-order.md ❌ sai tài liệu

        → Chunk của article_03 ngắn hơn nên sau chuẩn hoá L2, mật độ từ khoá
          bị thổi lên. BM25 phạt theo |d|/avgdl nên không mắc lỗi này.

    Khoảng điểm cũng khác hẳn: BM25 ~11–16 (không chặn trên), TF-IDF 0–1
    (cosine). Đây là lý do Task 7 phải gộp bằng RRF theo thứ hạng thay vì
    cộng điểm trực tiếp.

    ─────────────────────────────────────────────────────────────────────────

    Returns:
        List of {'content', 'score' (cosine similarity ∈ [0,1]), 'metadata'},
        sorted theo score giảm dần.

        Lưu ý về thang điểm: TF-IDF trả cosine ∈ [0,1] còn BM25 trả điểm không
        chặn trên. Muốn gộp hai nhánh phải dùng RRF (gộp theo THỨ HẠNG) như
        Task 7, không được cộng điểm trực tiếp.
    """
    if not isinstance(query, str):
        raise TypeError("query phải là chuỗi")
    if top_k <= 0 or not query.strip():
        return []

    vectorizer, matrix = _ensure_tfidf()
    if vectorizer is None or matrix is None:
        return []

    from sklearn.metrics.pairwise import cosine_similarity

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix)[0]

    ranked = sorted(range(len(CORPUS)), key=lambda i: float(scores[i]), reverse=True)

    results = []
    for i in ranked:
        score = float(scores[i])
        if score <= 0:
            break
        results.append({
            "content": CORPUS[i]["content"],
            "score": round(score, 6),
            "metadata": CORPUS[i].get("metadata", {}).copy(),
        })
        if len(results) >= top_k:
            break

    return results


def compare_bm25_vs_tfidf(query: str, top_k: int = 3) -> None:
    """
    In cạnh nhau kết quả của hai thuật toán — dùng để dẫn chứng khi demo.

    Chạy: python -X utf8 -m src.task6_lexical_search --compare
    """
    print("=" * 78)
    print(f"QUERY: {query}")
    print("=" * 78)
    for name, fn in (("BM25", lexical_search), ("TF-IDF", tfidf_search)):
        print(f"\n--- {name} ---")
        for rank, r in enumerate(fn(query, top_k=top_k), 1):
            src = r["metadata"].get("source", "?")
            print(f"  {rank}. [{r['score']:.4f}] {src[:44]:44} | {r['content'][:52]}")


if __name__ == "__main__":
    import sys

    if "--compare" in sys.argv:
        for q in [
            "Điều 33 Luật Doanh nghiệp quy định gì",   # câu có số hiệu điều luật
            "phương thức thanh toán shopee",            # câu từ khoá thông thường
        ]:
            compare_bm25_vs_tfidf(q, top_k=3)
            print()
    else:
        results = lexical_search("phương thức thanh toán shopee", top_k=5)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
