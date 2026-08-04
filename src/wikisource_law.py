"""
Helper lấy TOÀN VĂN luật Việt Nam từ Wikisource tiếng Việt (vi.wikisource.org).

Vì sao KHÔNG dùng PDF của vanban.chinhphu.vn:
    Các PDF "bản ký số" trên datafiles.chinhphu.vn là **ảnh scan** — MarkItDown trích
    ra 0 ký tự (đã kiểm chứng với Luật Doanh nghiệp 2020, NĐ 52/2013, NĐ 68/2026).
    Không có lớp text thì không chunk/embed được, tức là vô dụng với RAG, và còn làm
    Task 3 sinh ra file .md rỗng khiến `test_converted_files_have_content` fail.
    Muốn dùng phải OCR (tesseract + gói tiếng Việt) — thêm binary ngoài Python cho cả
    nhóm, quá nặng so với lợi ích.

Các nguồn khác đã thử và loại:
    - thuvienphapluat.vn  → 403 Cloudflare
    - luatvietnam.vn      → paywall / Cloudflare
    - vbpl.vn             → đã đổi sang Next.js SPA, URL .aspx cũ trả 404
    - congbao.chinhphu.vn → trang chi tiết chỉ có metadata, nội dung nằm trong PDF scan

Wikisource thì: có toàn văn dạng text, API MediaWiki công khai, và văn bản quy phạm
pháp luật Việt Nam thuộc phạm vi công cộng (Điều 15 Luật Sở hữu trí tuệ) nên chia sẻ
lại được.

Lưu ý: một số luật dài được tách thành trang con theo chương
(`<Tên luật>/Chương I`, `/Chương II`, ...). `fetch_law()` tự gom hết trang con.
"""

from __future__ import annotations

import re
import time
from html import unescape

import requests

API = "https://vi.wikisource.org/w/api.php"
USER_AGENT = "K4-Day08-RAG-Lab/1.0 (student project, educational use)"
HEADERS = {"User-Agent": USER_AGENT}


def _api(params: dict, timeout: int = 30) -> dict:
    params = {**params, "format": "json"}
    resp = requests.get(API, headers=HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _page_text(title: str) -> str:
    """Lấy nội dung 1 trang dưới dạng plain text."""
    data = _api({"action": "parse", "page": title, "prop": "text", "redirects": 1})
    html = data.get("parse", {}).get("text", {}).get("*", "")
    if not html:
        return ""

    # Bỏ phần điều hướng/hộp thông tin của Wikisource, chỉ giữ nội dung luật
    text = re.sub(r"(?is)<(script|style|table)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r'(?is)<div class="(ws-noexport|noprint)[^"]*".*?</div>', " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|h[1-6])>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\[\s*sửa\s*\]", "", text)          # link "sửa" của MediaWiki
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def _subpages(title: str, limit: int = 60) -> list[str]:
    """Liệt kê trang con `<title>/...` (thường là từng chương của luật)."""
    data = _api({
        "action": "query", "list": "allpages",
        "apprefix": f"{title}/", "apnamespace": 0, "aplimit": limit,
    })
    pages = [p["title"] for p in data.get("query", {}).get("allpages", [])]

    # Sắp theo số La Mã trong "Chương X" để giữ đúng thứ tự văn bản
    roman = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}

    def roman_val(s: str) -> int:
        total, prev = 0, 0
        for ch in reversed(s.upper()):
            v = roman.get(ch, 0)
            total += -v if v < prev else v
            prev = max(prev, v)
        return total

    def key(t: str):
        m = re.search(r"/Chương\s+([IVXLC]+)", t)
        return (0, roman_val(m.group(1))) if m else (1, t)

    return sorted(pages, key=key)


def fetch_law(title: str, sleep: float = 0.3) -> dict:
    """
    Lấy toàn văn một văn bản luật, tự gom các trang con theo chương.

    Returns:
        {'title', 'url', 'content_text', 'n_pages'}
    """
    parts = [_page_text(title)]
    subs = _subpages(title)
    for sub in subs:
        time.sleep(sleep)  # lịch sự với API công cộng
        parts.append(f"\n\n## {sub.split('/', 1)[-1]}\n\n{_page_text(sub)}")

    content = "\n".join(p for p in parts if p).strip()
    return {
        "title": title,
        "url": "https://vi.wikisource.org/wiki/" + title.replace(" ", "_"),
        "content_text": content,
        "n_pages": 1 + len(subs),
    }
