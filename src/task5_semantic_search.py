"""
Task 5 — Semantic Search Module (+ HyDE & Query Expansion).
"""
from .task4_chunking_indexing import get_collection, get_embedding_model


# ---------------------------------------------------------------------------
# Core semantic search (giữ nguyên như cũ)
# ---------------------------------------------------------------------------
def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.
    """
    try:
        model = get_embedding_model()
        collection = get_collection()
        if collection is None:
            return []
    except Exception as e:
        print(f"Could not perform semantic search. Have you run the indexing pipeline (Task 4)?")
        print(f"Error: {e}")
        return []

    query_vector = model.encode(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if not results or not results["documents"] or not results["documents"][0]:
        return []

    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        score = max(0.0, 1.0 - dist)
        output.append({"content": doc, "score": round(score, 4), "metadata": meta})

    output.sort(key=lambda x: x["score"], reverse=True)
    return output


# ---------------------------------------------------------------------------
# HyDE — Hypothetical Document Embeddings
# ---------------------------------------------------------------------------
_HYDE_PROMPT_TEMPLATE = """Bạn là chuyên gia trong lĩnh vực được hỏi.
Hãy viết một đoạn văn ngắn (3-5 câu) TRẢ LỜI trực tiếp câu hỏi sau,
như thể trích từ tài liệu chính thức. Không cần chính xác 100%,
chỉ cần đúng văn phong và các thuật ngữ liên quan để phục vụ retrieval.

Câu hỏi: {query}

Đoạn trả lời giả định:"""


def hyde_search(
    query: str,
    llm_generate,
    top_k: int = 10,
    num_hypotheses: int = 1,
) -> list[dict]:
    """
    HyDE: dùng LLM sinh (các) tài liệu giả định trả lời câu hỏi,
    rồi embed tài liệu đó thay vì embed câu hỏi thô để search.

    Args:
        query: Câu truy vấn gốc
        llm_generate: callable(prompt: str) -> str, dùng để sinh hypothetical doc.
                      Ví dụ: lambda p: anthropic_client.messages.create(...).content[0].text
        top_k: Số lượng kết quả tối đa
        num_hypotheses: Số hypothetical doc sinh ra. Nếu > 1, các embedding
                        sẽ được trung bình (averaged) trước khi search — đây
                        là cách làm chuẩn trong paper HyDE gốc, giúp giảm
                        nhiễu do 1 lần sinh không ổn định.

    Returns:
        Giống semantic_search(), kèm thêm field 'hyde_doc' để debug.
    """
    try:
        model = get_embedding_model()
        collection = get_collection()
        if collection is None:
            return []
    except Exception as e:
        print(f"Could not perform HyDE search. Have you run the indexing pipeline (Task 4)?")
        print(f"Error: {e}")
        return []

    hypotheses = []
    for _ in range(max(1, num_hypotheses)):
        try:
            hypo_doc = llm_generate(_HYDE_PROMPT_TEMPLATE.format(query=query))
            hypotheses.append(hypo_doc.strip())
        except Exception as e:
            print(f"HyDE generation failed, falling back to raw query. Error: {e}")
            hypotheses.append(query)

    # Embed từng hypothesis rồi trung bình cộng vector (mean pooling)
    vectors = [model.encode(h) for h in hypotheses]
    if len(vectors) == 1:
        query_vector = vectors[0]
    else:
        dim = len(vectors[0])
        query_vector = [
            sum(v[i] for v in vectors) / len(vectors) for i in range(dim)
        ]

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if not results or not results["documents"] or not results["documents"][0]:
        return []

    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        score = max(0.0, 1.0 - dist)
        output.append({
            "content": doc,
            "score": round(score, 4),
            "metadata": meta,
            "hyde_doc": hypotheses[0] if num_hypotheses == 1 else hypotheses,
        })

    output.sort(key=lambda x: x["score"], reverse=True)
    return output


# ---------------------------------------------------------------------------
# Query Expansion — sinh nhiều biến thể query, gộp kết quả (RRF)
# ---------------------------------------------------------------------------
_EXPAND_PROMPT_TEMPLATE = """Cho câu hỏi sau, hãy viết {n} câu hỏi khác có CÙNG Ý NGHĨA
nhưng dùng từ ngữ/cách diễn đạt khác nhau (đồng nghĩa, viết tắt, văn nói/văn viết...).
Chỉ trả về {n} câu hỏi, mỗi câu 1 dòng, không đánh số, không giải thích.

Câu hỏi gốc: {query}"""


def expand_query(query: str, llm_generate, n: int = 3) -> list[str]:
    """Sinh n biến thể của query bằng LLM. Luôn bao gồm cả query gốc."""
    try:
        raw = llm_generate(_EXPAND_PROMPT_TEMPLATE.format(query=query, n=n))
        variants = [line.strip() for line in raw.strip().split("\n") if line.strip()]
    except Exception as e:
        print(f"Query expansion failed, using original query only. Error: {e}")
        variants = []

    all_queries = [query] + variants
    # Loại trùng, giữ thứ tự
    seen = set()
    deduped = []
    for q in all_queries:
        if q.lower() not in seen:
            seen.add(q.lower())
            deduped.append(q)
    return deduped


def multi_query_search(
    query: str,
    llm_generate,
    top_k: int = 10,
    n_expansions: int = 3,
    rrf_k: int = 60,
) -> list[dict]:
    """
    Query Expansion + Reciprocal Rank Fusion (RRF).

    Chạy semantic_search cho query gốc + các biến thể, rồi gộp kết quả
    bằng RRF thay vì trung bình cộng score (score similarity giữa các
    query khác nhau không cùng thang đo nên cộng trực tiếp dễ sai lệch;
    RRF chỉ dựa vào rank nên ổn định hơn).

    RRF score của 1 chunk = sum(1 / (rrf_k + rank_i)) trên mọi query mà
    chunk đó xuất hiện.

    Returns:
        List of {'content', 'score' (RRF score), 'metadata'}, sorted descending.
    """
    queries = expand_query(query, llm_generate, n=n_expansions)

    # content dùng làm key để gộp (giả định content là unique identifier
    # đủ tốt trong phạm vi 1 collection; có thể đổi sang metadata['chunk_id']
    # nếu Task 4 có field đó)
    fused: dict[str, dict] = {}

    for q in queries:
        results = semantic_search(q, top_k=top_k)
        for rank, r in enumerate(results, start=1):
            key = r["content"]
            rrf_contribution = 1.0 / (rrf_k + rank)
            if key not in fused:
                fused[key] = {
                    "content": r["content"],
                    "metadata": r["metadata"],
                    "score": 0.0,
                }
            fused[key]["score"] += rrf_contribution

    output = list(fused.values())
    for r in output:
        r["score"] = round(r["score"], 6)
    output.sort(key=lambda x: x["score"], reverse=True)

    return output[:top_k]


if __name__ == "__main__":
    # Test semantic search thuần
    results = semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

    # --- Ví dụ dùng HyDE / multi-query, cần cắm 1 llm_generate thật ---
    #
    # from anthropic import Anthropic
    # client = Anthropic()
    #
    # def llm_generate(prompt: str) -> str:
    #     msg = client.messages.create(
    #         model="claude-sonnet-4-6",
    #         max_tokens=300,
    #         messages=[{"role": "user", "content": prompt}],
    #     )
    #     return msg.content[0].text
    #
    # hyde_results = hyde_search("quy định trả hàng hoàn tiền shopee", llm_generate, top_k=5)
    # mq_results = multi_query_search("quy định trả hàng hoàn tiền shopee", llm_generate, top_k=5)
