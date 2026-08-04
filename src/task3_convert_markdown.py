"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install "markitdown[pdf]"
    # Lưu ý: cần extra [pdf] để convert được file PDF. Chỉ "pip install markitdown"
    # (không có extra) sẽ báo MissingDependencyException khi convert PDF, dù JSON/DOCX
    # vẫn convert bình thường.

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import re
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _build_header(title: str, url: str, date: str, extra: dict | None = None) -> str:
    """
    Header metadata đặt ở đầu mỗi file .md.

    Vì sao cần: Task 4 chunk file này rồi gắn metadata cho từng chunk, Task 10 phải in
    citation `[Nguồn, Năm]`. Ghi metadata ngay trong file giúp cả 2 bước lấy được nguồn
    mà không phải mở lại file gốc ở data/landing/.
    """
    lines = [f"# {title or 'Unknown'}", ""]
    lines.append(f"**Source:** {url or 'N/A'}")
    lines.append(f"**Crawled:** {date or 'N/A'}")
    for key, value in (extra or {}).items():
        if value:
            lines.append(f"**{key}:** {value}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _clean(text: str) -> str:
    """Bỏ dòng trống thừa do MarkItDown sinh ra khi tách trang PDF."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_pdf_meta_block(text: str) -> str:
    """
    Bỏ khối metadata mà Task 1 đã in vào đầu trang PDF (tiêu đề, Nguồn, Chuyên mục,
    customer_role, Ngày thu thập).

    Vì sao: `_build_header()` đã ghi lại đúng những trường đó ở đầu file .md rồi. Giữ cả
    hai làm chunk đầu tiên của mỗi tài liệu bị lặp URL/tiêu đề — vừa tốn chỗ trong
    chunk 800 ký tự, vừa làm nhiễu điểm BM25 ở Task 6 (từ khoá trùng lặp).
    """
    marker = "Ngày thu thập:"
    idx = text.find(marker)
    if idx == -1:
        return text
    # Cắt từ sau hết dòng "Ngày thu thập: ..." — phần còn lại là nội dung chính sách thật.
    end_of_line = text.find("\n", idx)
    return text[end_of_line + 1 :] if end_of_line != -1 else text


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    # _metadata.json do Task 1 sinh ra — tra ngược title/url/customer_role theo tên file.
    meta_path = legal_dir / "_metadata.json"
    meta_by_file = {}
    if meta_path.exists():
        for item in json.loads(meta_path.read_text(encoding="utf-8")):
            meta_by_file[item["file"]] = item

    count = 0
    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            result = md.convert(str(filepath))

            meta = meta_by_file.get(filepath.name, {})
            header = _build_header(
                title=meta.get("title", filepath.stem),
                url=meta.get("url", "N/A"),
                date=meta.get("date_collected", "N/A"),
                extra={
                    "customer_role": meta.get("customer_role", "both"),
                    "doc_type": "policy",
                },
            )

            body = _clean(_strip_pdf_meta_block(result.text_content))
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(header + body, encoding="utf-8")
            print(f"  ✓ Saved: {output_path.name} ({output_path.stat().st_size:,} bytes)")
            count += 1

    print(f"→ {count} file chính sách đã convert")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))

            # File JSON đã chứa sẵn text sạch (Task 2 parse từ SSR data của help.shopee.vn),
            # nên không cần đưa qua MarkItDown — chỉ ghép header + nội dung.
            header = _build_header(
                title=data.get("title", "Unknown"),
                url=data.get("url", "N/A"),
                date=data.get("date_crawled", "N/A"),
                extra={
                    "customer_role": data.get("customer_role", "buyer"),
                    "topic": data.get("topic", ""),
                    "doc_type": "support_article",
                },
            )

            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(
                header + _clean(data.get("content_markdown", "")), encoding="utf-8"
            )
            print(f"  ✓ Saved: {output_path.name} ({output_path.stat().st_size:,} bytes)")
            count += 1

    print(f"→ {count} bài hướng dẫn đã convert")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n✓ Done! Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
