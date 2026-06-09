# Skill: Curador

## Quando usar
Implementar, depurar ou modificar `src/agents/curador.py`, ajustar scoring ou trabalhar no cache `seen_urls.json`.

## O que faz
1. Lê `outputs/raw/reporter_YYYY-MM-DD.json`
2. Carrega cache `outputs/seen_urls.json`
3. Etapa 1 — deduplicação Python: URL exata + similaridade de título (SequenceMatcher > 0.80)
4. Etapa 2 — scoring LLM (sonnet): relevance_score ponderado por 4 critérios
5. Seleciona top 3 por tópico; publica todos se < 3
6. Atualiza cache; salva `outputs/raw/curador_YYYY-MM-DD.json`

## Ferramentas
- `src/agents/curador.py`
- `outputs/seen_urls.json` — cache cross-dia
- `directives/personas/curador.md`
- `specs/agents/curador.spec.md`

## Relação com outros agentes
- Recebe de: **Reporter**
- Entrega para: **Validador**
- Efeito colateral: atualiza `seen_urls.json`
