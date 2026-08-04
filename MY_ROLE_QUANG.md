# Trách Nhiệm Của Tôi — Nguyễn Xuân Quang (2A202601776)

**Role 1 — Team Leader & Data/Pipeline**
Nhóm F5 · Ngày 8: RAG Pipeline v2 · Phương Án A (nhóm 4 người)

> File này là bản mô tả vai trò **của riêng tôi**. Kế hoạch chung của cả nhóm: [`PLAN.md`](PLAN.md).

---

## 1. Tôi chịu trách nhiệm gì

Vai trò của tôi có **2 phần tách biệt**, đừng nhầm lẫn:

| Phần | Nội dung | Nếu tôi hỏng thì sao |
|------|----------|----------------------|
| **A. Dữ liệu & Pipeline** (việc kỹ thuật) | Task 1, 2, 3, 8, 9 | Không có data → cả 3 người còn lại ngồi chơi |
| **B. Điều phối & Chốt bài** (việc quản lý) | Chốt hằng số, review PR, gác interface, nộp bài | Code chạy được nhưng nhóm không ghép được thành 1 sản phẩm |

Tôi là **người duy nhất chạm vào cả hai đầu pipeline**: đầu vào (thu thập dữ liệu) và
đầu ra (ghép thành `retrieve()` rồi đưa cho Hân). Vì thế tôi phải hiểu cả bức tranh,
không chỉ phần mình gõ.

---

## 2. Ticket của tôi

| Ticket | Nội dung | Điểm | Chặn ai | Trạng thái |
|--------|----------|------|---------|-----------|
| F5-0 | Chốt 3 hằng số (800 / 100 / 0.48) | — | T (F5-4), tôi (F5-9) | ✅ |
| F5-1 | Task 1 — thu thập văn bản chính sách + luật | 3 | F5-3 | ✅ 13 file |
| F5-2 | Task 2 — crawl bài hướng dẫn | 3 | F5-3 | ✅ 18 file |
| F5-3 | Task 3 — convert markdown | 4 | **T, S** | ✅ 31 file `.md` |
| F5-8 | Task 8 — PageIndex vectorless | 4 | F5-9 | ✅ 3 doc trên PageIndex |
| **F5-9** | **Task 9 — `retrieve()` + fallback** | **7** | **H (F5-10)** | ⬜ **chờ F5-5,6,7** |
| — | Tích hợp pipeline vào `app.py` | 4 | — | ⬜ |
| — | Viết kiến trúc + phân công 2 README | 3 | — | 🟡 đã viết, chờ chốt |
| F5-16 | ⭐ Bonus deploy HF Spaces | 4 | — | ⬜ |
| F5-17 | Chốt nộp: pytest 35/35 + dọn repo | — | — | ⬜ |

**Tổng điểm tôi gánh: 21 (Task 1–10) + 7 (bài nhóm) + 4 (bonus) = 32/100.**

---

## 3. Việc kỹ thuật khó nhất của tôi: F5-9

Đây là ticket 7 điểm và là chỗ **dễ mất điểm nhất cả bài**.

```python
def retrieve(query, top_k=5, score_threshold=0.48, use_reranking=True):
    dense  = semantic_search(query, top_k=10)     # của Tường
    sparse = lexical_search(query, top_k=10)      # của Sáng
    merged = rerank_rrf([dense, sparse], top_k=top_k)   # của Sáng

    # ↓↓↓ DÒNG QUYẾT ĐỊNH 7 ĐIỂM ↓↓↓
    best_cosine = dense[0]["score"] if dense else 0.0
    if best_cosine < score_threshold:
        return pageindex_search(query, top_k=top_k)     # của tôi (F5-8)
    return merged[:top_k]
```

**Cái bẫy:** so `score_threshold` với điểm RRF đã fuse thay vì cosine gốc.
Điểm RRF của top-1 luôn ≈ `1/(60+1)` ≈ **0.016**, tức là **luôn nhỏ hơn 0.48** —
hoặc ngược lại nếu so kiểu khác thì fallback **không bao giờ chạy**, kể cả với câu hỏi
hoàn toàn lạc đề. Cả `README.md` lẫn `LAB_GUIDE.md` đều cảnh báo riêng về bẫy này,
nghĩa là **giám khảo sẽ soi đúng chỗ đó**.

