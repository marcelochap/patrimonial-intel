import sys, asyncio, json
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, ".")
from src.agents.investigador import main

asyncio.run(main())

# Mostra resumo do output
from pathlib import Path
from datetime import date
out = Path(f"outputs/raw/investigador_{date.today()}.json")
if out.exists():
    data = json.loads(out.read_text(encoding="utf-8"))
    print(f"\n=== RESUMO ===")
    print(f"Total de itens: {data['total_items']}")
    for topic, items in data["topics"].items():
        print(f"  {topic}: {len(items)} itens")
    print(f"Erros: {len(data.get('errors', []))}")
