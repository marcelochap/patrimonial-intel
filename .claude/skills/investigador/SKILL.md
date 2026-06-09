# Skill: Investigador

## Quando usar
Quando o Chefe iniciar o pipeline ou quando se precisar coletar notícias jurídico-patrimoniais das últimas 24h.

## O que faz
1. Lê `directives/sources.md` para obter fontes e tópicos
2. Para cada tópico, lança busca paralela (httpx async)
3. Valida cada URL encontrada (HEAD request)
4. Serializa resultado em `outputs/raw/investigador_YYYY-MM-DD.json`

## Ferramentas usadas
- `src/scrapers/` — scrapers por domínio
- `src/utils/link_validator.py` — checagem de URLs
- Referência: **graphify** para mapear relações entre tópicos quando relevante

## Relação com outros agentes
- Precede: Reporter
- Controlado por: Chefe
