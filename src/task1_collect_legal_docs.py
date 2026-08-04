"""
Task 1 — Thu thập văn bản pháp lý cho chủ đề "Trợ Lý Pháp Lý Khởi Nghiệp & TMĐT".

Hai nguồn bổ sung nhau:
    - vi.wikisource.org  → luật Việt Nam (toàn văn, phạm vi công cộng)
    - help.shopee.vn     → quy định/chính sách của sàn TMĐT

Nguồn: Trung tâm trợ giúp công khai của Shopee Vietnam (help.shopee.vn).
robots.txt của site cho phép crawl toàn bộ (`Allow: /`).

Các trang chính sách là HTML (không có sẵn PDF), nên script tải nội dung rồi
render thành PDF bằng fpdf2 để đúng yêu cầu "file gốc PDF/DOCX trong
data/landing/legal/".

Mỗi tài liệu được gắn metadata `customer_role` (`buyer`/`seller`/`both`) — yêu cầu
riêng của K4 Variant (kế thừa Lab 07), dùng cho benchmark query có metadata_filter.
Metadata được ghi kèm ở đầu trang PDF và trong file sidecar `_metadata.json`.

Chạy:
    python -m src.task1_collect_legal_docs
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.shopee_help import fetch_article

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Font Unicode có dấu tiếng Việt (fpdf2 mặc định chỉ hỗ trợ latin-1).
FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

# =============================================================================
# NGUỒN 1 — Quy định sàn TMĐT (help.shopee.vn)
# article_id -> (tên file, customer_role)
# =============================================================================
LEGAL_DOCS = {
    77251: ("returns-refund-policy-shopee", "buyer"),
    77244: ("privacy-policy-shopee", "both"),
    77246: ("product-listing-regulations-shopee", "seller"),
    77250: ("shipping-policy-shopee", "both"),
    77247: ("prohibited-restricted-products-policy-shopee", "seller"),
    140097: ("anti-fraud-policy-seller-shopee", "seller"),
    77245: ("ecommerce-platform-operating-rules-shopee", "seller"),
    77242: ("terms-of-service-shopee", "both"),
}

# =============================================================================
# NGUỒN 2 — Luật Việt Nam, toàn văn từ Wikisource (vi.wikisource.org)
#
# Chủ đề #2 trong SUGGESTED_TOPICS.md: "Trợ lý Pháp lý Khởi nghiệp & TMĐT" —
# tra cứu quy định khi bán hàng online, đăng ký hộ kinh doanh, thành lập công ty.
# Quy định sàn (nguồn 1) trả lời "Shopee bắt tôi làm gì", văn bản luật (nguồn 2)
# trả lời "pháp luật bắt tôi làm gì" — hai lớp bổ sung nhau, không trùng.
#
# ĐÃ THỬ VÀ LOẠI vanban.chinhphu.vn: PDF "bản ký số" ở đó là ẢNH SCAN, MarkItDown
# trích ra 0 ký tự → không chunk/embed được, còn làm Task 3 sinh .md rỗng.
# Chi tiết các nguồn đã thử: xem docstring src/wikisource_law.py.
#
# tên trang Wikisource -> (tên file, customer_role, chủ đề)
# =============================================================================
WIKISOURCE_DOCS = {
    "Luật Doanh nghiệp nước Cộng hòa xã hội chủ nghĩa Việt Nam 2020":
        ("luat-doanh-nghiep-2020", "seller", "thành lập doanh nghiệp"),
    "Luật Thương mại nước Cộng hòa xã hội chủ nghĩa Việt Nam 2005":
        ("luat-thuong-mai-2005", "both", "hoạt động thương mại"),
    "Luật Bảo vệ quyền lợi người tiêu dùng nước Cộng hòa xã hội chủ nghĩa Việt Nam 2010":
        ("luat-bao-ve-quyen-loi-nguoi-tieu-dung-2010", "both", "quyền người tiêu dùng"),
    "Luật Giao dịch điện tử nước Cộng hòa xã hội chủ nghĩa Việt Nam 2005":
        ("luat-giao-dich-dien-tu-2005", "both", "giao dịch điện tử"),
    "Luật Thuế thu nhập cá nhân nước Cộng hòa xã hội chủ nghĩa Việt Nam 2007":
        ("luat-thue-thu-nhap-ca-nhan-2007", "seller", "thuế"),
}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


def _pick(candidates: list[Path]) -> Path | None:
    return next((p for p in candidates if p.exists()), None)


def write_pdf(article: dict, customer_role: str, filepath: Path) -> None:
    """Render nội dung bài viết thành PDF UTF-8 (có dấu tiếng Việt)."""
    from fpdf import FPDF

    regular = _pick(FONT_CANDIDATES)
    bold = _pick(FONT_BOLD_CANDIDATES)
    if regular is None:
        raise RuntimeError("Không tìm thấy font TTF Unicode để render tiếng Việt")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("uni", "", str(regular))
    pdf.add_font("uni", "B", str(bold or regular))
    pdf.add_page()

    pdf.set_font("uni", "B", 15)
    pdf.multi_cell(0, 8, article["title"])
    pdf.ln(2)

    pdf.set_font("uni", "", 9)
    meta_lines = [
        f"Nguồn: {article['url']}",
        f"Chuyên mục: {' > '.join(article['breadcrumb']) or 'Chính sách Shopee'}",
        f"customer_role: {customer_role}",
        f"Ngày thu thập: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
    ]
    pdf.multi_cell(0, 5, "\n".join(meta_lines))
    pdf.ln(3)

    pdf.set_font("uni", "", 11)
    pdf.multi_cell(0, 6, article["content_text"])
    pdf.output(str(filepath))


def collect_wikisource_laws(manifest: list[dict]) -> None:
    """
    Lấy toàn văn luật từ Wikisource rồi render thành PDF vào data/landing/legal/.

    Render PDF (thay vì lưu .txt) để đúng yêu cầu Task 1 "lưu file gốc PDF/DOCX",
    và để Task 3 xử lý mọi tài liệu legal bằng cùng một đường MarkItDown.
    """
    from src.wikisource_law import fetch_law

    for i, (page_title, (slug, role, topic)) in enumerate(WIKISOURCE_DOCS.items(), 1):
        print(f"[{i}/{len(WIKISOURCE_DOCS)}] Tải toàn văn: {page_title[:55]} ...")
        try:
            law = fetch_law(page_title)
        except Exception as exc:
            print(f"  ! Lỗi: {type(exc).__name__}: {exc} — bỏ qua")
            continue

        text = law["content_text"]
        if len(text) < 2000:
            print(f"  ! Nội dung quá ngắn ({len(text)} ký tự) — bỏ qua")
            continue

        article = {
            "title": law["title"],
            "url": law["url"],
            "breadcrumb": ["Wikisource", "Luật Việt Nam"],
            "content_text": text,
        }
        filepath = DATA_DIR / f"{slug}.pdf"
        write_pdf(article, role, filepath)

        print(f"  ✓ {filepath.name} ({filepath.stat().st_size:,} bytes, "
              f"{len(text):,} ký tự, {law['n_pages']} trang)")

        manifest.append({
            "file": filepath.name,
            "title": law["title"],
            "url": law["url"],
            "customer_role": role,
            "topic": topic,
            "source": "vi.wikisource.org",
            "doc_type": "legal_document",
            "date_collected": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "chars": len(text),
        })


def collect_all(engine: str = "requests") -> list[dict]:
    setup_directory()

    manifest = []
    for i, (article_id, (slug, role)) in enumerate(LEGAL_DOCS.items(), 1):
        print(f"[{i}/{len(LEGAL_DOCS)}] Tải chính sách {article_id} ...")
        article = fetch_article(article_id, engine=engine)

        filepath = DATA_DIR / f"{slug}.pdf"
        write_pdf(article, role, filepath)

        size = filepath.stat().st_size
        print(f"  ✓ {filepath.name} ({size:,} bytes) — {article['title'][:60]}")

        manifest.append(
            {
                "file": filepath.name,
                "article_id": article["article_id"],
                "title": article["title"],
                "url": article["url"],
                "customer_role": role,
                "source": "help.shopee.vn",
                "doc_type": "platform_policy",
                "date_collected": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "chars": len(article["content_text"]),
            }
        )

    print("\n--- Luật Việt Nam, toàn văn (vi.wikisource.org) ---")
    collect_wikisource_laws(manifest)

    (DATA_DIR / "_metadata.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ Đã lưu {len(manifest)} văn bản + _metadata.json")
    return manifest


if __name__ == "__main__":
    import sys

    engine = "crawl4ai" if "--crawl4ai" in sys.argv else "requests"
    collect_all(engine=engine)
