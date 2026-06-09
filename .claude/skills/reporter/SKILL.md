# Skill: Reporter

## Quando usar
Implementar, depurar ou modificar `src/agents/reporter.py` ou seus testes.

## O que faz
1. Lê `outputs/raw/investigador_YYYY-MM-DD.json`
2. Para cada item, chama claude-sonnet-4-6 com prompt jurídico
3. Retorna JSON com `summary`, `legal_basis`, `strategic_insight`, `comparison_table`
4. Retry 1x em JSON inválido; fallback se ainda falhar
5. Salva `outputs/raw/reporter_YYYY-MM-DD.json`
6. Registra custo via `CostTracker`

## Ferramentas
- `src/agents/reporter.py`
- `src/utils/cost_tracker.py`
- `directives/personas/reporter.md` — system prompt do LLM
- `specs/agents/reporter.spec.md` — schema completo e UCs

## Relação com outros agentes
- Recebe de: **Investigador**
- Entrega para: **Curador**
