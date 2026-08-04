# F5-16 — Deploy lên Hugging Face Spaces

Ticket bonus ⭐ **4 điểm**. Chỉ làm khi 50đ Task 1–10 đã an toàn (hiện tại: 35/35 ✅).

---

## Vì sao cần nhánh riêng `hf-space`

`requirements.txt` trên `main` có **20 gói** vì bài lab cần đủ cả pipeline build data
lẫn evaluation. Nhưng lúc **chạy** chatbot thì chỉ cần 9 gói:

| Nhóm | Gói | Cần lúc chạy Space? |
|------|-----|---------------------|
| Chatbot | `streamlit` | ✅ |
| Retrieval | `chromadb`, `sentence-transformers`, `langchain-text-splitters`, `rank-bm25`, `scikit-learn` | ✅ |
| Generation | `openai`, `python-dotenv` | ✅ |
| Fallback | `pageindex` | ✅ |
| **Build data** | `crawl4ai`, `markitdown[pdf]`, `fpdf2` | ❌ — chỉ dùng Task 1–3, data đã crawl xong |
| **Evaluation** | `ragas`, `datasets`, `langchain`, `langchain-community`, `langchain-openai` | ❌ — chỉ dùng Task 13, chạy ở máy |
| **Test** | `pytest` | ❌ |

`crawl4ai` một mình kéo theo `playwright` + `patchright` (~75MB) và cần tải Chromium —
trên Space free thì vừa lâu vừa dễ timeout build, mà **không hề được dùng**.

Giữ `main` nguyên vẹn (giám khảo cần đủ 20 gói để chạy toàn bộ pipeline), chỉ nhánh
`hf-space` mới dùng bản gọn.

---

## Các bước

### 1. Tạo Space

Vào https://huggingface.co/new-space:
- **Owner**: tài khoản của bạn
- **Space name**: `tro-ly-phap-ly-tmdt` (hoặc tên khác)
- **License**: mit
- **SDK**: **Streamlit**
- **Hardware**: CPU basic (free)
- **Visibility**: Public

> README.md đã có sẵn YAML header cấu hình Space ở 10 dòng đầu (`sdk: streamlit`,
> `app_file: app.py`) nên không cần viết Dockerfile.

### 2. Lấy token

https://huggingface.co/settings/tokens → New token → quyền **Write**.

### 3. Push nhánh `hf-space` lên Space

```powershell
# Nhánh hf-space đã được tạo sẵn, chỉ cần push
git remote add hf https://huggingface.co/spaces/<USERNAME>/<SPACE-NAME>
git push hf hf-space:main
```

Khi hỏi mật khẩu thì dán **token** (không phải mật khẩu tài khoản).

### 4. Khai báo secrets trên Space

Settings → **Variables and secrets** → New secret:

| Tên | Bắt buộc? | Dùng để |
|-----|-----------|---------|
| `OPENROUTER_API_KEY` | ✅ | Sinh câu trả lời (Task 10) |
| `PAGEINDEX_API_KEY` | ⚪ tuỳ chọn | Fallback vectorless; thiếu thì tự dùng fallback cục bộ |

⚠️ **KHÔNG commit `.env`.** File đó đang được `.gitignore` chặn — giữ nguyên như vậy.

### 5. Chờ build

Khoảng **5–10 phút**. Xem tiến trình ở tab **Logs**.

Lần khởi động đầu tiên app phải tải model `paraphrase-multilingual-MiniLM-L12-v2`
(~470MB) từ HF Hub — nhanh vì cùng hạ tầng. Các lần sau đã cache.

---

## Vì sao `chroma_db/` phải được commit

Space **không chạy** Task 4 lúc khởi động, nên nếu không có sẵn index thì chatbot
lên được nhưng không trả lời được câu nào.

`chroma_db/` (33MB, 36 file, lớn nhất 21MB) đã commit vào repo từ trước — dưới ngưỡng
cảnh báo 50MB/file của cả GitHub lẫn HF. Space pull về là dùng ngay.

---

## Cập nhật Space sau này

```powershell
git checkout hf-space
git merge main              # lấy code mới từ main
# giải quyết conflict ở requirements.txt: GIỮ BẢN GỌN của hf-space
git push hf hf-space:main
```

---

## Nếu build fail — 3 lỗi hay gặp

| Log báo | Nguyên nhân | Cách sửa |
|---------|-------------|----------|
| `No space left on device` | Space free 16GB, `torch` + model chiếm nhiều | Đã bỏ `crawl4ai`/`ragas` rồi; nếu vẫn lỗi thì đổi sang embedding API (`EMBEDDING_PROVIDER=google`) để khỏi cài `sentence-transformers`+`torch` |
| `OPENROUTER_API_KEY` is None | Quên khai secret | Settings → Variables and secrets |
| Chatbot chạy nhưng không tìm được gì | `chroma_db/` không lên Space | `git ls-files chroma_db \| wc -l` phải ra 36 |
