# F5-16 — Deploy chatbot online

Ticket bonus ⭐ **4 điểm**. Tiêu chí chấm trong `README.md`:
> *"Deploy chatbot online (Hugging Face Spaces / Render / ...)"*

Tiêu chí cho phép nhiều nền tảng — quan trọng là **có URL công khai chạy được**.

---

## ⛔ Hugging Face Spaces KHÔNG dùng được nữa

Đã thử thật ngày 04/08/2026, gặp 2 rào chắn:

```
POST /api/repos/create  {"sdk": "streamlit"}
→ 400  Invalid option: expected one of "gradio"|"docker"|"static"

POST /api/repos/create  {"sdk": "gradio"}
→ 402  Static Spaces are free for everyone, but hosting Gradio and Docker
       Spaces on free cpu-basic requires a PRO subscription.
```

1. **`streamlit` không còn là SDK hợp lệ** cho Space tạo mới.
2. **Gradio/Docker Space trên CPU free giờ cần tài khoản PRO trả phí.** Chỉ Static
   Space còn miễn phí, mà Static chỉ phục vụ HTML/JS tĩnh — app Streamlit cần
   Python chạy phía server nên không dùng được.

YAML header `sdk: streamlit` trong `README.md` là di sản từ starter template, viết
khi HF còn hỗ trợ. **Giữ lại cũng vô hại**, nhưng đừng trông chờ nó hoạt động.

---

## ✅ Dùng Streamlit Community Cloud thay thế

Miễn phí, do chính Streamlit vận hành, deploy thẳng từ GitHub repo — hợp nhất với app này.

### Bước 1 — Đăng nhập

https://share.streamlit.io → **Sign in with GitHub** (tài khoản `Mrgintamago`).
Cấp quyền đọc repo; repo private vẫn deploy được.

### Bước 2 — Tạo app

**Create app** → **Deploy a public app from GitHub** rồi điền:

| Trường | Giá trị |
|--------|---------|
| Repository | `Mrgintamago/K4-Day08-RAG-Pipeline_F5-1` |
| Branch | **`hf-space`** ← không phải `main`, xem lý do bên dưới |
| Main file path | `app.py` |
| App URL | tuỳ chọn, ví dụ `tro-ly-phap-ly-tmdt` |

### Bước 3 — Khai secrets

**Advanced settings → Secrets**, dán vào (định dạng TOML):

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
PAGEINDEX_API_KEY = "..."
```

`PAGEINDEX_API_KEY` là tuỳ chọn — thiếu thì `pageindex_search()` tự chuyển sang
fallback cục bộ, app vẫn chạy.

⚠️ **Không commit `.env`.** File đó đang bị `.gitignore` chặn, giữ nguyên như vậy.

### Bước 4 — Deploy

Bấm **Deploy**, chờ khoảng **5–10 phút**. Xem tiến trình ở panel log bên phải.

Lần khởi động đầu app tải model `paraphrase-multilingual-MiniLM-L12-v2` (~470MB)
từ HF Hub. Các lần sau đã cache.

---

## Vì sao deploy nhánh `hf-space` chứ không phải `main`

Khác `main` **đúng một file**: `requirements.txt`.

| | `main` | `hf-space` |
|---|---|---|
| Số gói | 21 | **9** |
| Mục đích | Giám khảo chạy toàn bộ pipeline Task 1–13 | Chỉ chạy chatbot |

Gói bị loại và lý do:

| Gói | Chỉ dùng ở | Vì sao bỏ |
|-----|-----------|-----------|
| `crawl4ai` | Task 2 | Kéo theo `playwright` + `patchright` (~75MB) và cần tải Chromium — build rất lâu, dễ timeout, mà data đã crawl xong từ lâu |
| `markitdown[pdf]` | Task 3 | Data đã convert, nằm sẵn trong `data/standardized/` |
| `fpdf2` | Task 1, upload PageIndex | Tài liệu đã upload lên PageIndex rồi |
| `ragas`, `datasets`, `langchain`, `langchain-community`, `langchain-openai` | Task 13 | Evaluation chạy ở máy cá nhân, không phải trên server |
| `pytest` | Test | Không chạy test trên server |

9 gói còn lại resolve ra **127 package** — đã verify bằng `uv pip compile`.

### Cập nhật app sau này

```powershell
git checkout hf-space
git merge main --no-edit
# Nếu conflict ở requirements.txt: GIỮ BẢN GỌN của hf-space
git checkout --ours requirements.txt && git add requirements.txt && git commit --no-edit
git push origin hf-space
```

Streamlit Cloud tự deploy lại khi nhánh có commit mới.

---

## Vì sao `chroma_db/` phải nằm trong repo

Server **không chạy** Task 4 lúc khởi động. Không có sẵn index thì chatbot lên được
nhưng không trả lời được câu nào.

`chroma_db/` (33MB, 36 file, lớn nhất 21MB) đã commit từ trước — dưới ngưỡng cảnh
báo 50MB/file của GitHub. Kiểm tra: `git ls-files chroma_db | wc -l` phải ra **36**.

---

## Nếu deploy fail — 3 lỗi hay gặp

| Log báo | Nguyên nhân | Cách sửa |
|---------|-------------|----------|
| `Error installing requirements` | Đang deploy nhầm nhánh `main` (21 gói) | Đổi branch sang `hf-space` trong Settings |
| `OPENROUTER_API_KEY is None` | Quên khai secrets | Settings → Secrets, dán TOML ở Bước 3 |
| App chạy nhưng không tìm được gì | `chroma_db/` không lên repo | `git ls-files chroma_db \| wc -l` phải ra 36 |

---

## Phương án dự phòng nếu Streamlit Cloud cũng vướng

**Render.com** — free tier, cần thêm `render.yaml` hoặc cấu hình Web Service:

```yaml
services:
  - type: web
    name: tro-ly-phap-ly-tmdt
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Free tier của Render ngủ sau 15 phút không dùng, lần gọi đầu sau đó mất ~30 giây
để đánh thức — chấp nhận được với mục đích demo.