Cách tôi tự kiểm tra:
```powershell
.\.venv\Scripts\python.exe -X utf8 -c "from src.task9_retrieval_pipeline import retrieve; print(retrieve('thoi tiet Ha Noi hom nay',3)[0].get('source'))"
```
Phải in ra `pageindex`. In ra `None` hoặc `hybrid` = tôi đang so sai điểm.

**Thêm việc bắt buộc:** sau khi Tường index xong, tôi phải **calibrate lại `SCORE_THRESHOLD`**.
0.48 chỉ là giá trị khởi điểm theo LAB_GUIDE. Cách làm: chạy `semantic_search()` với 3 câu
đúng chủ đề và 3 câu lạc đề, xem cosine top-1 rơi vào 2 khoảng nào, đặt ngưỡng vào giữa.
Nếu Tường đổi embedding model (MiniLM 384d thay vì bge-m3 1024d) thì **thang điểm khác hẳn,
bắt buộc đo lại**.

---

## 4. Việc điều phối — phần dễ bị bỏ quên

Đây là phần không có dòng code nào nhưng hỏng thì cả nhóm hỏng.

### 4.1. Gác hợp đồng interface

`PLAN.md` §3.2 liệt kê chữ ký hàm mà 4 người cùng dựa vào. **Tôi là người duy nhất được
duyệt việc đổi chữ ký.** Ai đổi lén → PR của 2 người khác đỏ mà không hiểu vì sao.

Khi review PR, kiểm đúng 6 thứ (checklist đầy đủ ở `PLAN.md` §7.4):
1. `pytest` không FAIL, số `passed` không giảm so với `main`
2. Ticket của PR đó **không còn `skipped`** — nhớ: `skipped` ≠ `passed`
3. Không đổi chữ ký hàm ở §3.2
4. Không commit `.env`, `chroma_db/`, `.venv/`
5. 3 hằng số vẫn là 800 / 100 / 0.48
6. Có dán output smoke test vào PR

### 4.2. Canh 3 nút thắt

| Nút thắt | Ai kẹt | Tôi làm gì khi thấy trễ |
|----------|--------|-------------------------|
| **F5-4** (Tường, ChromaDB) | Chặn cả T lẫn S | Ép Tường đổi sang MiniLM/Google ngay, đừng chờ `bge-m3` |
| **F5-9** (tôi) | Chặn Hân | Bảo Hân mock `retrieve()` bằng fixture giả, ghép thật sau |
| **F5-13** (Sáng, RAGAS) | Mất 12đ | Bảo Sáng dựng khung `eval_pipeline.py` với hàm giả từ CP4 |

### 4.3. Chốt cứng ở CP4

Nếu tới CP4 mà chưa `35/35 passed` → **tôi ra lệnh cả 4 người dừng việc riêng**, gộp sức
fix cho đủ mốc 50đ rồi mới quay lại. Bonus 20đ không bao giờ được ưu tiên hơn Task 1–10.

### 4.4. Chia sẻ API key

`OPENROUTER_API_KEY` và `PAGEINDEX_API_KEY` do tôi giữ và chia sẻ qua kênh riêng.
**Không bao giờ commit** — kể cả vào `.env.example` (file đó được đẩy lên GitHub công khai).

---

## 5. Những gì tôi đã làm và cần giải thích được khi bị hỏi

Coach có thể gọi bất kỳ ai. Đây là các quyết định của tôi và lý do — **phải tự nói được**:

