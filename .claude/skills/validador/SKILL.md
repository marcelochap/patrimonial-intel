# Skill: Validador

## Quando usar
Implementar, depurar ou modificar `src/agents/validador.py`, ajustar triggers de especulação ou `link_validator.py`.

## O que faz
1. Lê `outputs/raw/curador_YYYY-MM-DD.json`
2. Valida links via `link_validator.py` (HEAD requests async)
3. Heurística Python: detecta triggers de especulação em PT-BR
4. Se `fact_confidence < 0.70`: escala para claude-haiku para classificação
5. Adiciona `link_status`, `fact_status`, `fact_confidence`, `fact_method`, `speculation_triggers`
6. Salva `outputs/raw/validador_YYYY-MM-DD.json`

## Ferramentas
- `src/agents/validador.py`
- `src/utils/link_validator.py`
- `directives/personas/validador.md`
- `specs/agents/validador.spec.md` — lista completa de triggers e fórmula de confidence

## Relação com outros agentes
- Recebe de: **Curador**
- Entrega para: **Design**
