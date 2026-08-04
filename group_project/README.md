# Bài Tập Nhóm — ⚖️ Trợ Lý Pháp Lý Khởi Nghiệp & Thương Mại Điện Tử

> Chủ đề **#2** trong [`../SUGGESTED_TOPICS.md`](../SUGGESTED_TOPICS.md).
> Tên tiếng Anh dùng cho deploy: **E-commerce & Startup Legal Assistant**.

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot tra cứu quy định pháp lý khi bán hàng online: nghĩa vụ thuế, đăng ký hộ kinh doanh / thành lập công ty, quy định đăng bán trên sàn TMĐT, quyền người tiêu dùng.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

Xem code mẫu (DeepEval/RAGAS/TruLens) chi tiết trong `README.md` gốc mục "Yêu cầu 2".

### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống

**Chủ đề: #2 trong `SUGGESTED_TOPICS.md` — Trợ Lý Pháp Lý Khởi Nghiệp & TMĐT.**
Corpus 31 file / 865k ký tự, 2 lớp: **văn bản luật** (Wikisource, 5 file) trả lời
"pháp luật bắt tôi làm gì" + **quy định sàn** (Shopee, 26 file) trả lời "sàn bắt tôi làm gì".

```
vi.wikisource.org ─► Task 1 (5 luật toàn văn) ─┐
help.shopee.vn ───► Task 1 (8 PDF quy định) ───┤
                    Task 2 (18 JSON hướng dẫn) ┤ data/landing/
                                                ▼
                                Task 3 — MarkItDown ──► data/standardized/*.md
                                                ▼
                     Task 4 — chunk 800/overlap 100 + BAAI/bge-m3 ──► chroma_db/
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
        Task 5 semantic_search()                            Task 6 lexical_search()
        dense / cosine / HyDE                               sparse / BM25 + TF-IDF
                     └──────────────────────────┬──────────────────────────┘
                                                ▼
                              Task 7 — RRF rerank, k=60
                                                ▼
                     Task 9 — retrieve(): cosine gốc < 0.48 ?
                              ├─ không → kết quả hybrid
                              └─ có    → Task 8 PageIndex vectorless fallback
                                                ▼
                     Task 10 — reorder (front + back[::-1]) → LLM → citation
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
              app.py (Streamlit chatbot)          eval_pipeline.py (RAGAS, A/B test)
```

> Chi tiết kế hoạch, lịch checkpoint và bản đồ điểm: xem [`../PLAN.md`](../PLAN.md).

---

## Phân Công Công Việc

Theo `LAB_GUIDE.md` — **Phương Án A: nhóm 4 thành viên**.

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| Nguyễn Xuân Quang | 2A202601776 | **Role 1 — Team Leader & Data/Pipeline**: Task 1–2 (thu thập + crawl), Task 3 (convert markdown), Task 8 (PageIndex vectorless), Task 9 (retrieval pipeline + fallback), tích hợp vào `app.py`, review PR, deploy | 🟡 Task 1–2 xong |
| Cao Các Tường | 2A202601236 | **Role 2 — Vector DB & Dense Search**: Task 4 (chunking 800/100 + ChromaDB + `bge-m3`), Task 5 (semantic search), bonus HyDE / Query Expansion | ⬜ Đang làm |
| Lưu Nguyễn Ngọc Hân | 2A202601386 | **Role 3 — Generation & Frontend**: Task 10 (generation có citation + reorder), `app.py` Streamlit UI, bonus conversation memory + hiển thị source/score | ⬜ Đang làm |
| Trần Quang Sáng | 2A202601446 | **Role 4 — Sparse Search & Evaluation**: Task 6 (BM25 + TF-IDF), Task 7 (RRF rerank), `eval_pipeline.py` RAGAS 4 metric + A/B, `results.md` | ⬜ Đang làm |

**Việc chung:** `golden_dataset.json` (16 câu) — mỗi người viết 4 câu từ tài liệu đã crawl, Sáng gộp thành 1 file.

**Cân đối khối lượng** (Task 1–10 / bài nhóm / bonus): Q 21/7/4 · T 13/0/5 · H 4/11/6 · S 12/9/5.
Chi tiết: [`../PLAN.md` §8](../PLAN.md).

---

## Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
streamlit run app.py
# hoặc
chainlit run app.py
```

---

## Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
