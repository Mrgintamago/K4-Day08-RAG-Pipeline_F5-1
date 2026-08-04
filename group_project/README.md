# Bài Tập Nhóm — ⚖️ Trợ Lý Pháp Lý Khởi Nghiệp & Thương Mại Điện Tử

> Chủ đề **#2** trong [`../SUGGESTED_TOPICS.md`](../SUGGESTED_TOPICS.md).
> Tên tiếng Anh dùng cho deploy: **E-commerce & Startup Legal Assistant**.

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

**🚀 Demo:** https://hf-space-gu9frvc2ksareqt4amdfe2.streamlit.app

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
           Task 4 — chunk 800/overlap 100 + MiniLM đa ngữ 384d ──► chroma_db/
                    (1.216 chunk, đã commit sẵn trong repo)
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
        Task 5 semantic_search()                            Task 6 lexical_search()
        dense / cosine / + HyDE                             sparse / BM25
                     └──────────────────────────┬──────────────────────────┘
                                                ▼
                              Task 7 — RRF rerank, k=60
                                                ▼
                     Task 9 — retrieve(): cosine gốc < 0.40 ?
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

## Giải Thích Kiến Trúc — 6 Quyết Định Thiết Kế

### 1. Corpus 2 lớp thay vì 1 nguồn

| Lớp | Trả lời câu hỏi | Nguồn | Số file |
|-----|-----------------|-------|---------|
| Văn bản luật | *"Pháp luật bắt tôi làm gì?"* | vi.wikisource.org | 5 |
| Quy định sàn | *"Shopee bắt tôi làm gì?"* | help.shopee.vn | 26 |

Người bán online chịu **hai tầng ràng buộc độc lập**. Chỉ có luật thì không trả lời được "Shopee cấm bán gì"; chỉ có quy định sàn thì không trả lời được "doanh thu bao nhiêu phải nộp thuế". Metadata `doc_type` giữ ranh giới này để chatbot in rõ **PHÁP LUẬT** hay **QUY ĐỊNH SÀN** — khác biệt có ý nghĩa pháp lý thật.

**Nguồn đã thử và loại:** PDF trên `datafiles.chinhphu.vn` là ảnh scan (MarkItDown trích ra **0 ký tự**); `thuvienphapluat.vn` chặn bot (403); `luatvietnam.vn` paywall; `vbpl.vn` chuyển sang SPA. Wikisource có toàn văn dạng text + API công khai, và văn bản QPPL Việt Nam thuộc phạm vi công cộng (Điều 15 Luật SHTT).

### 2. Chunk 800 / overlap 100

Văn bản chính sách có đoạn dài. Mức 500 hay cắt giữa câu điều kiện *"nếu… thì…"* làm mất vế sau. 800 ký tự giữ trọn 1–2 điều khoản. Overlap 100 (12,5%) đủ để câu bị cắt ở ranh giới vẫn xuất hiện nguyên vẹn ở một trong hai chunk.

**Lọc chunk rác trước khi index.** Đo thực tế: chunk chân trang (khối chữ ký + "Liên hệ:") **đứng TOP-1** cho câu hỏi "hồ sơ đăng ký hộ kinh doanh". Chunk ngắn không có chủ đề rõ nằm giữa không gian vector nên "trung tính" với mọi query — vừa đẩy chunk hữu ích ra khỏi top-k, vừa kéo điểm câu lạc đề lên làm hỏng ngưỡng fallback. Loại 8 chunk như vậy: 1.224 → **1.216 chunk**.

### 3. Embedding: MiniLM đa ngữ 384 chiều

`paraphrase-multilingual-MiniLM-L12-v2` thay vì `BAAI/bge-m3` (1024 chiều): nhẹ hơn 4,5 lần (470MB vs 2,2GB), embed 1.216 chunk trong **~40 giây** thay vì 15–25 phút.

Đánh đổi được ghi nhận: chất lượng tiếng Việt kém hơn, thấy rõ ở `evaluation/results.md`. Đổi provider chỉ cần sửa `EMBEDDING_PROVIDER` trong `.env` (`sentence_transformers` | `google` | `openai`) — `embed_texts()` dispatch chung cho cả Task 4 và Task 5 nên không phải sửa code hai nơi.

### 4. Hybrid retrieval — vì sao cần cả hai nhánh

Corpus có hai loại câu hỏi khác hẳn nhau:
- *"Điều 33 Luật Doanh nghiệp quy định gì?"* → **BM25 thắng**, cần khớp chính xác số hiệu
- *"Bán online bao nhiêu thì đóng thuế?"* → **semantic thắng**, không có từ khoá trùng

RRF (k=60) gộp theo **thứ hạng** chứ không theo điểm, nên không phải chuẩn hoá hai thang điểm khác nhau về chung một đơn vị.

Kết quả A/B xác nhận: hybrid + rerank **+0,158 điểm trung bình** so với dense-only ([`evaluation/results.md`](evaluation/results.md)).

### 5. Fallback vectorless — chỗ dễ sai nhất

```python
dense = semantic_search(query, top_k*2)
best_cosine = dense[0]["score"]        # ← CHỤP TRƯỚC khi gộp
merged = rerank_rrf([dense, sparse])   # score bị ghi đè thành điểm RRF
if best_cosine < 0.40:                 # so bằng cosine, KHÔNG phải RRF
    return pageindex_search(query, top_k)
```

Sau `rerank_rrf()`, trường `score` mang điểm RRF ≈ `1/(60+1)` ≈ **0,016** — chỉ phản ánh thứ hạng, không phản ánh độ liên quan. So threshold với điểm đó thì **mọi query, kể cả câu vô nghĩa, đều cho cùng một khoảng điểm** và fallback không bao giờ đúng.

**Ngưỡng 0,40 calibrate từ số đo thật**, không lấy giá trị mẫu:

| Loại query | cosine top-1 |
|---|---|
| Đúng chủ đề | 0,444 – 0,531 |
| Lạc đề (thời tiết, nấu phở) | 0,265 – 0,365 |

Giá trị mẫu 0,48 của LAB_GUIDE hợp với thang điểm bge-m3; dùng cho MiniLM thì câu **đúng** chủ đề (0,444) cũng rơi nhầm xuống fallback.

### 6. Hạ cấp êm ở mọi tầng

Pipeline phụ thuộc 3 module của 3 người + 1 API ngoài. Mỗi tầng đều có đường lui:

| Tầng | Khi hỏng | Hành vi |
|------|----------|---------|
| `semantic_search` / `lexical_search` | `_safe_search()` nuốt lỗi | Chạy tiếp bằng nhánh còn lại |
| PageIndex | Hết quota (free tier chỉ 3 tài liệu) | Fallback cục bộ: duyệt heading `.md`, chấm điểm phủ từ khoá — vẫn đúng tinh thần vectorless, không dùng embedding |
| Crawl4AI | Thiếu Chromium | Tự chuyển sang `requests` (trang có SSR nên không cần trình duyệt) |

Một nhánh hỏng mà sập cả `retrieve()` thì kéo luôn Task 10 và chatbot.

---

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
