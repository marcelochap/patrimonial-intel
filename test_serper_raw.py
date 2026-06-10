import os, httpx
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get("SERPER_API_KEY", "")
print(f"Key presente: {'sim' if key else 'NAO'} (primeiros 6: {key[:6]})")

# Teste 1: query simples sem after:
r = httpx.post(
    "https://google.serper.dev/news",
    json={"q": "IRPF tributario", "gl": "br", "hl": "pt-br", "num": 3},
    headers={"X-API-KEY": key, "Content-Type": "application/json"},
    timeout=15,
)
print(f"Status (query simples): {r.status_code}")
if r.status_code == 200:
    data = r.json()
    news = data.get("news", [])
    print(f"Itens retornados: {len(news)}")
    for n in news[:2]:
        print(f"  {n.get('title','')[:60]}")
else:
    print(f"Erro: {r.text[:300]}")