| Quyết định | Lý do |
|-----------|-------|
| Crawl bằng `requests` chứ không phải Crawl4AI | `help.shopee.vn` có server-side rendering, dữ liệu bài viết nằm sẵn trong `window["FORGE_SSR_DATA_MAP"]`. Parse thẳng khối JSON đó cho text sạch, không cần Chromium. Vẫn giữ cờ `--crawl4ai` để dùng AsyncWebCrawler khi cần. |
| Không dùng PDF từ `vanban.chinhphu.vn` | PDF "bản ký số" ở đó là **ảnh scan**, MarkItDown trích ra **0 ký tự** → không chunk/embed được, còn làm Task 3 sinh `.md` rỗng khiến test fail. |
| Dùng Wikisource cho văn bản luật | Có toàn văn dạng text + API MediaWiki công khai. Văn bản QPPL Việt Nam thuộc **phạm vi công cộng** (Điều 15 Luật SHTT). Đã thử và loại: `thuvienphapluat.vn` 403 Cloudflare, `luatvietnam.vn` paywall, `vbpl.vn` đổi sang SPA, `congbao.chinhphu.vn` chỉ có metadata. |
| News không đi qua MarkItDown | File JSON từ Task 2 đã chứa text sạch rồi, đưa qua converter chỉ thêm bước thừa. |
| Bỏ khối metadata lặp trong PDF (Task 3) | Task 1 in metadata vào đầu trang PDF, MarkItDown trích ra lại trùng với header `.md`. Để nguyên thì chunk đầu mỗi tài liệu chứa URL lặp, làm nhiễu điểm BM25 ở Task 6. |
| PageIndex chỉ upload 3 tài liệu | Gói free trả `{"detail":"LimitReached"}` từ file thứ 4. Chọn 3 tài liệu có **cấu trúc chương/mục rõ nhất** vì đó đúng thế mạnh của PageIndex (duyệt cây cấu trúc, không cần embedding). |
| PageIndex gán `score = 1/rank` | PageIndex **không trả score** — nó chỉ trả các node LLM cho là liên quan. Gán điểm theo thứ hạng để sort/cắt `top_k` được như mọi ranker khác. **Điểm này không so sánh trực tiếp với cosine được** — đó là lý do ngưỡng 0.48 chỉ áp cho `semantic_search`. |
| `CHUNK_SIZE=800`, `OVERLAP=100` | Starter để 500/50 nhưng LAB_GUIDE yêu cầu 800/100. 800 giữ trọn 1–2 điều khoản trong cùng chunk (500 hay cắt giữa câu "nếu... thì..."). Overlap 12.5% đủ để câu bị cắt vẫn trọn vẹn ở một trong hai chunk. |
| `SCORE_THRESHOLD=0.48` | Theo LAB_GUIDE, **và phải calibrate lại** sau khi index xong — xem §3. |

---

## 6. Checklist theo checkpoint — chỉ phần của tôi

- [x] **CP0** — Sửa 3 hằng số, push `main`, chia sẻ API key
- [x] **CP1** — F5-1, F5-2, F5-3 (31 file `.md`)
- [x] **CP2/CP3** — F5-8 PageIndex (3 doc, `TestTask8` 2/2)
- [ ] **CP4** — F5-9 `retrieve()` + calibrate threshold + chạy `pytest` chốt **35/35**
- [ ] **CP5** — Ghép `retrieve()` + `generate_with_citation()` vào `app.py`; viết 4 câu golden dataset nhóm "Thành lập & đăng ký KD"; chốt mục kiến trúc trong 2 README
- [ ] **CP6** — Dọn repo, `pytest` lại trên `main`, push; ⭐ deploy HF Spaces nếu 50đ đã an toàn

---

## 7. Việc kế tiếp của tôi ngay lúc này

1. **Viết 4 câu golden dataset** nhóm "Thành lập & đăng ký kinh doanh" (không chờ ai) —
   evidence lấy từ `luat-doanh-nghiep-2020.md`.
2. **Giục Tường chốt embedding provider** — F5-4 đang chặn 2 người, corpus 1.081 chunk
   mà dùng `bge-m3` là mất 15–25 phút (bảng so sánh ở `PLAN.md` §1.5).
3. **Khi F5-5, F5-6, F5-7 merge xong** → làm F5-9 ngay, đây là đường găng của cả nhóm.

**Trạng thái hiện tại:** `pytest` **14 passed, 21 skipped** · Task 1, 2, 3, 8 xong (14/50đ).
