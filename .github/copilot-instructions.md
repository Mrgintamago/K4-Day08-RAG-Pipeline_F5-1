# GitHub Copilot — hướng dẫn cho repo này

Ngữ cảnh đầy đủ ở [`AGENTS.md`](../AGENTS.md), kế hoạch ở [`PLAN.md`](../PLAN.md).

## Bối cảnh

RAG pipeline tiếng Việt về chính sách thương mại điện tử (dữ liệu Shopee help center).
10 task, chấm bằng `pytest tests/test_individual.py`. Comment/docstring viết **tiếng Việt**.

## Luật cứng

- Python **3.12** trong `.venv/`. Chạy: `.\.venv\Scripts\python.exe -X utf8 -m src.<module>`.
- **Không đổi chữ ký hàm** đã chốt (xem `AGENTS.md` mục "Hợp đồng dữ liệu").
- **Không sửa** `tests/test_individual.py` — đó là file chấm điểm.
- **Không hardcode API key** — dùng `os.getenv()` + `python-dotenv`.
- **Không commit** `.env`, `chroma_db/`, `.venv/`.
- Hằng số đã chốt: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, `SCORE_THRESHOLD=0.48`.

## Shape dữ liệu chung của mọi hàm retrieval

```python
{"content": str, "score": float, "metadata": dict}   # sorted theo score giảm dần, len <= top_k
# Task 8 (pageindex_search) thêm: "source": "pageindex"
```

## Bẫy quan trọng nhất

Task 9 fallback: so `score_threshold` với **điểm cosine gốc** `dense_results[0]["score"]`,
**không** so với điểm RRF đã fuse (RRF top-1 luôn ≈ 0.016 → fallback không bao giờ chạy).

## Sau khi sinh code

Luôn chạy `.\.venv\Scripts\python.exe -m pytest tests/test_individual.py -v` và kiểm tra
test thật sự **passed**, không phải **skipped**.
