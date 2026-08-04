"""
Task 1 — Thu thập văn bản chính sách thương mại điện tử / hỗ trợ khách hàng.

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

# article_id -> (tên file, customer_role)
LEGAL_DOCS = {
    77251: ("returns-refund-policy-shopee", "buyer"),
    77244: ("privacy-policy-shopee", "both"),
    77246: ("product-listing-regulations-shopee", "seller"),
    77250: ("shipping-policy-shopee", "both"),
    77247: ("prohibited-restricted-products-policy-shopee", "seller"),
    140097: ("anti-fraud-policy-seller-shopee", "seller"),
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
                "date_collected": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                "chars": len(article["content_text"]),
            }
        )

    (DATA_DIR / "_metadata.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ Đã lưu {len(manifest)} văn bản chính sách + _metadata.json")
    return manifest


if __name__ == "__main__":
    import sys

    engine = "crawl4ai" if "--crawl4ai" in sys.argv else "requests"
    collect_all(engine=engine)
