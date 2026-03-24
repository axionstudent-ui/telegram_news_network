import feedparser
import asyncio
import aiohttp

RSS_FEEDS = {
    "Al Jazeera": "https://www.aljazeera.net/aljazeerarss/a7c3d207-1647-498b-90e6-69d67a149c71/7a4239e3-861f-442a-9e8c-f05256e6d1fb",
    "BBC Arabic": "https://www.bbc.com/arabic/index.xml",
    "CNN Arabic": "https://arabic.cnn.com/rss/cnnarabic_world.rss",
    "Al Arabiya": "https://www.alarabiya.net/.mrss/ar/last-24-hours.xml",
    "RT Arabic": "https://arabic.rt.com/rss/",
    "Sky News Arabia": "https://www.skynewsarabia.com/rss/feeds/rss.xml"
}

async def fetch_rss_news():
    """Fetches the latest news from all configured RSS feeds."""
    news_items = []
    async with aiohttp.ClientSession() as session:
        for source, url in RSS_FEEDS.items():
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        for entry in feed.entries[:5]: # Take top 5 from each
                            news_items.append({
                                "text": entry.title + "\n" + getattr(entry, 'summary', ''),
                                "source_name": f"{source} (RSS)",
                                "link": getattr(entry, 'link', '')
                            })
            except Exception as e:
                print(f"RSS Fetch Error ({source}): {e}")
    return news_items
