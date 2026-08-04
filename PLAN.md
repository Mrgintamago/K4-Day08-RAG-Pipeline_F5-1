# PLAN — Ngày 8: RAG Pipeline v2 (Nhóm F5)

**Chủ đề: ⚖️ Trợ Lý Pháp Lý Khởi Nghiệp & Thương Mại Điện Tử** (#2 trong `SUGGESTED_TOPICS.md`)

---

## 📊 BẢNG TIẾN ĐỘ — cập nhật mỗi lần merge

> **Cách dùng:** ai merge PR xong thì sửa đúng 1 ô trạng thái trong bảng này rồi push kèm.
> Đừng sửa chỗ khác — bảng này là chỗ duy nhất cả nhóm nhìn để biết đang ở đâu.

### Điểm đã chắc

```
Task 1-10 :  ███████████████░░░░░  37 / 50 điểm
Bài nhóm  :  ██░░░░░░░░░░░░░░░░░░   3 / 30 điểm   (golden dataset)
Bonus     :  ░░░░░░░░░░░░░░░░░░░░   0 / 20 điểm
pytest    :  27 passed · 8 skipped · 0 failed      (mốc cần: 35 passed)
```

**Còn thiếu 13đ = Task 6 (6) + Task 9 (7).** `chroma_db/` đã có **1.216 chunk** → F5-6 hết vật cản.

### 📈 Số đo retrieval (dùng cho F5-9 calibrate ngưỡng)

Đo trên index thật sau khi lọc chunk rác:

| Loại query | cosine top-1 |
|---|---|
| Đúng chủ đề (thuế, đăng ký KD, sản phẩm cấm) | **0,444 – 0,531** |
| Lạc đề (thời tiết, nấu phở) | **0,265 – 0,365** |

→ **`SCORE_THRESHOLD` nên đặt ~0,40**, không phải 0,48 như giá trị khởi điểm của LAB_GUIDE.
Đặt 0,48 thì câu đúng chủ đề cũng rơi xuống fallback. Quang chốt lại khi làm F5-9.

### Ticket

| Ticket | Việc | Ai | Điểm | Trạng thái |
|--------|------|----|------|-----------|
| F5-00 | Setup môi trường | cả 4 | — | 🟡 Q/H/S xong · **T chưa xác nhận** |
| F5-0 | Chốt 3 hằng số | Q | — | ✅ |
| F5-1 | Task 1 — 13 văn bản PDF | Q | 3 | ✅ |
| F5-2 | Task 2 — 18 bài JSON | Q | 3 | ✅ |
| F5-3 | Task 3 — 31 file `.md` | Q | 4 | ✅ |
| F5-4 | Task 4 — chunking + ChromaDB | T | 7 | ✅ **1.216 chunk**, 4/4 test passed |
| F5-5 | Task 5 — semantic search | T | 6 | ✅ 4/4 test passed |
| **F5-6** | **Task 6 — lexical BM25** | **S** | **6** | 🟢 **hết vật cản — làm được ngay** |
| F5-7 | Task 7 — RRF rerank | S | 6 | ✅ 3/3 test passed |
| F5-8 | Task 8 — PageIndex | Q | 4 | ✅ 3 doc trên PageIndex |
| **F5-9** | **Task 9 — retrieve + fallback** | **Q** | **7** | ⬜ chỉ còn chờ **F5-6** |
| F5-10 | Task 10 — generation | H | 4 | ✅ 3/3 test passed |
| F5-11 | `app.py` chatbot | H | 8 | 🟢 **làm được ngay** (F5-10 xong rồi) |
| F5-12 | Golden dataset 16 câu | S | 3 | ✅ 16 câu, đủ 3 trường |
| F5-13 | RAGAS eval + `results.md` | S | 9 | 🟡 scaffold 418 dòng · chờ pipeline thật để chạy |
| ⭐ F5-14 | Bonus HyDE | T | 5 | 🔒 khoá đến khi xong 50đ |
| ⭐ F5-15 | Bonus memory + UI | H | 6 | 🔒 khoá đến khi xong 50đ |
| ⭐ F5-16 | Bonus deploy HF | Q | 4 | 🔒 khoá đến khi xong 50đ |
| F5-17 | Chốt nộp | Q | — | ⬜ |

Ký hiệu: ✅ xong · 🟡 đang làm · 🟢 làm được ngay, không chờ ai · ⬜ chờ ticket khác ·
🔴 đang chặn người khác · 🔒 chưa được phép làm · ⭐ bonus

### Ai đang làm gì

| | Đã xong | Đang làm | Kế tiếp |
|---|---|---|---|
| **Q** Quang | F5-0, 1, 2, 3, 8 — **14đ** | 4 câu golden dataset | **F5-9** (chỉ chờ F5-6) |
| **T** Tường | F5-4, F5-5 — **13đ** | — | ⭐F5-14 sau khi đủ 50đ |
| **H** Hân | F5-10 — **4đ** | F5-11 `app.py` | ⭐F5-15 sau khi đủ 50đ |
| **S** Sáng | F5-7, F5-12 — **6đ + 3đ** | **F5-6 🔴 đường găng** | F5-13 chạy A/B thật |

### 🚨 Đang chặn tiến độ

**F5-6 của Sáng.** `chroma_db/` đã có 1.216 chunk nên F5-6 hết vật cản — nhưng nó là
ticket cuối cùng chặn **F5-9 (7đ)**, và F5-9 lại chặn phần chạy thật của **F5-13 (9đ)**.
Nghĩa là 1 ticket đang khoá 13/50 điểm còn lại cộng 9 điểm bài nhóm.

Thứ tự đúng: **F5-6 (S) → F5-9 (Q) → F5-13 chạy A/B (S)**.

### ⚠️ Chất lượng retrieval — cần biết trước khi làm F5-6 và F5-13

Model đang dùng là `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều), chọn vì đã có sẵn
trong cache và embed 1.216 chunk chỉ mất ~40 giây. Đánh đổi: **chất lượng tiếng Việt ở mức
trung bình** — với câu "sản phẩm nào bị cấm đăng bán", chunk đứng đầu vẫn là một đoạn liệt kê
tên shop chứ không phải điều khoản cấm.

Hệ quả cần lường trước:
- **F5-6 (BM25) nhiều khả năng thắng semantic** ở câu hỏi có số hiệu điều luật
  ("Điều 33", "Luật số 59/2020/QH14") — đây là luận điểm tốt cho phân tích A/B của F5-13.
- **Điểm RAGAS context_precision sẽ không cao.** Đừng hoảng, hãy ghi vào `results.md`
  như một phát hiện có căn cứ, kèm đề xuất cải tiến: đổi sang `BAAI/bge-m3` (1024 chiều,
  chuyên đa ngữ) — chỉ cần sửa `EMBEDDING_MODEL` + `EMBEDDING_DIM` rồi xoá `chroma_db/`
  và chạy lại Task 4. Đây chính là **cấu hình thứ 3 cho A/B test**, đáng giá điểm phân tích.

---

> ## 🔴 ĐỌC TRƯỚC — Đổi chủ đề, ai bị ảnh hưởng gì
>
> **Chủ đề mới:** #2 trong `SUGGESTED_TOPICS.md` — **"Trợ lý Pháp lý Khởi nghiệp & TMĐT"**
> (tra cứu quy định khi bán hàng online, đăng ký hộ kinh doanh, nghĩa vụ thuế).
> Chủ đề cũ (hỗ trợ khách hàng Shopee) là **tập con** của chủ đề mới, nên **không ai phải làm lại từ đầu.**
>
> | Role | Có bị ảnh hưởng? | Phải làm gì khác |
> |------|------------------|------------------|
> | **Q — Quang** | ✅ Đã xử lý xong | Task 1–3 crawl lại xong rồi, không còn việc tồn |
> | **T — Tường** | ⚠️ **CÓ — đọc mục [1.5](#15-corpus-doi--tuong-va-sang-phai-doc)** | Corpus to gấp 2.5 lần → chọn embedding provider cho đúng, nếu không F5-4 chạy 20+ phút |
> | **H — Hân** | ⚪ Gần như không | Chỉ đổi câu hỏi gợi ý trong `app.py` sang chủ đề pháp lý |
> | **S — Sáng** | ⚠️ **CÓ — đọc mục [1.5](#15-corpus-doi--tuong-va-sang-phai-doc)** | Golden dataset phải hỏi về luật + thuế, không chỉ hỏi đơn hàng |
>
> Chi tiết corpus mới và lý do chọn nguồn: [§1.5](#15-corpus-doi--tuong-va-sang-phai-doc).

Bám theo `README.md` (chấm điểm), `LAB_GUIDE.md` (checkpoint & phân vai — **Phương Án A: nhóm 4 thành viên**)
và `group_project/README.md` (deliverable bài nhóm).

Tổng thời lượng: **180 phút (3 giờ)** / 7 checkpoint.

**Mục lục**
0. [**📊 Bảng tiến độ**](#-bảng-tiến-độ--cập-nhật-mỗi-lần-merge) ← xem đầu tiên
1. [Phân vai, cân bằng khối lượng & **quy tắc hỗ trợ chéo**](#1-phân-vai--cân-bằng-khối-lượng)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Hợp đồng interface — chốt ở CP0](#3-hợp-đồng-interface--chốt-ở-cp0-bắt-buộc)
4. [Bảng ticket kiểu Jira](#4-bảng-ticket-kiểu-jira)
5. [Sơ đồ phụ thuộc](#5-sơ-đồ-phụ-thuộc-ai-chặn-ai)
6. [Kế hoạch theo checkpoint](#6-kế-hoạch-theo-checkpoint)
7. [Hướng dẫn test trước khi push & merge](#7-hướng-dẫn-test-trước-khi-push--merge)
8. [Bản đồ điểm](#8-bản-đồ-điểm--người-chịu-trách-nhiệm)
9. [Rủi ro & dự phòng](#9-rủi-ro--phương-án-dự-phòng)
10. [**Hướng dẫn dùng AI coding agent** (Codex / Claude / Antigravity / Copilot)](#10-hướng-dẫn-dùng-ai-coding-agent-codex--claude--antigravity--copilot)

---

## 1. Phân Vai & Cân Bằng Khối Lượng

| Role | Thành viên | MSSV | Mảng phụ trách |
|------|-----------|------|----------------|
| **Role 1** — Team Leader & Data/Pipeline | **Nguyễn Xuân Quang** | 2A202601776 | **Task 1, 2, 3** (data) + **Task 8** (PageIndex) + **Task 9** (pipeline) + điều phối, review PR |
| **Role 2** — Vector DB & Dense Search | **Cao Các Tường** | 2A202601236 | **Task 4** (chunking + ChromaDB) + **Task 5** (semantic search) + bonus **HyDE** |
| **Role 3** — Generation & Frontend | **Lưu Nguyễn Ngọc Hân** | 2A202601386 | **Task 10** (citation + reorder) + **`app.py`** + bonus **memory & UI** |
| **Role 4** — Sparse Search & Evaluation | **Trần Quang Sáng** | 2A202601446 | **Task 6** (BM25/TF-IDF) + **Task 7** (RRF) + **RAGAS eval** + `results.md` |

Viết tắt: **Q** = Quang, **T** = Tường, **H** = Hân, **S** = Sáng.

### Bảng cân đối khối lượng

| | Q (Quang) | T (Tường) | H (Hân) | S (Sáng) |
|---|---|---|---|---|
| **Task 1–10** | T1 ✅, T2 ✅, T3, T8, T9 | T4, T5 | T10 | T6, T7 |
| **Điểm Task 1–10** | 21 (đã xong 6) | 13 | 4 | 12 |
| **Bài nhóm** | tích hợp (4) + README (3) | — | chatbot (8) + chất lượng (3) | eval 4 metric + A/B + báo cáo (9) |
| **Golden dataset (3đ)** | 4 câu | 4 câu | 4 câu | 4 câu + gộp file |
| **Bonus phụ trách** | deploy (4) | HyDE (5) | memory (3) + UI (3) | TF-IDF (5) |
| **Còn phải làm** | 3 task + tích hợp | 2 task + bonus | 1 task + app + 2 bonus | 2 task + eval + bonus |

Cân đối: mỗi người **~3 đầu việc lớn**. Quang mang 5 task nhưng **Task 1 & 2 đã xong**,
nên phần còn lại (T3, T8, T9) tương đương người khác.

### Phần tôi (Quang) đã làm sẵn trên máy này

| Việc | Kết quả | File |
|------|---------|------|
| **Task 1** | **13 văn bản PDF**: 8 quy định Shopee + 5 luật toàn văn, đều trích được text | `data/landing/legal/*.pdf` + `_metadata.json` |
| **Task 2** | **18 bài hướng dẫn JSON**, đủ `url` / `title` / `date_crawled` / `topic` / `customer_role` | `data/landing/news/article_*.json` |
| **Task 3** | **31 file `.md`** kèm header metadata, `TestTask3` 4/4 passed | `data/standardized/**` |
| **Task 8** | PageIndex + fallback vectorless cục bộ, `TestTask8` 2/2 passed | `src/task8_pageindex_vectorless.py` |
| Helper crawl | Parse SSR JSON của help.shopee.vn → text sạch, không cần Chromium; hỗ trợ portal 4 & 10 | `src/shopee_help.py` (mới) |
| Helper luật | Lấy toàn văn luật qua API Wikisource, tự gom trang con theo chương | `src/wikisource_law.py` (mới) |
| **F5-0** | Sửa 3 hằng số mâu thuẫn giữa starter và LAB_GUIDE (xem §3.3) | `task4_...py`, `task9_...py` |
| Merge upstream | Lấy hint `EMBEDDING_PROVIDER` + `SUGGESTED_TOPICS.md`, gỡ conflict `requirements.txt` | — |
| Hạ tầng | `.venv` Python 3.12, `chroma_db/` vào `.gitignore`, sửa xung đột dependency | `.venv/`, `.gitignore`, `requirements.txt` |

**Nguồn đã thử và loại cho lớp văn bản luật** (ghi lại để không ai mất công thử lại):
`vanban.chinhphu.vn` PDF là ảnh scan → 0 ký tự · `thuvienphapluat.vn` 403 Cloudflare ·
`luatvietnam.vn` paywall · `vbpl.vn` đổi sang Next.js SPA, URL `.aspx` cũ 404 ·
`congbao.chinhphu.vn` chỉ có metadata. Chi tiết: docstring `src/wikisource_law.py`.

> Task 1–10 vẫn là **bài chung của cả nhóm** (50% điểm) — chốt bằng
> `pytest tests/test_individual.py` chạy trên `main`, cả nhóm cùng chịu trách nhiệm.

### 1.5. Corpus đổi — Tường và Sáng phải đọc

Chủ đề mới cần 2 lớp tài liệu bổ sung nhau:

| Lớp | Trả lời câu hỏi | Nguồn | Số file |
|-----|-----------------|-------|---------|
| **Quy định sàn** | "Shopee bắt tôi làm gì?" | help.shopee.vn | 26 |
| **Văn bản luật** | "Pháp luật bắt tôi làm gì?" | vi.wikisource.org | 5 |

**Corpus hiện tại: 31 file `.md`, 865.028 ký tự ≈ 1.081 chunk @800.**
Trước khi đổi chủ đề là 16 file / ~350k ký tự — **to lên 2,5 lần**.

<details>
<summary><b>13 văn bản lớp legal</b> (bấm để xem)</summary>

| File | Role | Nguồn |
|------|------|-------|
| returns-refund-policy-shopee | buyer | Shopee |
| privacy-policy-shopee | both | Shopee |
| product-listing-regulations-shopee | seller | Shopee |
| shipping-policy-shopee | both | Shopee |
| prohibited-restricted-products-policy-shopee | seller | Shopee |
| anti-fraud-policy-seller-shopee | seller | Shopee |
| ecommerce-platform-operating-rules-shopee | seller | Shopee |
| terms-of-service-shopee | both | Shopee |
| **luat-doanh-nghiep-2020** (328k ký tự) | seller | Wikisource |
| **luat-thuong-mai-2005** (182k ký tự) | both | Wikisource |
| **luat-bao-ve-quyen-loi-nguoi-tieu-dung-2010** | both | Wikisource |
| **luat-giao-dich-dien-tu-2005** | both | Wikisource |
| **luat-thue-thu-nhap-ca-nhan-2007** | seller | Wikisource |

18 bài news theo chủ đề: thuế & hoá đơn (5), theo dõi đơn hàng (3), phương thức
thanh toán (3), trả hàng & hoàn tiền (2), mua hàng xuyên biên giới (2),
dòng tiền người bán (2), bảo hành (1).
</details>

#### ⚠️ TƯỜNG (F5-4) — đọc kỹ, đây là thay đổi lớn nhất

**1.081 chunk thay vì ~430.** Với `BAAI/bge-m3` chạy CPU, embedding 1.081 chunk mất
**khoảng 15–25 phút** — vượt hẳn 25 phút của cả CP2. Ba lựa chọn, chọn 1 **ngay từ CP0**:

| Cách | Lệnh / cấu hình | Thời gian embed | Đánh đổi |
|------|-----------------|-----------------|----------|
| 🟢 **`all-MiniLM-L6-v2`** (khuyến nghị nếu chưa tải model) | Đổi `EMBEDDING_MODEL`, `EMBEDDING_DIM=384` | ~3–5 phút | Yếu hơn với tiếng Việt, nhưng đủ để pass test và demo |
| 🟡 **Google `text-embedding-004`** | `EMBEDDING_PROVIDER=google` + `GEMINI_API_KEY`, `EMBEDDING_DIM=768` | ~2–4 phút | Không phải tải 2.2GB; tốn API call, có thể dính rate limit |
| 🔴 **`bge-m3`** (mặc định) | Giữ nguyên | 15–25 phút | Chất lượng tiếng Việt tốt nhất, nhưng **chặn cả S lẫn Q** |

> Upstream vừa thêm hint viết `embed_texts()` dispatch theo `EMBEDDING_PROVIDER`
> (xem docstring `task4_chunking_indexing.py`). Làm theo hint đó thì đổi provider chỉ
> là sửa `.env`, và Task 5 tự dùng đúng provider mà không phải sửa code lần hai.
>
> **Đổi provider → BẮT BUỘC xoá `chroma_db/` rồi index lại** (dimension 384/768/1024
> không tương thích ngược).

Cân nhắc thêm: `luat-doanh-nghiep-2020.md` một mình đã chiếm ~38% corpus. Nếu cần
cắt thời gian, có thể chỉ index các chương liên quan (Chương I quy định chung,
Chương IV–V về công ty TNHH) — **ghi rõ lý do lược bớt vào comment** để trả lời được
khi bị hỏi.

#### ⚠️ SÁNG (F5-12, F5-13) — golden dataset phải đổi

Bộ câu hỏi cũ chỉ hỏi vận hành đơn hàng → **không còn đại diện cho chủ đề mới**.
16 câu chia theo 4 nhóm, mỗi người 4 câu:

| Nhóm | Ai viết | Ví dụ câu hỏi | Tài liệu chứa evidence |
|------|---------|---------------|------------------------|
| **Thuế & hoá đơn** | Sáng | "Bán hàng online doanh thu bao nhiêu thì phải nộp thuế TNCN?" | `luat-thue-thu-nhap-ca-nhan-2007`, `article_11..15` |
| **Thành lập & đăng ký KD** | Quang | "Công ty TNHH một thành viên có bắt buộc có Ban kiểm soát không?" | `luat-doanh-nghiep-2020` |
| **Quy định bán hàng trên sàn** | Tường | "Những mặt hàng nào bị cấm đăng bán trên Shopee?" | `prohibited-restricted-products`, `product-listing-regulations` |
| **Quyền người tiêu dùng & đổi trả** | Hân | "Người tiêu dùng có quyền trả hàng trong bao lâu?" | `luat-bao-ve-quyen-loi-nguoi-tieu-dung-2010`, `returns-refund-policy` |

Yêu cầu thêm: **ít nhất 3 câu phải cần lọc `customer_role=seller`** để chứng minh
metadata_filter hoạt động (yêu cầu K4 Variant). Corpus giờ có **12 tài liệu `seller`**
nên retrieve được — trước khi đổi chủ đề chỉ có 3, quá mỏng.

Với **F5-13 (A/B test)**: corpus 2 nguồn khiến so sánh có ý nghĩa hơn — câu hỏi về luật
thường cần BM25 (bắt số hiệu điều luật "Điều 33", "Luật số 59/2020/QH14"), câu hỏi vận
hành thì semantic mạnh hơn. Đây chính là luận điểm để phân tích worst performers.

#### ⚪ HÂN (F5-10, F5-11) — chỉ đổi phần hiển thị

Code không đổi. Chỉ cần:
- Đổi **câu hỏi gợi ý** trong `app.py` sang chủ đề pháp lý (lấy từ bảng của Sáng ở trên).
- Citation nên in kèm `doc_type` (`legal_document` vs `platform_policy`) để người dùng
  phân biệt "đây là luật" hay "đây là quy định riêng của sàn" — khác biệt quan trọng
  về mặt pháp lý, và là điểm cộng khi chấm "chất lượng câu trả lời".

#### Metadata mỗi file `.md` giờ có thêm

```markdown
**customer_role:** buyer | seller | both
**doc_type:** legal_document | platform_policy | support_article
**topic:** thuế & hoá đơn | thành lập doanh nghiệp | ...
```

`doc_type` là trường mới — Tường nhớ đưa vào metadata của chunk ở F5-4.

---

### 🔁 Quy tắc hỗ trợ chéo — XONG VIỆC LÀ QUA GIÚP NGƯỜI KHÁC

**Không ai được ngồi chơi khi còn người đang kẹt.** Bảng phân việc ở trên là điểm xuất phát,
không phải hàng rào. Xong ticket của mình → **báo nhóm 1 dòng rồi nhảy sang hỗ trợ ngay**.

#### Xong việc thì làm gì — theo đúng thứ tự này

1. **Push + báo nhóm** (5 phút): `F5-6 merged — lexical_search chạy được, TestTask6 4 passed`.
2. **Hỏi 1 câu trong nhóm**: "Mình xong F5-6, ai đang kẹt?"
3. **Không ai trả lời trong 1 phút** → tự chọn theo bảng ưu tiên dưới đây.

#### Bảng ưu tiên: xong rồi thì qua giúp ai

| Nếu bạn xong… | Ưu tiên 1 | Ưu tiên 2 | Ưu tiên 3 |
|---------------|-----------|-----------|-----------|
| **Q** xong F5-3 / F5-8 / F5-9 | Giúp **T** ở F5-4 (viết `load_documents()` trong khi T tải model) | Giúp **S** ở F5-13 (chạy eval song song) | Viết câu hỏi F5-12 |
| **T** xong F5-4 / F5-5 | Giúp **S** ở F5-6 (BM25 dùng chung corpus với F5-4) | Giúp **H** ở F5-11 (UI hiển thị score) | Làm bonus F5-14 HyDE |
| **H** xong F5-10 / F5-11 | Giúp **S** ở F5-12 (viết thêm câu hỏi) | Giúp **Q** test fallback F5-9 bằng query lạc đề | Làm bonus F5-15 |
| **S** xong F5-6 / F5-7 | Giúp **Q** ở F5-8 (PageIndex hoặc viết fallback dự phòng) | Giúp **T** ở F5-4 nếu index còn lỗi | Bắt đầu sớm F5-13 |

#### Việc nào chia đôi được ngay (2 người làm song song không giẫm chân)

| Ticket | Cách chia | Vì sao không conflict |
|--------|-----------|----------------------|
| **F5-4** | 1 người `load_documents()` + `chunk_documents()`, người kia `embed_chunks()` + `index_to_vectorstore()` | 4 hàm rời, chỉ nối ở `run_pipeline()` |
| **F5-6** | 1 người BM25, người kia TF-IDF (bonus 5đ) | 2 hàm độc lập, chung 1 corpus loader |
| **F5-12** | Chia theo chủ đề: hoàn tiền / thanh toán / vận chuyển / bảo mật — mỗi người 4 câu | Mỗi người 1 file `golden_part_<tên>.json`, S gộp cuối |
| **F5-13** | 1 người chạy config A (hybrid+rerank), người kia config B (dense-only) | 2 lần chạy độc lập, ghép bảng ở `results.md` |
| **F5-11** | 1 người khung chat + memory, người kia panel source/score | 2 hàm render tách biệt trong `app.py` |

#### Việc KHÔNG nên chia đôi

**F5-9** (`retrieve()`) và **F5-10** (`generate_with_citation()`) — logic dính liền,
2 người sửa cùng lúc chắc chắn conflict. Muốn giúp thì **pair**: 1 người gõ, 1 người đọc
test + soi lỗi, không tách branch.

#### Quy tắc chống giẫm chân

1. **Báo trước khi đụng file người khác**: "Mình vào giúp `task4_chunking_indexing.py` hàm `embed_chunks` nhé?" — đợi OK rồi mới sửa.
2. **Người chủ ticket vẫn là người merge PR** — người hỗ trợ push lên **branch của chủ ticket**, không mở branch riêng.
3. **Ưu tiên tuyệt đối theo điểm**: Task 1–10 (50đ) > chatbot + eval (30đ) > bonus (20đ).
   Còn task nào trong 50đ chưa xong thì **cấm ai làm bonus**.
4. **Từ CP4 trở đi**, nếu chưa đủ 35/35 test → **cả 4 người dừng việc riêng**, gộp sức fix
   cho đủ mốc 50đ rồi mới quay lại phần của mình.

---

## 2. Kiến Trúc Hệ Thống

```
                    ┌──────────────────────────────────────┐
   help.shopee.vn ─►│ Task 1: 6 PDF chính sách  (legal/)   │  Q
   (robots: Allow)  │ Task 2: 10 JSON hướng dẫn (news/)    │  Q
                    └───────────────┬──────────────────────┘
                                    │ Task 3 — MarkItDown          Q
                                    ▼
                          data/standardized/**/*.md
                                    │ Task 4 — Recursive splitter  T
                                    │   size=800, overlap=100
                                    │   embed: BAAI/bge-m3 (1024d)
                                    ▼
                    chroma_db/  collection "ecommerce_support_docs"
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
   Task 5: semantic_search()   T              Task 6: lexical_search()   S
   dense / cosine / + HyDE                    sparse / BM25 + TF-IDF
              └─────────────────────┬─────────────────────┘
                                    ▼
                     Task 7: rerank_rrf()  RRF(d)=Σ 1/(60+rank)     S
                                    │
                                    ▼
                   Task 9: retrieve(query, top_k, score_threshold)   Q
                   ├─ cosine gốc của dense top-1 ≥ 0.48 → hybrid
                   └─ < 0.48 → Task 8: PageIndex vectorless          Q
                                    │
                                    ▼
                   Task 10: reorder (front + back[::-1]) → LLM       H
                            → answer + citation [Nguồn, Năm]
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        app.py (Streamlit chatbot)  H    eval_pipeline.py (RAGAS, A/B)  S
```

---

## 3. Hợp Đồng Interface — Chốt ở CP0 (BẮT BUỘC)

Đây là phần quan trọng nhất để **4 người làm song song mà không chặn nhau**.
Chốt xong ở CP0 thì S và H code được ngay, **không cần chờ** ChromaDB của T.

### 3.1 Kiểu dữ liệu dùng chung

Mọi hàm retrieval (Task 5, 6, 7, 8, 9) đều trả về **cùng một shape**:

```python
Result = {
    "content":  str,    # nội dung chunk
    "score":    float,  # điểm của ranker tạo ra nó
    "metadata": dict,   # {"source": str, "title": str, "customer_role": str, "url": str, ...}
    # Task 8 bắt buộc thêm:
    "source":   "pageindex",
}
```

Danh sách trả về **luôn sorted theo `score` giảm dần** và **độ dài ≤ top_k**.

### 3.2 Chữ ký hàm — không ai được đổi

| Task | Chữ ký | Chủ |
|------|--------|-----|
| 4 | `load_documents() -> list[dict]`, `chunk_documents(docs) -> list[dict]`, `run_pipeline()` | T |
| 5 | `semantic_search(query: str, top_k: int = 10) -> list[Result]` | T |
| 6 | `lexical_search(query: str, top_k: int = 10) -> list[Result]` | S |
| 7 | `rerank_rrf(ranked_lists: list[list[Result]], top_k=5, k=60) -> list[Result]`<br>`rerank(query, candidates, top_k=5, method="rrf") -> list[Result]` | S |
| 8 | `pageindex_search(query: str, top_k: int = 5) -> list[Result]` (có `source="pageindex"`) | Q |
| 9 | `retrieve(query, top_k=5, score_threshold=0.48, use_reranking=True) -> list[Result]` | Q |
| 10 | `reorder_for_llm(chunks) -> list[dict]`<br>`format_context(chunks) -> str`<br>`generate_with_citation(query, top_k=5) -> {"answer", "sources", "retrieval_source"}` | H |

### 3.3 Hằng số đã chốt — ✅ ĐÃ SỬA

Starter mâu thuẫn với LAB_GUIDE ở 3 chỗ. **Tôi (Quang) đã sửa, kèm comment giải thích:**

| Hằng số | File | Starter | LAB_GUIDE | Đã chốt |
|---------|------|---------|-----------|---------|
| `CHUNK_SIZE` | `task4_chunking_indexing.py` | ~~500~~ | 800 | ✅ **800** |
| `CHUNK_OVERLAP` | `task4_chunking_indexing.py` | ~~50~~ | 100 | ✅ **100** |
| `SCORE_THRESHOLD` | `task9_retrieval_pipeline.py` | ~~0.3~~ | 0.48 | ✅ **0.48** |

⚠️ **`0.48` mới là giá trị khởi điểm.** Sau khi F5-4 index xong, **Quang calibrate lại**:
chạy `semantic_search()` với vài câu đúng chủ đề và vài câu lạc đề, xem cosine top-1 rơi
khoảng nào, đặt threshold vào giữa. Đổi embedding model → **bắt buộc đo lại**.

### 3.4 Cách làm việc song song khi chưa có dữ liệu thật

S và H **không được ngồi chờ** `chroma_db/`. Dùng fixture giả:

```python
# scratch_fixture.py — chỉ để test cục bộ, KHÔNG commit
FAKE = [
    {"content": "Shopee hoàn tiền trong 7 ngày kể từ khi nhận hàng.",
     "score": 0.81, "metadata": {"source": "returns-refund-policy-shopee.md",
                                 "title": "Chính sách trả hàng và hoàn tiền",
                                 "customer_role": "buyer"}},
    {"content": "Các phương thức thanh toán gồm ShopeePay, thẻ tín dụng, COD.",
     "score": 0.64, "metadata": {"source": "available-payment-methods.md",
                                 "title": "Phương thức thanh toán",
                                 "customer_role": "buyer"}},
]
```

- **S** test `rerank_rrf([FAKE, FAKE_2])` bằng list giả → không cần ChromaDB.
- **H** test `reorder_for_llm(FAKE)` và `format_context(FAKE)` bằng list giả → không cần Task 9.

---

## 4. Bảng Ticket Kiểu Jira

Trạng thái: ⬜ To Do · 🟡 In Progress · 🔵 In Review · ✅ Done · 🚫 Blocked

**Ký hiệu:** ⭐ = ticket **BONUS** (20đ, làm SAU CÙNG). Ticket không có ⭐ là **bắt buộc**
(Task 1–10 = 50đ + bài nhóm = 30đ). Xem [§8.4 danh sách bonus gọn](#84-bonus--20-điểm-làm-sau-cùng).

### 📋 LUẬT SỬA BẢNG JIRA — đọc trước khi đụng vào

Bảng này là **nguồn sự thật duy nhất** về tiến độ. Ai cũng sửa được, nhưng theo đúng 6 luật:

1. **Chỉ sửa ô `TT` của ticket MÌNH phụ trách.** Muốn đổi trạng thái ticket người khác →
   nhắn họ, đừng tự sửa. Ngoại lệ: Quang được sửa mọi ô (vai trò điều phối).
2. **Chỉ đổi trạng thái khi có bằng chứng**, không đổi theo cảm giác:

   | Đổi sang | Điều kiện bắt buộc |
   |----------|--------------------|
   | 🟡 In Progress | Đã tạo branch `F5-<n>-<mô-tả>` |
   | 🔵 In Review | Đã mở PR **và** `pytest` không FAIL |
   | ✅ Done | Đã **merge vào `main`** và test của ticket đó **`passed`, không phải `skipped`** |

   > ⚠️ `skipped` ≠ `passed`. Chưa implement thì test tự skip — đánh ✅ lúc đó là báo cáo sai.

3. **Đánh ✅ thì phải cập nhật 3 chỗ cùng lúc** (nếu không bảng sẽ mâu thuẫn nhau):
   - ô `TT` trong bảng này
   - dòng tương ứng ở [📊 Bảng tiến độ](#-bảng-tiến-độ--cập-nhật-mỗi-lần-merge) đầu file
   - con số `pytest` ở Bảng tiến độ (chạy `pytest tests/test_individual.py` lấy số thật)

4. **Cập nhật cột `Bàn giao` bằng số thật**, không để mô tả chung chung.
   Ví dụ: `chroma_db/ có 1.081 chunk` thay vì `chroma_db/ > 0 docs`.
   Người sau đọc cột này để biết đầu vào của mình là gì.

5. **Ticket bị chặn** thì ghi rõ đang chờ ai ở cột `TT`, ví dụ `⬜ chờ F5-4 (T)`.
   Thấy mình bị chặn quá 10 phút → áp dụng [quy tắc hỗ trợ chéo §1](#-quy-tắc-hỗ-trợ-chéo--xong-việc-là-qua-giúp-người-khác),
   nhảy sang giúp người đang chặn thay vì ngồi chờ.

6. **Commit sửa bảng đi kèm commit code**, đừng để thành commit riêng lẻ —
   bảng phải luôn khớp với `main`. Mẫu commit: `F5-6: lexical_search BM25 + cap nhat PLAN`.

**Không được làm:** xoá dòng ticket · đổi ID ticket · gộp 2 ticket ·
đánh ✅ cho ticket còn `skipped` · sửa cột `Blocked by`/`Blocks` mà không báo Quang
(đó là đồ thị phụ thuộc, đổi là hỏng thứ tự làm việc của cả nhóm).

| ID | Ticket | Ai | CP | Blocked by | Blocks | Bàn giao (artifact người sau cần) | TT |
|----|--------|----|----|-----------|--------|-----------------------------------|----|
| **F5-00** | **Setup môi trường** (venv 3.12 + deps + `.env`) | **cả 4** | CP0 | — | *tất cả* | Mỗi máy chạy được lệnh verify `SETUP OK` (§CP0-A) | 🟡 Q xong · T/H/S chưa xác nhận |
| **F5-0** | Chốt 3 hằng số + push `main` | Q | CP0 | — | F5-4, F5-9 | `main` có 800 / 100 / 0.48 | ✅ |
| **F5-1** | Task 1 — ≥3 PDF chính sách | Q | CP1 | — | F5-3 | `data/landing/legal/` **13 PDF** (8 Shopee + 5 luật), đều trích được text 1.4k–328k ký tự + `_metadata.json` | ✅ |
| **F5-2** | Task 2 — ≥5 bài hướng dẫn | Q | CP1 | — | F5-3 | `data/landing/news/` **18 JSON**, đủ `url`/`title`/`date_crawled`/`topic`/`customer_role` | ✅ |
| **F5-3** | Task 3 — convert markdown | Q | CP1 | F5-1, F5-2 | F5-4, F5-8, F5-12 | `data/standardized/` **31 file `.md`**, 865.028 ký tự, mỗi file có header 5 trường metadata | ✅ |
| **F5-4** | Task 4 — chunking + ChromaDB index | T | CP2 | ~~F5-0, F5-3~~ ✅ | F5-5, F5-6 | `chroma_db/` **1.216 chunk** @800, model `paraphrase-multilingual-MiniLM-L12-v2` (384d), **đã commit lên repo** — pull về là dùng được ngay, không phải index lại. `TestTask4` **4/4 passed** | ✅ |
| **F5-5** | Task 5 — `semantic_search()` | T | CP2 | ~~F5-4~~ ✅ | F5-9 | Trả `list[Result]` sorted desc, score là cosine [0,1]. Đo thực tế: đúng chủ đề **0,444–0,531** · lạc đề **0,265–0,365**. `TestTask5` **4/4 passed** | ✅ |
| **F5-6** | Task 6 — `lexical_search()` BM25 + TF-IDF | S | CP2 | ~~F5-4~~ ✅ | F5-9 | Trả `list[Result]` sorted desc; corpus lấy từ `data/standardized/**/*.md` (31 file) | 🔴 **ĐƯỜNG GĂNG — khoá 13đ Task + 9đ bài nhóm** |
| **F5-7** | Task 7 — `rerank_rrf()` + `rerank()` | S | CP3 | — *(fixture giả)* | F5-9 | Gộp ≥2 ranked list, output re-sorted, có `score` — `TestTask7` **3/3 passed** | ✅ |
| **F5-8** | Task 8 — `pageindex_search()` | Q | CP3 | F5-3 | F5-9 | **3 doc trên PageIndex** + fallback cục bộ; `TestTask8` **2/2 passed** | ✅ |
| **F5-9** | Task 9 — `retrieve()` + fallback | Q | CP4 | ~~F5-5~~ ✅, **F5-6**, ~~F5-7~~ ✅, ~~F5-8~~ ✅ | F5-10, F5-13 | `retrieve()` chạy, fallback trigger. **Đặt `SCORE_THRESHOLD ≈ 0,40`** theo số đo ở F5-5 — KHÔNG dùng 0,48, câu đúng chủ đề sẽ rơi nhầm xuống fallback | ⬜ **chỉ còn chờ F5-6** |
| **F5-10** | Task 10 — `generate_with_citation()` | H | CP4 | F5-9 *(đã mock)* | F5-11, F5-13 | `{answer, sources, retrieval_source}` + `[Nguồn, Năm]` — `TestTask10` **3/3 passed** | ✅ |
| **F5-11** | `app.py` — Streamlit chatbot | H | CP5 | ~~F5-10~~ ✅ | — | `streamlit run app.py` trả lời + hiện source & score | 🟢 **làm được ngay** |
| **F5-12** | `golden_dataset.json` — 16 Q&A **theo 4 nhóm chủ đề mới** (§1.5) | S | CP5 | F5-3 | F5-13 | **16 câu**, đủ `question`/`expected_answer`/`expected_context`, bám luật + thuế + quy định sàn | ✅ |
| **F5-13** | `eval_pipeline.py` + `results.md` — RAGAS A/B | S | CP5 | ~~F5-10~~ ✅, ~~F5-12~~ ✅, **F5-9** | — | 4 metric × 2 config + phân tích worst performers | 🟡 scaffold 418 dòng · chờ `retrieve()` thật mới chạy được A/B |
| ⭐ **F5-14** | **[BONUS 5đ]** HyDE / Query Expansion | T | CP5 | F5-5 | — | Flag bật/tắt trong `task5`, đo được chênh lệch | 🔒 khoá đến khi xong 50đ |
| ⭐ **F5-15** | **[BONUS 3+3đ]** conversation memory + UI source/score | H | CP5 | F5-11 | — | Follow-up hiểu ngữ cảnh; UI hiện nguồn + điểm | 🔒 khoá đến khi xong 50đ |
| ⭐ **F5-16** | **[BONUS 4đ]** deploy Hugging Face Spaces | Q | CP6 | F5-11 | — | URL Space chạy được | 🔒 khoá đến khi xong 50đ |
| **F5-17** | Chốt nộp: pytest 35/35 + dọn repo + push | Q | CP6 | tất cả | — | `main` xanh, `.env`/`chroma_db/`/`.venv/` không lọt git | ⬜ chờ tất cả |

### Ticket làm được NGAY, không chờ ai

| Ticket | Ai | Vì sao không bị chặn |
|--------|----|--------------------|
| **F5-6** | S | 🔴 **Đường găng — làm ngay.** `chroma_db/` đã commit sẵn, pull về là chạy |
| **F5-11** | H | F5-10 xong → nối `generate_with_citation()` thật vào `app.py` |
| **F5-12** (4 câu) | Q | Nhóm "Thành lập & đăng ký KD", evidence từ `luat-doanh-nghiep-2020.md` |
| ~~F5-4, F5-5~~ | T | ✅ 1.216 chunk đã index và commit |
| ~~F5-7, F5-12~~ | S | ✅ RRF + 16 câu golden dataset |

---

## 5. Sơ Đồ Phụ Thuộc (ai chặn ai)

```
CP0         CP1               CP2                CP3          CP4             CP5             CP6
──────────────────────────────────────────────────────────────────────────────────────────────────────
F5-00 (cả 4) ──────────────►┐
F5-0  (Q) ✅ ───────────────┤
                            │
F5-1 (Q) ✅ ──┐             │
              ├─► F5-3 (Q) ─┼─► F5-4 (T) ─┬─► F5-5 (T) ──┐
F5-2 (Q) ✅ ──┘             │              └─► F5-6 (S) ──┤
                            │                             ├──► F5-9 (Q) ──► F5-10 (H) ─┬─► F5-11 (H) ──► F5-16 (Q)
              F5-7 (S) ─────┼─────────────────────────────┤                            │                    │
              (fixture giả) │                             │                            └─► F5-13 (S) ───────┼──► F5-17 (Q)
                            └─► F5-8 (Q) ─────────────────┘                                    ▲            │
                                                                                               │            │
              F5-12 (cả 4) ───────────────────────────────────────────────────────────────────┘            │
              (chỉ cần data/landing)                                                                        │
              F5-14 (T) ────────────────────────────────────────────────────────────────────────────────────┘
              F5-15 (H) ────────────────────────────────────────────────────────────────────────────────────┘
```

**3 nút thắt cổ chai — canh chừng:**

| Nút thắt | Ai chờ ai | Hệ quả nếu trễ | Cách gỡ |
|----------|-----------|----------------|---------|
| **F5-6** (BM25) 🔴 **ĐANG XẢY RA** | S chặn Q (F5-9) → chặn chính S (F5-13) | Khoá 13đ Task + 9đ bài nhóm | Tường đã rảnh → nhảy vào làm cùng: BM25 và TF-IDF là 2 hàm độc lập, chia đôi được |
| ~~F5-4 (ChromaDB)~~ ✅ | — | — | Đã xong, `chroma_db/` commit lên repo nên không ai phải index lại |
| ~~F5-13 (RAGAS)~~ | S | — | Scaffold xong rồi, chỉ chờ `retrieve()` thật để chạy A/B |

**Quy tắc bàn giao:** ai xong ticket thì **push lên `main` trong vòng 5 phút** rồi
báo nhóm 1 dòng: `F5-4 merged — chroma_db/ có 342 chunks, chạy lại bằng python -m src.task4_chunking_indexing`.
Người sau **không clone nhánh của người trước** — luôn lấy từ `main`.

---

## 6. Kế Hoạch Theo Checkpoint

### CP0 — Setup môi trường (0:00–0:10)

> **Setup là việc của CẢ 4 NGƯỜI, không chia vai.** Ai cũng phải có môi trường chạy được
> trên máy mình — không có chuyện "để một người cài rồi mình dùng ké".

#### CP0-A — Các bước MỌI NGƯỜI đều phải làm

Chạy trong PowerShell, tại thư mục repo:

```powershell
# 1. Lấy code mới nhất
git clone <repo-nhóm>            # lần đầu
cd K4-Day08-RAG-Pipeline_F5
git pull origin main

# 2. Tạo venv Python 3.12  (KHÔNG dùng 3.13/3.14 — xem cảnh báo bên dưới)
uv venv --python 3.12 .venv
#   Không có uv? cài: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
#   Hoặc dùng python 3.12 sẵn có: py -3.12 -m venv .venv

# 3. Cài dependencies (~450MB, 5–15 phút tuỳ mạng)
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
#   Dùng pip thường: .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Tạo .env và điền key
Copy-Item .env.example .env
#   Điền OPENROUTER_API_KEY (Quang chia sẻ), PAGEINDEX_API_KEY (Quang lấy ở F5-8)

# 5. Encoding tiếng Việt — thêm vào MỖI phiên PowerShell
$env:PYTHONIOENCODING="utf-8"
```

**Verify — ai cũng phải chạy và thấy `SETUP OK`:**

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "import chromadb, sentence_transformers, streamlit, ragas, datasets, rank_bm25, sklearn, markitdown, fpdf; from dotenv import load_dotenv; load_dotenv(); import os; assert os.getenv('OPENROUTER_API_KEY'), 'thieu OPENROUTER_API_KEY trong .env'; print('SETUP OK')"
```

Rồi chạy test — đúng lúc này phải thấy **6 passed** (Task 1–2 đã xong), còn lại skipped:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_individual.py -v
```

#### CP0-B — Phần riêng theo role (sau khi CP0-A xong)

| # | Việc | Ai | Xong khi |
|---|------|-----|----------|
| 1 | ~~F5-0: sửa 3 hằng số (§3.3)~~ | Q | ✅ đã sửa, còn commit + push `main` |
| 2 | Chia sẻ `OPENROUTER_API_KEY` cho cả nhóm (kênh riêng, KHÔNG commit) | Q | Cả 4 người gọi được API |
| 3 | **Chốt embedding provider** theo bảng §1.5 (corpus 1.081 chunk!) rồi tải model chạy nền | T | Đã chọn xong provider, không đổi giữa chừng |
| 4 | `streamlit run app.py` mở được | H | localhost:8501 |
| 5 | Đọc `tests/test_individual.py::TestTask6,TestTask7` để nắm tiêu chí | S | Biết test đòi gì trước khi code |

Lệnh tải model trước cho T (chạy nền, làm việc khác song song):

```powershell
.\.venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3'); print('model cached')"
```

#### ⚠️ 4 lỗi setup đã gặp thật — đọc trước khi hỏi nhóm

| Lỗi | Nguyên nhân | Xử lý |
|-----|-------------|-------|
| `No matching distribution for torch` / build từ source rất lâu | Đang dùng **Python 3.13/3.14** — chưa có wheel torch, chromadb | Bắt buộc **3.12**. Kiểm tra: `.\.venv\Scripts\python.exe -V` |
| `Failed to acquire lock on the client cache` | Có **tiến trình `uv` khác đang treo** giữ lock | `Get-Process uv` → `Stop-Process -Id <PID> -Force`, rồi cài lại |
| `MissingDependencyException` khi convert PDF | Thiếu extra đọc PDF của markitdown | `uv pip install --python .venv\Scripts\python.exe "markitdown[pdf]"` |
| `BrowserType.launch: Executable doesn't exist` | `crawl4ai` chưa tải Chromium | `.\.venv\Scripts\playwright.exe install chromium` — **hoặc bỏ qua**: Task 1–2 đã crawl xong bằng `requests` |

**Trạng thái hiện tại:** `.venv` (Python 3.12 qua `uv`) đã tạo; `requirements.txt` **chưa cài xong**
(lần trước treo do lock, đã kill tiến trình — chạy lại bước 3 ở CP0-A).

---

### CP1 — Task 1–3 (0:10–0:35)

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | ~~F5-1~~ | Q | ✅ 6 PDF trong `data/landing/legal/` + `_metadata.json` |
| 2 | ~~F5-2~~ | Q | ✅ 10 JSON trong `data/landing/news/` |
| 3 | ~~**F5-3**~~ | Q | ✅ 16 file `.md` (6 legal + 10 news), TestTask3 4/4 passed |
| 4 | **F5-12** khởi động — mỗi người viết 4 câu hỏi từ data đã crawl | cả 4 | Mỗi người có 4 câu nháp |
| 5 | Đọc data để hiểu domain trước khi code | T, H, S | Biết corpus nói về gì |

**Đã làm sẵn:** `src/shopee_help.py` parse khối SSR JSON `window["FORGE_SSR_DATA_MAP"]`
của help.shopee.vn → text bài viết sạch, không cần Chromium.
Chạy `--crawl4ai` để đổi sang Crawl4AI AsyncWebCrawler (tự fallback nếu thiếu browser binary).

Task 3 cần `markitdown[pdf]` — lỗi `MissingDependencyException` thì `pip install "markitdown[pdf]"`.

---

### 📦 BÀN GIAO F5-3 → F5-4 (Quang → Tường)

**F5-4 đã hết vật cản, Tường bắt đầu được ngay.** `git pull origin main` rồi làm.

⚠️ **Đọc [§1.5](#15-corpus-doi--tuong-va-sang-phai-doc) TRƯỚC** — corpus đã đổi, phải chọn
embedding provider cho đúng nếu không F5-4 chạy 20+ phút và chặn cả nhóm.

Đầu vào có sẵn: **31 file** trong `data/standardized/` — 13 `legal/` + 18 `news/`,
tổng 865k ký tự ≈ 1.081 chunk @800.
Mỗi file mở đầu bằng khối header cố định:

```markdown
# CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN

**Source:** https://help.shopee.vn/portal/4/article/77251
**Crawled:** 2026-08-04T11:49:52+07:00
**customer_role:** buyer | seller | both
**doc_type:** legal_document | platform_policy | support_article
**topic:** thuế & hoá đơn | thành lập doanh nghiệp | ...

---
<nội dung thật bắt đầu từ đây>
```

`doc_type` là **trường mới** sau khi đổi chủ đề — phân biệt văn bản luật (Wikisource)
với quy định riêng của sàn (Shopee). Nhớ đưa vào metadata chunk: Hân cần nó để in
citation phân biệt "luật" vs "quy định sàn".

**Tường nên làm gì với header này** trong `load_documents()`:
- Parse `**Key:** value` phía trên dấu `---` → dict metadata cho document.
- Lấy `# <tiêu đề>` dòng đầu làm `title`.
- Phần sau `---` mới là nội dung đem đi chunk — **đừng chunk luôn cả header**,
  nếu không mỗi chunk đầu tài liệu sẽ chứa URL làm nhiễu BM25 ở Task 6.
- Gắn vào metadata mỗi chunk: `source` (tên file), `title`, `url`, `customer_role`, `doc_type`.
  Task 10 cần `title` + `url` để in citation `[Nguồn, Năm]`; Task 6/9 cần `customer_role`
  cho benchmark có metadata_filter.

Kiểm tra nhanh trước khi code:
```powershell
Get-ChildItem data\standardized -Recurse -Filter *.md | Measure-Object   # phải ra 16
Get-Content data\standardized\legal\returns-refund-policy-shopee.md -TotalCount 12
```

Prompt sẵn cho agent: `PLAN.md` §10.3, mục **F5-4**.

---

### CP2 — Task 4–6 (0:35–1:00)

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | **F5-4** — chunk 800/100, embed `bge-m3`, index `chroma_db/` | T | Collection > 0 docs, `TestTask4` pass |
| 2 | **F5-5** — `semantic_search()` | T | `TestTask5` pass, score là cosine [0,1] |
| 3 | **F5-6** — `lexical_search()` BM25 · ⭐ thêm TF-IDF = **BONUS 5đ** | S | `TestTask6` pass, keyword khớp phải xếp cao hơn |
| 4 | **F5-8** — đăng ký pageindex.ai, upload doc | Q | Có `PAGEINDEX_API_KEY`, doc đã upload |
| 5 | **F5-10** khởi động — `reorder_for_llm()` + `format_context()` bằng fixture giả | H | 2 hàm chạy đúng, chưa cần LLM |

---

### CP3 — Task 7–8 (1:00–1:20)

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | **F5-7** — `rerank_rrf()` ghép dữ liệu thật | S | `TestTask7` pass |
| 2 | **F5-8** — `pageindex_search()` | Q | `TestTask8` pass, có `source="pageindex"` |
| 3 | **F5-5** hoàn thiện + bắt đầu **F5-14** (HyDE) | T | Semantic search ổn định |
| 4 | **F5-10** — ghép LLM call | H | Gọi được OpenRouter, có output |

**Dự phòng F5-8:** nếu PageIndex không đăng ký kịp / hết quota → Quang tự viết fallback
"vectorless": duyệt theo heading của `.md` trong `data/standardized/`, chấm bằng keyword overlap,
vẫn gắn `source="pageindex"`. Vẫn pass `TestTask8`; ghi rõ lý do thay thế vào docstring.

---

### CP4 — Task 9–10 (1:20–1:45) 🎯 MỐC 50 ĐIỂM BẮT BUỘC

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | **F5-9** — `retrieve()` = semantic + lexical → RRF → fallback | Q | `TestTask9` pass, fallback trigger thật |
| 2 | Calibrate lại `SCORE_THRESHOLD` trên corpus thật | Q | Query lạc đề rơi vào PageIndex, query đúng thì không |
| 3 | **F5-10** — output có `[Nguồn, Năm]` | H | Thiếu evidence → "I cannot verify this information" |
| 4 | **F5-13** — dựng khung `eval_pipeline.py` với hàm giả | S | Chạy được end-to-end với 2 câu mẫu |
| 5 | ⭐ **F5-14** — HyDE — **BONUS 5đ** (chỉ làm nếu F5-5 đã xanh) | T | Bật/tắt bằng flag |
| 6 | Chạy full `pytest -v` trên `main` | Q | **35/35 passed** |

---

### CP5 — Bài nhóm (1:45–2:15)

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | **F5-11** — `app.py`: chat, sidebar `top_k`, panel source + score | H | Hỏi → trả lời kèm nguồn |
| 2 | ⭐ **F5-15** — memory + UI source/score — **BONUS 3+3đ** | H | Follow-up "còn phí thì sao?" hiểu ngữ cảnh |
| 3 | **F5-12** — gộp 16 câu của 4 người thành `golden_dataset.json` | S gộp | Có `expected_context` khớp file thật |
| 4 | **F5-13** — RAGAS 4 metric × **A/B: hybrid+rerank vs dense-only** | S | `results.md` có bảng điểm + worst performers |
| 5 | Tích hợp `retrieve()` + `generate_with_citation()` vào `app.py` | Q | Không import vòng, chạy 1 lệnh |
| 6 | Viết mục kiến trúc + phân công trong 2 README | Q | Đủ theo yêu cầu chấm (3đ) |

**Rate limit RAGAS:** OpenRouter free rất dễ 429. Chạy thử **5 câu trước**, xác nhận
pipeline đúng rồi mới chạy full 16 câu.

---

### CP6 — Hoàn thiện & nộp bài (2:15–3:00)

| # | Ticket | Ai | Xong khi |
|---|--------|-----|----------|
| 1 | **F5-17** — `pytest` lại trên `main` sau khi merge hết | Q | 35/35 passed |
| 2 | ⭐ **F5-16** — deploy Hugging Face Spaces — **BONUS 4đ** | Q | URL Space chạy được |
| 3 | `streamlit run app.py` từ clone sạch | H | Không lỗi import |
| 4 | Chốt `results.md` | S | Đủ 4 metric, 2 config, worst performers |
| 5 | Dọn repo, kiểm tra `.gitignore` | T | `git status` sạch |

**Đệm 45 phút này là vùng dự trữ.** Nếu CP1–CP5 trượt, lấy giờ ở đây bù, ưu tiên:
(1) 35/35 test → (2) chatbot chạy → (3) `results.md` → (4) bonus.

---

## 7. Hướng Dẫn Test Trước Khi Push & Merge

### 7.1 Quy trình chuẩn cho MỌI ticket

```powershell
# 1. Luôn xuất phát từ main mới nhất
git checkout main
git pull origin main

# 2. Tạo branch theo tên ticket
git checkout -b F5-6-lexical-search

# ... code ...

# 3. TEST CỤC BỘ (xem lệnh riêng từng ticket ở 7.2)
$env:PYTHONIOENCODING="utf-8"
.\.venv\Scripts\python.exe -m pytest tests/test_individual.py::TestTask6 -v

# 4. Chạy TOÀN BỘ test — không được làm hỏng phần người khác
.\.venv\Scripts\python.exe -m pytest tests/test_individual.py -v

# 5. Kiểm tra không lọt file cấm
git status
git diff --stat

# 6. Push
git add src/task6_lexical_search.py
git commit -m "F5-6: lexical_search bang BM25 + TF-IDF"
git push -u origin F5-6-lexical-search
```

Rồi mở PR → gán Quang review → merge vào `main`.

### 7.2 Lệnh test riêng từng ticket

| Ticket | Ai | Lệnh test | Pass nghĩa là |
|--------|----|-----------|---------------|
| F5-3 | Q | `pytest tests/test_individual.py::TestTask3 -v` | Có `.md` ở cả `legal/` và `news/`, > 200 ký tự |
| F5-4 | T | `pytest tests/test_individual.py::TestTask4 -v` | Chunk không vượt `CHUNK_SIZE * 1.1` |
| F5-5 | T | `pytest tests/test_individual.py::TestTask5 -v` | List sorted desc, đủ key, tôn trọng `top_k` |
| F5-6 | S | `pytest tests/test_individual.py::TestTask6 -v` | Như trên **+ chunk khớp keyword phải điểm cao hơn** |
| F5-7 | S | `pytest tests/test_individual.py::TestTask7 -v` | Output re-sorted, có `score`, tôn trọng `top_k` |
| F5-8 | Q | `pytest tests/test_individual.py::TestTask8 -v` | `results[0]["source"] == "pageindex"` |
| F5-9 | Q | `pytest tests/test_individual.py::TestTask9 -v` | Không crash với query rác `"xyzabc123nonsense"` |
| F5-10 | H | `pytest tests/test_individual.py::TestTask10 -v` | `format_context()` có source, `generate_with_citation()` trả dict có `answer` |

⚠️ **Test có `skipTest`** — chưa implement thì test **SKIP chứ không FAIL**.
Đọc kỹ output: `4 passed` khác hẳn `1 passed, 3 skipped`. **Skipped = chưa xong = chưa được merge.**

### 7.3 Smoke test thủ công (chạy trước khi mở PR)

Test tự động không bắt được câu trả lời sai nội dung. Mỗi ticket kèm 1 lệnh mắt thường:

```powershell
$env:PYTHONIOENCODING="utf-8"

# F5-3 (Q)
.\.venv\Scripts\python.exe -X utf8 -m src.task3_convert_markdown
Get-ChildItem data\standardized -Recurse -Filter *.md | Measure-Object

# F5-4 (T)
.\.venv\Scripts\python.exe -X utf8 -m src.task4_chunking_indexing

# F5-5 / F5-6 — kết quả có ĐÚNG chủ đề không?
.\.venv\Scripts\python.exe -X utf8 -c "from src.task5_semantic_search import semantic_search; [print(round(r['score'],3), r['content'][:80]) for r in semantic_search('bao lau thi duoc hoan tien', 3)]"
.\.venv\Scripts\python.exe -X utf8 -c "from src.task6_lexical_search import lexical_search; [print(round(r['score'],3), r['content'][:80]) for r in lexical_search('hoan tien', 3)]"

# F5-9 (Q) — BẮT BUỘC: fallback có trigger thật không?
.\.venv\Scripts\python.exe -X utf8 -c "from src.task9_retrieval_pipeline import retrieve; r=retrieve('thoi tiet Ha Noi hom nay', 3); print(r[0].get('source'))"
# Kỳ vọng in 'pageindex'. Nếu in None/'hybrid' → đang so threshold với điểm RRF, SAI.

# F5-10 (H)
.\.venv\Scripts\python.exe -X utf8 -c "from src.task10_generation import generate_with_citation; r=generate_with_citation('Toi co the doi tra hang trong bao lau?'); print(r['answer'])"
# Mắt thường: câu trả lời PHẢI có [Nguồn, Năm], KHÔNG được bịa số ngày

# F5-11 (H)
.\.venv\Scripts\streamlit.exe run app.py
```

### 7.4 Checklist trước khi bấm Merge (Quang review)

- [ ] `pytest tests/test_individual.py -v` trên branch: **không FAIL**, số `passed` **không giảm** so với `main`
- [ ] Ticket của PR này không còn `skipped`
- [ ] Không đổi chữ ký hàm ở §3.2 (đổi → phải báo nhóm trước, không merge lén)
- [ ] Không commit: `.env`, `chroma_db/`, `.venv/`, `__pycache__/`, `scratch_fixture.py`
- [ ] Có smoke test 7.3 kèm output dán vào PR
- [ ] Không có `print()` debug rác, không có API key hardcode

### 7.5 Xử lý conflict

- File **không chồng lấn** giữa các role → conflict chủ yếu ở `requirements.txt` và 2 README.
- Ai đụng `requirements.txt` phải báo nhóm ngay (người khác phải cài lại).
- Conflict thì **rebase lên main**, đừng merge ngược:
  ```powershell
  git fetch origin
  git rebase origin/main
  # sửa conflict, rồi:
  git rebase --continue
  .\.venv\Scripts\python.exe -m pytest tests/test_individual.py -v   # chạy lại test SAU rebase
  git push --force-with-lease
  ```
- **Cấm `git push --force`** lên `main`. Chỉ `--force-with-lease` trên branch của mình.

---

## 8. Bản Đồ Điểm → Người Chịu Trách Nhiệm

### Task 1–10 — 50 điểm

| Task | Ticket | Điểm | Chủ trì | Trạng thái |
|------|--------|------|---------|-----------|
| 1 — Thu thập ≥3 văn bản chính sách | F5-1 | 3 | **Q** | ✅ 6 PDF |
| 2 — Crawl ≥5 bài viết | F5-2 | 3 | **Q** | ✅ 10 JSON |
| 3 — Convert markdown | F5-3 | 4 | **Q** | ⬜ |
| 4 — Chunking + indexing | F5-4 | 7 | **T** | ⬜ |
| 5 — Semantic search | F5-5 | 6 | **T** | ⬜ |
| 6 — Lexical search (BM25) | F5-6 | 6 | **S** | ⬜ |
| 7 — Reranking (RRF) | F5-7 | 6 | **S** | ⬜ |
| 8 — PageIndex vectorless | F5-8 | 4 | **Q** | ⬜ |
| 9 — Retrieval pipeline + fallback | F5-9 | 7 | **Q** | ⬜ |
| 10 — Generation có citation | F5-10 | 4 | **H** | ⬜ |

Tổng theo người: **Q 21đ** (6 đã xong) · **T 13đ** · **S 12đ** · **H 4đ**
(H bù lại bằng 11đ bài nhóm ở chatbot).

### Bài nhóm — 30 điểm

| Tiêu chí | Ticket | Điểm | Chủ trì |
|----------|--------|------|---------|
| RAG Chatbot demo hoạt động | F5-11 | 8 | **H** |
| Tích hợp pipeline Task 1–10 | F5-9 | 4 | **Q** |
| Kiến trúc rõ ràng + README | F5-17 | 3 | **Q** |
| Chất lượng câu trả lời (citation, đúng nội dung) | F5-10 | 3 | **H** |
| Golden dataset ≥15 Q&A | F5-12 | 3 | **cả 4** |
| Eval ≥4 metrics | F5-13 | 4 | **S** |
| A/B ≥2 configs + phân tích | F5-13 | 3 | **S** |
| Báo cáo worst performers | F5-13 | 2 | **S** |

Tổng theo người: **H 11đ** · **S 9đ** · **Q 7đ** · **cả 4 3đ**

### 8.4. ⭐ BONUS — 20 điểm (LÀM SAU CÙNG)

> 🚫 **Quy tắc cứng: còn bất kỳ ticket nào của 50đ (Task 1–10) chưa xanh → CẤM làm bonus.**
> Bonus chỉ đáng làm khi phần bắt buộc đã an toàn. 3đ bonus không bù nổi 7đ Task 9 bị mất.

| ⭐ | Tiêu chí | Ticket | Điểm | Chủ trì | Điều kiện được bắt đầu | Rẻ/đắt |
|----|----------|--------|------|---------|------------------------|--------|
| ⭐1 | TF-IDF song song BM25 + giải thích cơ chế trong docstring/README | **F5-6** | **5** | S | F5-6 (BM25) đã pass | 🟢 **Rẻ nhất** — cùng file, ~10 phút |
| ⭐2 | HyDE / Query Expansion | **F5-14** | **5** | T | F5-5 đã pass | 🟡 Trung bình — cần thêm 1 LLM call |
| ⭐3 | Conversation memory multi-turn | **F5-15** | **3** | H | F5-11 chạy được | 🟢 Rẻ — `st.session_state` |
| ⭐4 | UI/UX: source + score + highlight | **F5-15** | **3** | H | F5-11 chạy được | 🟢 Rẻ — làm luôn khi dựng UI |
| ⭐5 | Deploy Hugging Face Spaces | **F5-16** | **4** | Q | F5-11 xong hết | 🔴 Đắt — dễ vỡ phút chót, làm cuối cùng |

Tổng theo người: **H 6đ** · **S 5đ** · **T 5đ** · **Q 4đ**

**Thứ tự nhặt điểm nếu thiếu thời gian:** ⭐1 (5đ, 10 phút) → ⭐3 + ⭐4 (6đ, làm sẵn trong UI)
→ ⭐2 (5đ) → ⭐5 (4đ, bỏ được nếu gấp).
Chỉ cần ⭐1 + ⭐3 + ⭐4 là đã có **11/20đ bonus** với công sức rất thấp.

### 📊 Tổng cộng cả 3 phần

| | Q (Quang) | T (Tường) | H (Hân) | S (Sáng) |
|---|---|---|---|---|
| Task 1–10 | 21 | 13 | 4 | 12 |
| Bài nhóm | 7 | 0 | 11 | 9 |
| Bonus | 4 | 5 | 6 | 5 |
| Golden dataset (chia đều) | 0.75 | 0.75 | 0.75 | 0.75 |
| **TỔNG** | **32.75** | **18.75** | **21.75** | **26.75** |

Q cao hơn vì đã hoàn thành 6đ (Task 1–2) và gánh vai điều phối/review;
T thấp nhất về điểm nhưng **F5-4 là ticket nặng nhất về thời gian** (tải model 2.2GB + index)
và là nút thắt chặn 2 người khác.

---

## 9. Rủi Ro & Phương Án Dự Phòng

| Rủi ro | Dấu hiệu | Xử lý | Ai |
|--------|----------|-------|-----|
| **Embed 1.081 chunk quá lâu** (corpus to 2.5× sau khi đổi chủ đề) | CP2 quá 10 phút chưa index xong | Đổi `all-MiniLM-L6-v2` (~3–5 ph) hoặc `EMBEDDING_PROVIDER=google` — bảng so sánh ở §1.5 | T |
| Tải `bge-m3` quá lâu (~2.2GB) | Chưa tải xong khi tới CP2 | Đừng chờ: chuyển thẳng sang MiniLM/Google, ghi lý do vào comment | T |
| Golden dataset vẫn hỏi theo chủ đề cũ | Câu hỏi toàn về đơn hàng, không có luật/thuế | Dùng đúng 4 nhóm chủ đề ở §1.5, mỗi người 4 câu | S |
| PageIndex không đăng ký/hết quota | F5-8 lỗi 401/429 | Fallback vectorless tự viết theo heading `.md` | Q |
| RAGAS dính 429 | Eval treo giữa chừng | Giảm còn 5–8 câu, thêm `time.sleep`, retry | S |
| Fallback F5-9 không trigger | Query lạc đề vẫn ra kết quả hybrid | So threshold với **cosine gốc** `dense_results[0]["score"]`, không phải điểm RRF | Q |
| `UnicodeEncodeError` trên Windows | Crash khi print tiếng Việt | `$env:PYTHONIOENCODING="utf-8"` hoặc `python -X utf8` | cả nhóm |
| Đổi dữ liệu nhưng kết quả cũ còn | Search trả chunk lạ | Xoá `chroma_db/` rồi chạy lại F5-4 | T |
| Ai đó đổi chữ ký hàm giữa chừng | PR người khác bỗng đỏ | Chữ ký ở §3.2 là bất biến; muốn đổi phải báo nhóm trước | Q gác |
| Một người xong sớm, người khác kẹt | Có người ngồi chơi | Áp dụng **quy tắc hỗ trợ chéo** ở §1 — xong việc là qua giúp ngay theo bảng ưu tiên | Q điều phối |
| Chưa đủ 35/35 test khi tới CP4 | pytest còn FAIL/skipped | **Cả 4 dừng việc riêng**, gộp sức fix cho đủ 50đ rồi mới quay lại | cả nhóm |

---

## 10. Hướng Dẫn Dùng AI Coding Agent (Codex / Claude / Antigravity / Copilot)

Cả nhóm được dùng agent, nhưng **agent viết sai kiểu là hỏng bài của 3 người còn lại**.
Mục này chuẩn hoá cách dùng để không ai phá hợp đồng interface ở §3.

### 10.1. File ngữ cảnh — đã tạo sẵn, không phải viết lại

| File | Dùng cho | Nội dung |
|------|----------|----------|
| **`AGENTS.md`** | **Codex, Antigravity** (và mọi agent đọc chuẩn AGENTS.md) | Nguồn sự thật: môi trường, luật cứng, hợp đồng dữ liệu, 2 cái bẫy, quy trình test |
| **`CLAUDE.md`** | **Claude Code** | Trỏ về `AGENTS.md` + tóm tắt 5 điều dễ sai |
| **`.github/copilot-instructions.md`** | **GitHub Copilot** (VS Code / JetBrains) | Bản rút gọn của `AGENTS.md` |

Cả 3 file **đã commit trong repo** → ai clone về là agent tự đọc, không cần cấu hình thêm.
Nếu tool của bạn dùng tên file khác (đọc doc của tool), tạo file đó **trỏ về `AGENTS.md`**,
đừng chép nội dung ra nhiều bản — sẽ lệch nhau.

### 10.2. Khởi động theo từng tool

| Tool | Cách bắt đầu | Ghi chú |
|------|--------------|---------|
| **Claude Code** | `cd` vào repo → `claude` → tự đọc `CLAUDE.md` | Dùng plan mode để duyệt trước khi cho sửa |
| **Codex** | Mở repo → agent tự đọc `AGENTS.md` | Yêu cầu nó chạy `pytest` sau mỗi thay đổi |
| **Antigravity** | Mở workspace → giao task qua Agent Manager, trỏ vào `AGENTS.md` | Kiểm lại diff trước khi accept, đừng auto-accept hàng loạt |
| **Copilot** | VS Code: Copilot Chat / Agent mode trong repo | Đọc `.github/copilot-instructions.md`; tab-completion **không** đọc file này → tự canh |

### 10.3. Mẫu prompt cho từng ticket — copy thẳng vào agent

Mỗi prompt đã gài sẵn 3 thứ: phạm vi file, ràng buộc, và cách tự kiểm chứng.

**F5-3 (Q) — convert markdown**
```
Đọc AGENTS.md. Hoàn thiện src/task3_convert_markdown.py: dùng MarkItDown convert
data/landing/legal/*.pdf và data/landing/news/*.json sang data/standardized/{legal,news}/*.md,
giữ nguyên cấu trúc thư mục con. File JSON lấy trường content_markdown và ghi kèm metadata
(url, title, date_crawled) ở đầu file .md.
CHỈ sửa file này. Xong thì chạy:
  .\.venv\Scripts\python.exe -X utf8 -m src.task3_convert_markdown
  .\.venv\Scripts\python.exe -m pytest tests/test_individual.py::TestTask3 -v
và cho tôi xem output. Nếu test skipped chứ không passed, sửa tiếp.
```

**F5-4 (T) — chunking & indexing**
```
Đọc AGENTS.md. Hoàn thiện src/task4_chunking_indexing.py: 4 hàm load_documents,
chunk_documents, embed_chunks, index_to_vectorstore.
GIỮ NGUYÊN CHUNK_SIZE=800, CHUNK_OVERLAP=100, EMBEDDING_MODEL="BAAI/bge-m3",
COLLECTION_NAME="ecommerce_support_docs" — không được đổi.
Dùng RecursiveCharacterTextSplitter và ChromaDB PersistentClient tại chroma_db/.
Mỗi chunk phải mang metadata source/title/customer_role lấy từ file gốc.
CHỈ sửa file này. Xong chạy pytest tests/test_individual.py::TestTask4 -v.
```

**F5-5 (T) — semantic search**
```
Đọc AGENTS.md. Hoàn thiện semantic_search() trong src/task5_semantic_search.py.
Trả về list[{"content","score","metadata"}] sorted theo score giảm dần, len <= top_k.
QUAN TRỌNG: score phải là COSINE SIMILARITY thang [0,1], không phải distance.
ChromaDB trả distance → phải chuyển: similarity = 1 - distance.
CHỈ sửa file này. Xong chạy pytest tests/test_individual.py::TestTask5 -v, rồi chạy
smoke test ở PLAN.md §7.3 và cho tôi xem điểm số thực tế.
```

**F5-6 (S) — lexical search + TF-IDF (bonus)**
```
Đọc AGENTS.md. Hoàn thiện src/task6_lexical_search.py: build_bm25_index() và
lexical_search() dùng rank_bm25.BM25Okapi, đọc corpus từ data/standardized/**/*.md.
Trả đúng shape {"content","score","metadata"} sorted desc.
Thêm hàm tfidf_search() dùng sklearn TfidfVectorizer (bonus 5đ), và viết docstring
giải thích cơ chế TF-IDF khác BM25 chỗ nào (saturation tần suất + chuẩn hoá độ dài).
CHỈ sửa file này. Xong chạy pytest tests/test_individual.py::TestTask6 -v.
Lưu ý test đòi: chunk khớp keyword phải có điểm CAO HƠN chunk không khớp.
```

**F5-7 (S) — RRF rerank**
```
Đọc AGENTS.md. Hoàn thiện rerank_rrf() và rerank() trong src/task7_reranking.py.
RRF(d) = Σ 1/(k + rank), k=60, rank tính từ 1.
Gộp nhiều ranked list theo key là item["content"], cộng dồn điểm, sort giảm dần, cắt top_k.
CHỈ sửa file này. Test bằng 2 list giả (fixture ở PLAN.md §3.4) — KHÔNG cần ChromaDB.
Xong chạy pytest tests/test_individual.py::TestTask7 -v.
```

**F5-8 (Q) — PageIndex vectorless**
```
Đọc AGENTS.md. Hoàn thiện src/task8_pageindex_vectorless.py: upload_documents() và
pageindex_search(). Kết quả BẮT BUỘC có "source": "pageindex".
Nếu không có PAGEINDEX_API_KEY hoặc API lỗi, fallback sang chế độ tự viết: duyệt heading
của data/standardized/**/*.md, chấm điểm bằng keyword overlap, vẫn gắn source="pageindex".
Ghi rõ lý do dùng fallback trong docstring. CHỈ sửa file này.
Xong chạy pytest tests/test_individual.py::TestTask8 -v.
```

**F5-9 (Q) — retrieval pipeline** ⚠️ prompt quan trọng nhất
```
Đọc AGENTS.md, đặc biệt mục "2 cái bẫy đã biết".
Hoàn thiện retrieve() trong src/task9_retrieval_pipeline.py:
1. Chạy semantic_search + lexical_search
2. Merge bằng rerank_rrf
3. So sánh ngưỡng: PHẢI dùng dense_results[0]["score"] (cosine gốc, thang [0,1]),
   TUYỆT ĐỐI KHÔNG dùng điểm RRF đã fuse
4. Nếu cosine gốc < SCORE_THRESHOLD (0.48) → trả pageindex_search()
5. Trả top_k
CHỈ sửa file này. Xong chạy pytest tests/test_individual.py::TestTask9 -v VÀ smoke test:
  python -X utf8 -c "from src.task9_retrieval_pipeline import retrieve; print(retrieve('thoi tiet Ha Noi hom nay',3)[0].get('source'))"
Phải in ra 'pageindex'. Nếu không, logic ngưỡng đang sai — sửa lại.
```

**F5-10 (H) — generation có citation**
```
Đọc AGENTS.md. Hoàn thiện src/task10_generation.py:
- reorder_for_llm(): pattern front + back[::-1] để chống lost-in-the-middle
- format_context(): mỗi chunk kèm nhãn nguồn lấy từ metadata
- generate_with_citation(): gọi OpenRouter qua openai SDK (base_url openrouter),
  key từ os.getenv("OPENROUTER_API_KEY"), trả {"answer","sources","retrieval_source"}
Answer phải có citation dạng [Nguồn, Năm]; thiếu evidence thì trả
"I cannot verify this information". Giải thích lý do chọn TOP_P/TEMPERATURE trong comment.
CHỈ sửa file này. Xong chạy pytest tests/test_individual.py::TestTask10 -v.
```

**F5-11 (H) — Streamlit chatbot**
```
Đọc AGENTS.md. Viết app.py: giao diện chat Streamlit gọi
generate_with_citation() từ src.task10_generation.
Cần có: khung chat, sidebar chỉnh top_k, panel hiển thị source documents kèm score,
vài câu hỏi gợi ý, và conversation memory bằng st.session_state (bonus 3đ).
KHÔNG sửa file trong src/. Xong chạy: .\.venv\Scripts\streamlit.exe run app.py
```

**F5-13 (S) — RAGAS eval**
```
Đọc AGENTS.md. Viết group_project/evaluation/eval_pipeline.py:
đọc golden_dataset.json, chạy generate_with_citation() cho từng câu, đo 4 metric RAGAS
(faithfulness, answer_relevancy, context_recall, context_precision).
Chạy A/B 2 config: (A) hybrid + rerank, (B) dense-only — dùng tham số use_reranking của retrieve().
Xuất bảng điểm + top 3 worst performers ra group_project/evaluation/results.md.
Thêm time.sleep giữa các câu để tránh 429 của OpenRouter free.
Chạy thử 5 câu trước khi chạy full 16 câu.
```

### 10.4. Luật dùng agent — bắt buộc tuân thủ

1. **Đọc diff trước khi accept.** Agent hay "tiện tay" sửa file ngoài phạm vi → conflict với người khác.
2. **Bắt agent chạy `pytest` và dán output.** Không tin câu "đã xong" khi chưa thấy `passed`.
   Nhớ: `skipped` ≠ `passed`.
3. **Agent không được sửa `tests/test_individual.py`.** Nếu thấy nó đụng file này → revert ngay.
   Đây là file chấm điểm, sửa test cho vừa code là gian lận.
4. **Kiểm tra 3 hằng số** sau mỗi lần agent sửa `task4`/`task9`: 800 / 100 / 0.48.
   Agent rất hay "tối ưu" tự ý đổi về giá trị mặc định.
5. **Không để agent thêm dependency mới** vào `requirements.txt` mà không báo nhóm —
   người khác phải cài lại toàn bộ.
6. **Tự hiểu code trước khi merge.** Coach hỏi "vì sao chọn RRF k=60?", "vì sao ngưỡng 0.48?"
   mà không trả lời được thì mất điểm — agent viết hộ nhưng không thi hộ được.
7. **Với `retrieve()` và `generate_with_citation()`**: đọc kỹ từng dòng, đây là 2 hàm
   giám khảo soi nhiều nhất.

### 10.5. Prompt tự kiểm tra trước khi mở PR

Dán cho agent trước khi push:

```
Review lại thay đổi của bạn trên branch này, đối chiếu AGENTS.md:
1. Có đổi chữ ký hàm nào ở PLAN.md §3.2 không?
2. Có đụng file ngoài phạm vi ticket không?
3. Có sửa tests/test_individual.py không?
4. CHUNK_SIZE / CHUNK_OVERLAP / SCORE_THRESHOLD còn đúng 800 / 100 / 0.48 chứ?
5. Có hardcode API key, hoặc thêm .env / chroma_db/ vào git không?
6. Chạy pytest tests/test_individual.py -v và cho tôi biết chính xác bao nhiêu
   passed / failed / skipped.
Liệt kê vi phạm nếu có, đừng tự sửa vội.
```

---

## 11. Việc Kế Tiếp Ngay

| Ưu tiên | Ai | Việc | Thời gian |
|---------|----|------|-----------|
| 🔴 **1** | **S** | **F5-6** `lexical_search()` BM25 — `chroma_db/` sẵn rồi, **đang khoá 13đ** | 15 phút |
| 🟡 2 | **Q** | **F5-9** ngay khi F5-6 merge · đặt `SCORE_THRESHOLD ≈ 0,40` (số đo ở trên) | 30 phút |
| 🟢 3 | **H** | F5-11 `app.py` — nối `generate_with_citation()` thật | 25 phút |
| 🟢 3 | **Q** | 4 câu golden dataset nhóm "Thành lập & đăng ký KD" | 10 phút |
| ⬜ 4 | **S** | F5-13 chạy A/B thật sau khi có `retrieve()` | 20 phút |
| ⬜ 5 | **T** | Rảnh rồi → nhảy sang giúp F5-6 hoặc F5-11 (hỗ trợ chéo §1) | — |

**Trạng thái:** `pytest` **27 passed · 8 skipped · 0 failed** · **37/50 điểm**.
Xong: Task 1, 2, 3, 4, 5, 7, 8, 10 + golden dataset.
Còn: **Task 6 (6đ) + Task 9 (7đ)** — 8 test đang skip đúng là của 2 task này.

> **Tường đã xong phần của mình** (F5-4 + F5-5, 13đ). Theo quy tắc hỗ trợ chéo,
> Tường nên nhảy sang F5-6 cùng Sáng — đó là ticket duy nhất đang chặn cả nhóm.
