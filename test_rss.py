import sys, asyncio
sys.path.insert(0, ".")
from src.scrapers.rss_scraper import RssScraper

async def test():
    s = RssScraper()
    items = await s.fetch("tributario", since_hours=48)
    print(f"Items encontrados: {len(items)}")
    for i in items[:3]:
        print(f"  [{i['source']}] {i['title'][:70]}")
        print(f"   {i['date']} | {i['link_status']} | {i['url'][:60]}")

asyncio.run(test())
