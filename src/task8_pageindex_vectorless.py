"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — nó dựng cây cấu trúc (chương/mục/tiêu đề)
của tài liệu rồi để LLM duyệt cây tìm phần liên quan, thay vì so khớp embedding.
Dùng làm fallback ở Task 9 khi hybrid search cho điểm cosine quá thấp.

Cách chạy:
    python -X utf8 -m src.task8_pageindex_vectorless            # upload + query thử
    python -X utf8 -m src.task8_pageindex_vectorless --debug    # in raw JSON response
    python -X utf8 -m src.task8_pageindex_vectorless --reupload # bỏ cache, upload lại

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
LEGAL_PDF_DIR = PROJECT_DIR / "data" / "landing" / "legal"
PDF_CACHE_DIR = PROJECT_DIR / "pageindex_pdfs"
DOC_IDS_PATH = PROJECT_DIR / "pageindex_doc_ids.json"

# Số tài liệu query song song mỗi lần fallback. PageIndex query theo từng doc_id, muốn
# tìm trên toàn corpus phải hỏi từng tài liệu → chạy song song cho đỡ chậm.
MAX_PARALLEL_DOCS = 6
POLL_TIMEOUT_SEC = 60
POLL_INTERVAL_SEC = 2


# =============================================================================
# Chuẩn bị PDF để upload
# =============================================================================

