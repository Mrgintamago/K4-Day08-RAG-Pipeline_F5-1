"""
Helper dùng chung cho Task 1 & Task 2 — lấy nội dung bài viết từ Trung tâm trợ giúp
công khai của Shopee Vietnam (help.shopee.vn).

Vì sao cần helper riêng:
    Trang help.shopee.vn render bằng React nhưng CÓ server-side rendering: toàn bộ dữ liệu
    bài viết được nhúng sẵn trong HTML dưới dạng JSON tại biến
    `window["FORGE_SSR_DATA_MAP"]`. Parse trực tiếp khối JSON này cho nội dung sạch
    (tiêu đề + HTML thân bài), thay vì phải bóc tách DOM lẫn menu/nav/footer.

    robots.txt của help.shopee.vn cho phép crawl toàn bộ (`Allow: /`).

Hai engine fetch:
    - "crawl4ai": dùng AsyncWebCrawler (theo khuyến nghị của bài lab). Cần
      `playwright install chromium`.
    - "requests": HTTP thuần, nhanh hơn nhiều và đủ dùng vì trang có SSR.
      Được dùng làm fallback tự động khi crawl4ai không sẵn sàng.
"""

from __future__ import annotations

import json
import re
from html import unescape

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

ARTICLE_URL = "https://help.shopee.vn/portal/4/article/{article_id}"
SSR_KEY = 'window["FORGE_SSR_DATA_MAP"] = '


# ---------------------------------------------------------------------------
# Fetch HTML
# ---------------------------------------------------------------------------

def fetch_html_requests(url: str, timeout: int = 30) -> str:
    import requests

    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.text


async def fetch_html_crawl4ai(url: str) -> str:
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)
        if not result.success:
            raise RuntimeError(f"crawl4ai thất bại: {result.error_message}")
        return result.html


# ---------------------------------------------------------------------------
# Parse nội dung bài viết từ khối SSR JSON
# ---------------------------------------------------------------------------

def _extract_ssr_json(html: str) -> dict:
    """Cắt đúng object JSON gán cho window["FORGE_SSR_DATA_MAP"] (quét cân bằng ngoặc)."""
    start = html.find(SSR_KEY)
    if start < 0:
        raise ValueError("Không tìm thấy FORGE_SSR_DATA_MAP — trang có thể đã đổi cấu trúc")
    start += len(SSR_KEY)

    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(html)):
        ch = html[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : i + 1])
    raise ValueError("JSON SSR không đóng ngoặc hợp lệ")


def html_to_text(fragment: str) -> str:
    """Chuyển HTML thân bài thành plain text giữ được xuống dòng theo block."""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", fragment)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def parse_article(html: str, article_id: str | int) -> dict:
    """
    Trả về {'article_id', 'title', 'content_html', 'content_text', 'breadcrumb'}.
    """
    data = _extract_ssr_json(html)

    node = None
    for value in data.values():
        if isinstance(value, dict) and str(value.get("id")) == str(article_id) and value.get("content"):
            node = value
            break
    if node is None:  # bài viết duy nhất có trường content
        candidates = [v for v in data.values() if isinstance(v, dict) and v.get("content")]
        if not candidates:
            raise ValueError(f"Không tìm thấy nội dung bài {article_id} trong SSR data")
        node = candidates[0]

    breadcrumb = []
    m = re.search(r'"BreadcrumbList".*?"itemListElement":(\[.*?\])</script>', html, re.S)
    if m:
        try:
            breadcrumb = [it.get("name", "") for it in json.loads(m.group(1))]
        except json.JSONDecodeError:
            breadcrumb = []

    content_html = node["content"]
    return {
        "article_id": str(node.get("id", article_id)),
        "title": node.get("title", "").strip(),
        "content_html": content_html,
        "content_text": html_to_text(content_html),
        "breadcrumb": breadcrumb,
    }


def fetch_article(article_id: str | int, engine: str = "requests") -> dict:
    """
    Lấy 1 bài viết theo article_id.

    engine="crawl4ai" dùng AsyncWebCrawler (khuyến nghị của bài lab); nếu thiếu
    thư viện / chưa `playwright install chromium` thì tự động fallback sang requests.
    """
    url = ARTICLE_URL.format(article_id=article_id)

    html = None
    if engine == "crawl4ai":
        try:
            import asyncio

            html = asyncio.run(fetch_html_crawl4ai(url))
        except Exception as exc:  # thiếu browser binary, import lỗi, timeout...
            print(f"  ! crawl4ai lỗi ({type(exc).__name__}: {exc}) → fallback requests")

    if html is None:
        html = fetch_html_requests(url)

    article = parse_article(html, article_id)
    article["url"] = url
    return article
