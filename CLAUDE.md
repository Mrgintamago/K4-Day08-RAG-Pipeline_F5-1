# CLAUDE.md

Toàn bộ ngữ cảnh, luật cứng, hợp đồng interface và quy trình test của dự án nằm ở
**[`AGENTS.md`](AGENTS.md)** — đọc file đó trước khi sửa code.

Kế hoạch, phân công và lịch checkpoint: **[`PLAN.md`](PLAN.md)**.

Tóm tắt 5 điều dễ sai nhất:

1. Chạy bằng `.\.venv\Scripts\python.exe -X utf8 -m src.<module>` (Python 3.12, không phải `python`).
2. Không đổi chữ ký hàm ở `PLAN.md` §3.2, không sửa `tests/test_individual.py`.
3. Task 9: so `score_threshold` với **cosine gốc** `dense_results[0]["score"]`, không phải điểm RRF.
4. Test `skipped` ≠ `passed` — chưa implement thì test tự skip, đừng tưởng là xong.
5. Hằng số đã chốt: `CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`, `SCORE_THRESHOLD=0.48`.