def _md_to_pdf(md_path: Path, out_path: Path) -> Path:
    """
    Convert 1 file markdown sang PDF đơn giản — PageIndex chỉ nhận PDF, không nhận .md.

    Dùng font Unicode hệ thống vì fpdf2 mặc định chỉ hỗ trợ latin-1, không in được dấu
    tiếng Việt.
    """
    from fpdf import FPDF

    font = next(
        (p for p in [Path("C:/Windows/Fonts/arial.ttf"),
                     Path("C:/Windows/Fonts/segoeui.ttf"),
                     Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")] if p.exists()),
        None,
    )
    if font is None:
        raise RuntimeError("Không tìm thấy font TTF Unicode để render tiếng Việt")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("uni", "", str(font))
    pdf.add_page()
    pdf.set_font("uni", "", 11)
    pdf.multi_cell(0, 6, md_path.read_text(encoding="utf-8"))
    pdf.output(str(out_path))
    return out_path


def _collect_pdfs() -> list[tuple[Path, dict]]:
    """
    Gom danh sách PDF cần upload kèm metadata.

    - `data/landing/legal/*.pdf` dùng thẳng, vốn đã là PDF do Task 1 tạo.
    - `data/standardized/news/*.md` phải convert sang PDF (cache ở pageindex_pdfs/).
    """
    PDF_CACHE_DIR.mkdir(exist_ok=True)
    items: list[tuple[Path, dict]] = []

    for pdf in sorted(LEGAL_PDF_DIR.glob("*.pdf")):
        items.append((pdf, {"source": pdf.name, "doc_type": "policy"}))

    for md in sorted((STANDARDIZED_DIR / "news").glob("*.md")):
        out = PDF_CACHE_DIR / f"{md.stem}.pdf"
        if not out.exists():
            _md_to_pdf(md, out)
        items.append((out, {"source": md.name, "doc_type": "support_article"}))

    return items


# =============================================================================
# Upload
# =============================================================================

def _client():
    from pageindex.client import PageIndexClient

    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Thiếu PAGEINDEX_API_KEY trong .env")
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def upload_documents(reupload: bool = False) -> dict:
    """
    Upload toàn bộ documents lên PageIndex, trả về mapping doc_id -> metadata.

    Kết quả cache tại `pageindex_doc_ids.json` để lần chạy sau không upload lại
    (mỗi lần upload tốn quota và mất vài chục giây xử lý phía PageIndex).
    """
    if DOC_IDS_PATH.exists() and not reupload:
        cached = json.loads(DOC_IDS_PATH.read_text(encoding="utf-8"))
        print(f"✓ Dùng lại {len(cached)} doc_id đã cache ({DOC_IDS_PATH.name})")
        return cached

    client = _client()
    doc_ids: dict[str, dict] = {}

    items = _collect_pdfs()
    for i, (pdf_path, meta) in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Uploading: {pdf_path.name}")
        resp = client.submit_document(str(pdf_path))
        doc_id = resp.get("doc_id") or resp.get("id")
        if not doc_id:
            print(f"  ! Không lấy được doc_id, response: {json.dumps(resp)[:200]}")
            continue
        doc_ids[doc_id] = meta
        print(f"  ✓ {doc_id}")

    DOC_IDS_PATH.write_text(json.dumps(doc_ids, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Đã upload {len(doc_ids)} tài liệu, lưu vào {DOC_IDS_PATH.name}")

    # PageIndex xử lý bất đồng bộ — chờ tài liệu sẵn sàng trước khi query.
    print("Chờ PageIndex xử lý xong...")
    for doc_id in doc_ids:
        deadline = time.time() + POLL_TIMEOUT_SEC
        while time.time() < deadline:
            try:
                if client.is_retrieval_ready(doc_id):
                    break
            except Exception:
                pass
            time.sleep(POLL_INTERVAL_SEC)
    print("✓ Sẵn sàng query")

    return doc_ids


def _load_doc_ids() -> dict:
    if DOC_IDS_PATH.exists():
        return json.loads(DOC_IDS_PATH.read_text(encoding="utf-8"))
    return {}


# =============================================================================
# Query
# =============================================================================

def _query_one_doc(client, doc_id: str, query: str, meta: dict, debug: bool = False) -> list[dict]:
    """Query 1 tài liệu, poll đến khi có kết quả, parse ra list chunk."""
    resp = client.submit_query(doc_id=doc_id, query=query)
    retrieval_id = resp.get("retrieval_id") or resp.get("id")
    if not retrieval_id:
        return []

    retrieval = None
    deadline = time.time() + POLL_TIMEOUT_SEC
    while time.time() < deadline:
        retrieval = client.get_retrieval(retrieval_id)
        if retrieval.get("status") in ("completed", "success", "done"):
            break
        if retrieval.get("status") in ("failed", "error"):
            return []
        time.sleep(POLL_INTERVAL_SEC)

    if not retrieval:
        return []
    if debug:
        print(json.dumps(retrieval, ensure_ascii=False, indent=2)[:3000])

    out = []
    for node in retrieval.get("retrieved_nodes", []):
        # relevant_contents là list LỒNG: list[list[{section_title, relevant_content}]]
        for group in node.get("relevant_contents", []):
            for item in group if isinstance(group, list) else [group]:
                if not isinstance(item, dict):
                    continue
                content = (item.get("relevant_content") or "").strip()
                if not content:
                    continue
                out.append({
                    "content": content,
                    "metadata": {
                        **meta,
                        "section": item.get("section_title", ""),
                        "doc_id": doc_id,
                    },
                })
    return out


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    doc_ids = _load_doc_ids()

    # Không có API key hoặc chưa upload → dùng fallback cục bộ, vẫn giữ đúng shape
    # để Task 9 không phải phân biệt hai nhánh.
    if not PAGEINDEX_API_KEY or not doc_ids:
        return _local_vectorless_search(query, top_k)

    try:
        client = _client()
        picked = list(doc_ids.items())[:MAX_PARALLEL_DOCS]
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOCS) as pool:
            batches = pool.map(
                lambda kv: _query_one_doc(client, kv[0], query, kv[1]), picked
            )
        results = [item for batch in batches for item in batch]
    except Exception as exc:
        print(f"  ! PageIndex lỗi ({type(exc).__name__}: {exc}) → dùng fallback cục bộ")
        return _local_vectorless_search(query, top_k)

    if not results:
        return _local_vectorless_search(query, top_k)

    # PageIndex KHÔNG trả score — nó chỉ trả các node đã được LLM chọn là liên quan.
    # Gán điểm giảm dần theo thứ hạng để Task 9/10 vẫn sort và cắt top_k được như
    # mọi ranker khác (đây là điểm giả lập, không so sánh trực tiếp với cosine được).
    for rank, item in enumerate(results, 1):
        item["score"] = 1.0 / rank
        item["source"] = "pageindex"

    return results[:top_k]


# =============================================================================
# Fallback cục bộ — dùng khi PageIndex không sẵn sàng
# =============================================================================

def _local_vectorless_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval tự viết, chạy khi PageIndex thiếu key / hết quota / lỗi mạng.

    Cùng tinh thần với PageIndex: KHÔNG dùng embedding, mà duyệt theo CẤU TRÚC tài liệu —
    tách mỗi file .md theo heading, rồi chấm điểm từng section bằng độ phủ từ khoá của
    câu hỏi (tiêu đề tính trọng số gấp đôi vì heading tóm tắt nội dung section).

    Không thay thế được PageIndex về chất lượng, nhưng giữ cho Task 9 luôn có nhánh
    fallback chạy được thay vì crash.
    """
    tokens = {t for t in re.findall(r"\w+", query.lower()) if len(t) > 1}
    if not tokens:
        return []

    scored = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")

        # Tách header metadata (phần trên dấu ---) khỏi nội dung
        header, _, body = text.partition("\n---\n")
        title_match = re.search(r"^#\s*(.+)$", header, re.M)
        url_match = re.search(r"\*\*Source:\*\*\s*(\S+)", header)
        role_match = re.search(r"\*\*customer_role:\*\*\s*(\S+)", header)

        # Cắt body theo heading; đoạn trước heading đầu tiên tính là "Mở đầu"
        sections = re.split(r"^(#{1,6}\s+.*|^\d+(?:\.\d+)*\.?\s+[A-ZĐÂÊÔƯÁÀẢÃẠ].*)$", body, flags=re.M)
        chunks: list[tuple[str, str]] = []
        current_title = "Mở đầu"
        buffer = sections[0] if sections else body
        for i in range(1, len(sections), 2):
            chunks.append((current_title, buffer))
            current_title = sections[i].strip().lstrip("#").strip()
            buffer = sections[i + 1] if i + 1 < len(sections) else ""
        chunks.append((current_title, buffer))

        for section_title, content in chunks:
            content = content.strip()
            if len(content) < 40:
                continue
            haystack = f"{section_title} {section_title} {content}".lower()
            hits = sum(1 for t in tokens if t in haystack)
            if hits == 0:
                continue
            scored.append((
                hits / len(tokens),
                {
                    "content": content[:1200],
                    "metadata": {
                        "source": md_file.name,
                        "title": title_match.group(1).strip() if title_match else md_file.stem,
                        "url": url_match.group(1) if url_match else "",
                        "customer_role": role_match.group(1) if role_match else "both",
                        "section": section_title,
                    },
                    "source": "pageindex",
                },
            ))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, item in scored[:top_k]:
        item["score"] = round(score, 4)
        results.append(item)
    return results


if __name__ == "__main__":
    import sys

    debug = "--debug" in sys.argv
    reupload = "--reupload" in sys.argv

    if not PAGEINDEX_API_KEY:
        print("⚠ Chưa có PAGEINDEX_API_KEY trong .env — chạy fallback cục bộ")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents(reupload=reupload)

    print("\nTest query:")
    results = pageindex_search("danh sách sản phẩm cấm đăng bán", top_k=3)
    for r in results:
        print(f"[{r['score']:.3f}] ({r['source']}) {r['metadata'].get('section','')[:40]}")
        print(f"        {r['content'][:120]}...")
