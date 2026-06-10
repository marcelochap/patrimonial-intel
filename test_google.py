import sys, asyncio
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, ".")
from src.scrapers.google_search import GoogleSearchScraper

async def test():
    s = GoogleSearchScraper()
    items = await s.fetch("tributario", since_hours=48)
    print(f"Items encontrados: {len(items)}")
    for i in items[:5]:
        print(f"  [{i['source']}] {i['title'][:70]}")
        print(f"   {i['date']} | {i['link_status']}")

asyncio.run(test())
