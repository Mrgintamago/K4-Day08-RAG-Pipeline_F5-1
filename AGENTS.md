# AGENTS.md — Ngữ cảnh cho AI coding agent (Nhóm F5, Lab Ngày 8)

File này là **nguồn sự thật dùng chung** cho mọi agent: Codex, Claude Code, Antigravity, Copilot.
Đọc file này trước khi sửa bất kỳ dòng code nào.

---

## Dự án là gì

RAG pipeline tiếng Việt cho chủ đề **chính sách thương mại điện tử & hỗ trợ khách hàng**
(dữ liệu crawl từ trung tâm trợ giúp công khai Shopee Vietnam).
Bài lab có **10 task**, chấm bằng `pytest tests/test_individual.py` (35 test = 50 điểm),
cộng bài nhóm (chatbot Streamlit + đánh giá RAGAS).

Kế hoạch đầy đủ, phân công, lịch checkpoint: đọc **`PLAN.md`**.

---

## Môi trường

- **Python 3.12 bắt buộc** trong `.venv/`. Python 3.13/3.14 chưa có wheel torch/chromadb.
- Luôn chạy bằng `.\.venv\Scripts\python.exe`, KHÔNG dùng `python` toàn cục.
- Windows + PowerShell. Đặt `$env:PYTHONIOENCODING="utf-8"` và chạy `python -X utf8`
  cho mọi script in tiếng Việt, nếu không sẽ `UnicodeEncodeError`.
- Chạy module bằng `-m`: `.\.venv\Scripts\python.exe -X utf8 -m src.task4_chunking_indexing`
  (KHÔNG `python src/task4_chunking_indexing.py` — sẽ lỗi import `src.`).

---

## LUẬT CỨNG — vi phạm là hỏng bài của người khác

1. **KHÔNG đổi chữ ký hàm** đã chốt trong `PLAN.md` §3.2. Cả nhóm code song song dựa vào đó.
   Muốn đổi → báo người trong nhóm trước, không tự sửa.
2. **KHÔNG sửa `tests/test_individual.py`.** Đây là file chấm điểm. Code phải chạy đúng theo test,
   không phải sửa test cho vừa code.
3. **KHÔNG commit**: `.env`, `chroma_db/`, `.venv/`, `__pycache__/`, file fixture tạm.
4. **KHÔNG hardcode API key.** Luôn `os.getenv("OPENROUTER_API_KEY")` qua `python-dotenv`.
5. **KHÔNG sửa file ngoài phạm vi ticket đang làm.** Mỗi người một file, sửa lung tung là conflict.
6. **KHÔNG đổi 3 hằng số đã chốt**: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, `SCORE_THRESHOLD=0.48`.

---

## Hợp đồng dữ liệu

Mọi hàm retrieval (Task 5, 6, 7, 8, 9) trả về **cùng một shape**, sorted theo `score` giảm dần,
độ dài ≤ `top_k`:

```python
{
    "content":  str,    # nội dung chunk
    "score":    float,  # điểm của ranker
    "metadata": dict,   # {"source", "title", "customer_role", "url", ...}
    # Task 8 bắt buộc thêm:
    "source":   "pageindex",
}
```

Chữ ký hàm bất biến:

```python
semantic_search(query: str, top_k: int = 10) -> list[dict]
lexical_search(query: str, top_k: int = 10) -> list[dict]
rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]
rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "rrf") -> list[dict]
pageindex_search(query: str, top_k: int = 5) -> list[dict]
retrieve(query, top_k=5, score_threshold=0.48, use_reranking=True) -> list[dict]
reorder_for_llm(chunks: list[dict]) -> list[dict]
format_context(chunks: list[dict]) -> str
generate_with_citation(query: str, top_k: int = 5) -> dict  # {"answer","sources","retrieval_source"}
```

---

## 2 cái bẫy đã biết — đừng để agent viết sai

### 1. Ngưỡng fallback ở Task 9

So `score_threshold` với **điểm cosine gốc** `dense_results[0]["score"]` (thang `[0,1]`),
**KHÔNG** so với điểm RRF đã fuse. Điểm RRF top-1 luôn ≈ `1/(60+1)` ≈ 0.016, nên nếu so nhầm
thì fallback **không bao giờ trigger**, kể cả query hoàn toàn lạc đề.

```python
# ĐÚNG
dense = semantic_search(query, top_k=10)
best_cosine = dense[0]["score"] if dense else 0.0
if best_cosine < score_threshold:
    return pageindex_search(query, top_k=top_k)

# SAI
merged = rerank_rrf([dense, sparse])
if merged[0]["score"] < score_threshold:   # điểm RRF ≈ 0.016, luôn < threshold hoặc vô nghĩa
    ...
```

### 2. Test dùng `skipTest`

Chưa implement thì test **SKIP chứ không FAIL**. `1 passed, 3 skipped` **không phải là xong**.
Sau khi sửa code phải kiểm tra test thật sự `passed`, không phải `skipped`.

---

## Quy trình bắt buộc sau khi sửa code

```powershell
$env:PYTHONIOENCODING="utf-8"

# 1. Test riêng task vừa sửa
.\.venv\Scripts\python.exe -m pytest tests/test_individual.py::TestTask6 -v

# 2. Test toàn bộ — không được làm hỏng phần người khác
.\.venv\Scripts\python.exe -m pytest tests/test_individual.py -v

# 3. Kiểm tra không lọt file cấm
git status
```

Chỉ báo "xong" khi test **passed** (không phải skipped) và đã chạy smoke test ở `PLAN.md` §7.3.

---

## Phong cách code

- Comment và docstring **bằng tiếng Việt** (đồng bộ với starter).
- Giữ nguyên cấu trúc file starter, chỉ điền vào chỗ `# TODO:` và thay `raise NotImplementedError`.
- Với mỗi lựa chọn kỹ thuật (chunk size, embedding model, top_p, threshold) phải **ghi lý do
  vào comment** — đây là tiêu chí chấm điểm trong `README.md`.
- Không thêm dependency mới nếu `requirements.txt` đã có thứ dùng được.
  Thêm mới → phải báo cả nhóm vì mọi người phải cài lại.
