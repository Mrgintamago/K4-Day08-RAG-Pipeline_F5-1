"""
Task 2 — Crawl bài viết/hướng dẫn hỗ trợ khách hàng về thương mại điện tử.

Nguồn: Trung tâm trợ giúp công khai của Shopee Vietnam (help.shopee.vn),
robots.txt cho phép crawl toàn bộ (`Allow: /`).

Chủ đề: theo dõi đơn hàng, đổi phương thức thanh toán, bằng chứng hoàn tiền,
mua hàng xuyên biên giới — khớp với chủ đề K4 "E-commerce Policy / Customer Support".

Engine:
    Mặc định dùng HTTP thuần (`requests`) vì trang help.shopee.vn có server-side
    rendering: dữ liệu bài viết nằm sẵn trong `window["FORGE_SSR_DATA_MAP"]`,
    không cần trình duyệt headless.
    Chạy với cờ `--crawl4ai` để dùng Crawl4AI AsyncWebCrawler theo khuyến nghị
    của bài lab (cần `playwright install chromium`; tự fallback nếu thiếu).

Chạy:
    python -m src.task2_crawl_news
    python -m src.task2_crawl_news --crawl4ai
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from src.shopee_help import fetch_article

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

MIN_CONTENT_CHARS = 200  # bài ngắn hơn coi như crawl hỏng, bỏ qua


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# article_id -> (tên file, chủ đề, customer_role)
ARTICLES = {
    79215: ("track-shipping-status", "theo dõi đơn hàng", "buyer"),
    79472: ("check-order-status", "theo dõi đơn hàng", "buyer"),
    79128: ("change-payment-method-prepaid-order", "phương thức thanh toán", "buyer"),
    79198: ("available-payment-methods", "phương thức thanh toán", "buyer"),
    79467: ("refund-evidence-guide", "trả hàng & hoàn tiền", "buyer"),
    79233: ("submit-return-refund-request", "trả hàng & hoàn tiền", "buyer"),
    79470: ("track-international-order", "mua hàng xuyên biên giới", "buyer"),
    79556: ("international-order-delivery-time", "mua hàng xuyên biên giới", "buyer"),
    79491: ("lookup-tracking-number", "theo dõi đơn hàng", "buyer"),
    79545: ("pay-with-credit-debit-card", "phương thức thanh toán", "buyer"),
}

ARTICLE_URLS = [f"https://help.shopee.vn/portal/4/article/{aid}" for aid in ARTICLES]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from src.shopee_help import fetch_html_crawl4ai, parse_article

    article_id = url.rstrip("/").split("/")[-1].split("-")[0]
    html = await fetch_html_crawl4ai(url)
    article = parse_article(html, article_id)
    return {
        "url": url,
        "title": article["title"],
        "date_crawled": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "content_markdown": article["content_text"],
    }


def crawl_all(engine: str = "requests"):
    """Crawl toàn bộ bài viết trong ARTICLES."""
    setup_directory()

    saved, skipped = [], []
    for i, (article_id, (slug, topic, role)) in enumerate(ARTICLES.items(), 1):
        url = f"https://help.shopee.vn/portal/4/article/{article_id}"
        print(f"[{i}/{len(ARTICLES)}] Crawling: {url}")
        try:
            article = fetch_article(article_id, engine=engine)
        except Exception as exc:
            print(f"  ! Lỗi: {type(exc).__name__}: {exc} — bỏ qua")
            skipped.append(article_id)
            continue

        text = article["content_text"]
        if len(text) < MIN_CONTENT_CHARS:
            print(f"  ! Nội dung quá ngắn ({len(text)} ký tự) — có thể là trang SPA rỗng, bỏ qua")
            skipped.append(article_id)
            continue

        record = {
            "url": url,
            "title": article["title"],
            "date_crawled": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "content_markdown": text,
            "article_id": article["article_id"],
            "topic": topic,
            "customer_role": role,
            "breadcrumb": article["breadcrumb"],
            "source": "help.shopee.vn",
        }

        filepath = DATA_DIR / f"article_{i:02d}_{slug}.json"
        filepath.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath.name} ({filepath.stat().st_size:,} bytes, {len(text):,} ký tự)")
        saved.append(record)

    print(f"\n✓ Crawl xong: {len(saved)} bài lưu vào {DATA_DIR}")
    if skipped:
        print(f"⚠ Bỏ qua {len(skipped)} bài: {skipped}")
    return saved


if __name__ == "__main__":
    import sys

    engine = "crawl4ai" if "--crawl4ai" in sys.argv else "requests"
    crawl_all(engine=engine)
