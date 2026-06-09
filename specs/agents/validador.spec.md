# Spec: Agente Validador

## 1. Objetivo
Recebe itens do Curador e adiciona metadados de confiabilidade: `link_status` e `fact_status`. Não descarta itens — apenas os enriquece para que o Design Agent exiba badges adequados.

## 2. Entradas
`outputs/raw/curador_YYYY-MM-DD.json`

## 3. Saídas
`outputs/raw/validador_YYYY-MM-DD.json` — mesmo schema + campos adicionados:
- `link_status`: `"ok" | "broken" | "redirect" | "timeout" | "unknown"`
- `link_redirect_url`: `string | null`
- `fact_status`: `"fact" | "speculation" | "opinion"`
- `fact_confidence`: `float 0.0-1.0`
- `fact_method`: `"heuristic" | "llm"`
- `speculation_triggers`: `list[str]`

## 4. Etapa 1 — Validação de Links
Via `src/utils/link_validator.py`:
- HEAD request, timeout 10s, follow_redirects=True (máx 3)
- 200-299 → `"ok"` | 301/302 → `"redirect"` | 404/410 → `"broken"` | timeout → `"timeout"`
- Retry 2x em timeout/erro de rede

## 5. Etapa 2 — Classificação Fato/Especulação

### 5.1 Heurística Python
```python
SPECULATION_TRIGGERS = [
    "poderia", "poderá", "especula-se", "especulação",
    "seria", "seriam", "segundo fontes", "fontes ouvidas",
    "teria", "teriam", "pode vir a", "cogita-se",
    "rumores", "não confirmado", "suposto", "supostamente",
    "aguarda-se", "antecipa-se", "promete-se",
]

# 0 triggers → fact, confidence = 0.95
# 1 trigger, texto > 200 palavras → confidence = 0.65 → escalar LLM
# 1 trigger, texto <= 200 palavras → speculation, confidence = 0.80
# 2+ triggers → speculation, confidence = 0.90
```

### 5.2 LLM Fallback (claude-haiku-4-5-20251001)
Acionado quando `fact_confidence < 0.70`.
Prompt: ver `directives/personas/validador.md`

## 6. Casos de Uso

### UC-01 — Item factual claro
- 0 triggers → `fact`, `confidence = 0.95`, `method = "heuristic"`, LLM não acionado

### UC-02 — Especulação detectada por heurística
- 2+ triggers → `speculation`, `confidence = 0.90`, `method = "heuristic"`
- Design exibe badge amarelo ⚠

### UC-03 — Ambíguo → LLM
- 1 trigger em texto > 200 palavras → `confidence = 0.65` → LLM classifica
- LLM pode reclassificar como `fact` (hermenêutica jurídica usa linguagem condicional)

## 7. Métricas
| Métrica | Alvo |
|---|---|
| Links verificados | 100% dos itens |
| Itens escalonados para LLM | <= 20% |
| Tempo total | <= 30s |
