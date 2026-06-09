# Spec: Agente Reporter

## 1. Objetivo
Transforma itens brutos do Investigador em texto editorial completo. Cada item recebe: `summary`, `legal_basis`, `strategic_insight` e, quando cabível, `comparison_table`. Não filtra — isso é responsabilidade do Curador.

## 2. Entradas
`outputs/raw/investigador_YYYY-MM-DD.json`

## 3. Saídas
`outputs/raw/reporter_YYYY-MM-DD.json`

```json
{
  "date": "YYYY-MM-DD",
  "items_by_topic": {
    "1_sucessorio": [{
      "title": "string",
      "date": "YYYY-MM-DD|null",
      "url": "string",
      "source": "string",
      "topic": "string",
      "snippet": "string",
      "link_status": "verified|unverified|unavailable",
      "summary": "string (3-5 linhas)",
      "legal_basis": "string|null",
      "strategic_insight": "string",
      "comparison_table": {"before": "string", "after": "string"} | null
    }]
  },
  "total_tokens": 0,
  "errors": []
}
```

## 4. Casos de Uso

### UC-01 — Item com base legal explícita
- Fluxo: LLM extrai artigos/processos para `legal_basis`; `comparison_table = null`
- Resultado: item completo com todos os campos

### UC-02 — Item sem base legal
- Fluxo: `legal_basis = null`; demais campos gerados normalmente
- Resultado: item publicado sem `legal_basis`

### UC-03 — Mudança de entendimento
- Pré-condição: texto contém contraste ("anteriormente...", "novo entendimento...")
- Fluxo: `comparison_table` preenchida com `before` e `after`
- Resultado: Design Agent renderiza tabela visual

## 5. Prompt Template
Ver `directives/personas/reporter.md`

## 6. Tratamento de Erros
- LLM timeout: retry 3x com backoff 2s/4s/8s
- JSON inválido: retry 1x; falha → fallback (summary=snippet, legal_basis=null)
- Rate limit: `asyncio.sleep(0.5)` entre chamadas por tópico

## 7. Métricas
| Métrica | Alvo |
|---|---|
| Taxa de sucesso | >= 95% |
| Tokens por item | <= 600 |
| Tempo total (15 itens) | <= 120s |
