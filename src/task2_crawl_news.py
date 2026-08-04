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


# article_id -> (tên file, chủ đề, customer_role, portal)
# portal 4 = trung tâm trợ giúp người mua, portal 10 = người bán/đối tác.
#
# Nửa dưới (thuế, hoá đơn, số dư) phục vụ chủ đề #2 "Pháp lý khởi nghiệp & TMĐT":
# đây là mặt vận hành thực tế của nghĩa vụ thuế mà Luật Thuế TNCN / Luật Doanh nghiệp
# quy định ở mức nguyên tắc — cặp "luật nói gì" + "trên sàn làm thế nào".
# Đồng thời cân lại phân bố customer_role: trước đó 10/10 bài news đều là buyer,
# khiến benchmark có metadata_filter=seller gần như không có tài liệu để retrieve.
ARTICLES = {
    # --- Người mua: vận hành đơn hàng ---
    79215: ("track-shipping-status", "theo dõi đơn hàng", "buyer", 4),
    79472: ("check-order-status", "theo dõi đơn hàng", "buyer", 4),
    79128: ("change-payment-method-prepaid-order", "phương thức thanh toán", "buyer", 4),
    79198: ("available-payment-methods", "phương thức thanh toán", "buyer", 4),
    79467: ("refund-evidence-guide", "trả hàng & hoàn tiền", "buyer", 4),
    79233: ("submit-return-refund-request", "trả hàng & hoàn tiền", "buyer", 4),
    79470: ("track-international-order", "mua hàng xuyên biên giới", "buyer", 4),
    79556: ("international-order-delivery-time", "mua hàng xuyên biên giới", "buyer", 4),
    79491: ("lookup-tracking-number", "theo dõi đơn hàng", "buyer", 4),
    79545: ("pay-with-credit-debit-card", "phương thức thanh toán", "buyer", 4),
    # --- Người bán / hộ kinh doanh: thuế, hoá đơn, dòng tiền ---
    79636: ("issue-einvoice-vat-for-order", "thuế & hoá đơn", "both", 4),
    103406: ("issue-einvoice-seller-service-fee", "thuế & hoá đơn", "seller", 4),
    165118: ("lookup-personal-tax-code", "thuế & hoá đơn", "seller", 10),
    180808: ("update-payment-and-tax-info", "thuế & hoá đơn", "seller", 10),
    178455: ("check-payment-tax-info-status", "thuế & hoá đơn", "seller", 10),
    79510: ("withdraw-balance-to-bank", "dòng tiền người bán", "seller", 4),
    79447: ("shopee-balance-faq", "dòng tiền người bán", "seller", 4),
    79046: ("product-warranty-policy", "bảo hành & trách nhiệm", "both", 4),
}

ARTICLE_URLS = [
    f"https://help.shopee.vn/portal/{meta[3]}/article/{aid}"
    for aid, meta in ARTICLES.items()
]


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
    for i, (article_id, (slug, topic, role, portal)) in enumerate(ARTICLES.items(), 1):
        url = f"https://help.shopee.vn/portal/{portal}/article/{article_id}"
        print(f"[{i}/{len(ARTICLES)}] Crawling: {url}")
        try:
            article = fetch_article(article_id, engine=engine, portal=portal)
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
