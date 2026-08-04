"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results

⚠️ BẪY THƯỜNG GẶP — đọc kỹ trước khi code:
    Nếu bạn dùng điểm RRF đã fuse (Task 7) để so với score_threshold, bạn sẽ gặp bug
    thật: RRF max score luôn ≈ 1/(k+1) ≈ 0.0164 (k=60) BẤT KỂ nội dung có liên quan
    hay không. Nếu đặt threshold thấp (như 0.005) để "hợp" với thang điểm RRF, thực
    chất KHÔNG câu hỏi nào đủ thấp để trigger fallback nữa — kể cả query hoàn toàn vô
    nghĩa vẫn trả về kết quả "hybrid" (rác) thay vì fallback đúng như thiết kế.

    Cách sửa đúng: giữ điểm cosine similarity GỐC của semantic_search (trước khi qua
    RRF) làm căn cứ quyết định fallback, tách biệt khỏi điểm RRF dùng để sắp xếp kết
    quả cuối cùng. Calibrate threshold bằng cách tự đo: chạy vài câu hỏi chắc chắn
    liên quan và vài câu chắc chắn lạc đề/rác qua semantic_search, xem khoảng cách
    điểm số giữa hai nhóm rồi chọn ngưỡng nằm giữa.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

# ĐÃ CALIBRATE trên index thật (1.216 chunk, paraphrase-multilingual-MiniLM-L12-v2).
# Cách đo: chạy semantic_search() với các câu chắc chắn đúng chủ đề và các câu chắc
# chắn lạc đề, ghi lại cosine top-1 của từng nhóm:
#
#     Đúng chủ đề (thuế TNCN, hồ sơ hộ kinh doanh, sản phẩm cấm) : 0.444 – 0.531
#     Lạc đề      (thời tiết Hà Nội, công thức nấu phở)          : 0.265 – 0.365
#
# Hai khoảng cách nhau ~0.08 → đặt ngưỡng vào giữa: 0.40.
#
# KHÔNG dùng 0.48 như giá trị mẫu của LAB_GUIDE: con số đó hợp với thang điểm của
# BAAI/bge-m3, còn model nhóm đang dùng cho cosine thấp hơn. Để 0.48 thì câu ĐÚNG chủ
# đề (0.444) cũng bị coi là kém và rơi nhầm xuống fallback PageIndex — mất hết tác dụng
# của hybrid search.
#
# Đổi embedding model → PHẢI đo lại, thang điểm mỗi model một khác.
#
# LƯU Ý: đây là ngưỡng cho ĐIỂM COSINE GỐC (dense_results[0]["score"], thang [0,1]),
# KHÔNG phải điểm RRF đã fuse (top-1 RRF luôn ≈ 1/61 ≈ 0.016 nên fallback sẽ không bao
# giờ trigger nếu so nhầm).
SCORE_THRESHOLD = 0.40  # Nếu best score (cosine gốc) < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search → dense_results (giữ điểm cosine gốc)
          ├→ Lexical Search  → sparse_results
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank → reranked_results
          │
          └→ If dense_results[0]["score"] < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm cosine gốc tối thiểu (KHÔNG phải điểm RRF)
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # -------------------------------------------------------------------------
    # Bước 1 — Chạy cả hai retriever, lấy dư gấp đôi top_k
    #
    # Lấy top_k * 2 ở mỗi nhánh chứ không phải top_k: sau khi RRF gộp hai danh sách
    # sẽ có phần trùng nhau, nếu chỉ lấy đúng top_k mỗi bên thì số ứng viên duy nhất
    # còn lại có thể ít hơn top_k và kết quả cuối bị thiếu.
    # -------------------------------------------------------------------------
    dense_results = _safe_search(semantic_search, query, top_k * 2, "semantic_search")
    sparse_results = _safe_search(lexical_search, query, top_k * 2, "lexical_search")

    # -------------------------------------------------------------------------
    # Bước 2 — GIỮ ĐIỂM COSINE GỐC TRƯỚC KHI GỘP
    #
    # Đây là mấu chốt của cả Task 9. Sau khi qua rerank_rrf(), trường "score" bị
    # ghi đè bằng điểm RRF (≈ 1/61 ≈ 0.016 cho top-1, chỉ phản ánh THỨ HẠNG chứ
    # không phản ánh độ liên quan). Nếu đọc score sau khi gộp rồi đem so với
    # threshold thì mọi query — kể cả câu vô nghĩa — đều cho ra cùng một khoảng
    # điểm, và fallback không bao giờ trigger đúng.
    #
    # Vì vậy chụp lại điểm cosine ngay tại đây, trước mọi bước biến đổi.
    # -------------------------------------------------------------------------
    best_cosine = dense_results[0]["score"] if dense_results else 0.0

    # -------------------------------------------------------------------------
    # Bước 3 — Quyết định fallback dựa trên điểm cosine gốc
    #
    # Đặt trước bước gộp/rerank để khỏi tốn công tính toán trên tập ứng viên mà
    # ta đã biết là kém.
    # -------------------------------------------------------------------------
    if best_cosine < score_threshold:
        print(f"  ⚠ Semantic best score ({best_cosine:.3f}) < threshold "
              f"({score_threshold}) → fallback PageIndex")
        fallback = _safe_search(pageindex_search, query, top_k, "pageindex_search")
        if fallback:
            for item in fallback:
                item.setdefault("source", "pageindex")
            return fallback[:top_k]
        # PageIndex cũng không có gì → vẫn trả kết quả hybrid còn hơn trả rỗng,
        # nhưng đánh dấu để tầng trên (Task 10) biết độ tin cậy thấp.
        print("  ⚠ PageIndex không trả kết quả — dùng tạm kết quả hybrid điểm thấp")

    # -------------------------------------------------------------------------
    # Bước 4 — Gộp hai danh sách bằng RRF rồi rerank
    # -------------------------------------------------------------------------
    ranked_lists = [lst for lst in (dense_results, sparse_results) if lst]
    if not ranked_lists:
        return []

    merged = rerank_rrf(ranked_lists, top_k=top_k * 2)
    for item in merged:
        item["source"] = "hybrid"

    if use_reranking and merged:
        try:
            final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        except Exception as exc:
            print(f"  ! rerank({RERANK_METHOD}) lỗi: {type(exc).__name__}: {exc} "
                  f"— dùng thứ tự RRF")
            final_results = merged[:top_k]
    else:
        final_results = merged[:top_k]

    # rerank() có thể trả về item chưa gắn nhãn nguồn
    for item in final_results:
        item.setdefault("source", "hybrid")

    return final_results[:top_k]


def _safe_search(fn, query: str, top_k: int, name: str) -> list[dict]:
    """
    Gọi một retriever, nuốt lỗi và trả list rỗng thay vì để vỡ cả pipeline.

    Vì sao cần: pipeline phụ thuộc 3 module của 3 người khác nhau và 1 API ngoài
    (PageIndex). Nếu một nhánh hỏng — chưa index, hết quota, mất mạng — thì cả
    `retrieve()` sập theo, kéo luôn Task 10 và chatbot. Hạ cấp êm (degrade
    gracefully) giữ cho phần còn lại vẫn trả lời được.
    """
    try:
        results = fn(query, top_k=top_k)
        return results if isinstance(results, list) else []
    except Exception as exc:
        print(f"  ! {name} lỗi: {type(exc).__name__}: {exc} — bỏ qua nhánh này")
        return []


if __name__ == "__main__":
    test_queries = [
        "What payment methods does Shopee support?",
        "How do I request a return or refund?",
        "What evidence do I need for a refund request?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
