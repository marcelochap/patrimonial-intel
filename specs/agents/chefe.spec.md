# Spec: Agente Chefe

## 1. Objetivo
Orquestrador do pipeline. Coordena agentes em sequência, valida entregas, aplica retry, envia PDF por e-mail e registra log completo.

## 2. Pipeline
```
Investigador → Reporter → Curador → Validador → Design → E-mail
```
Cada etapa: retry até 3x com backoff `2^attempt` segundos.

## 3. Critérios de Validação por Agente

| Agente | Aprovação | Rejeição |
|---|---|---|
| Investigador | `total_items >= 1` e JSON válido | items vazio ou JSON corrompido |
| Reporter | >= 80% dos itens com `summary != null` | < 80% com summary |
| Curador | `items_selected >= 1` | zero itens |
| Validador | Todos os itens com `link_status` e `fact_status` | campo ausente em qualquer item |
| Design | PDF existe e tamanho >= 10KB | arquivo ausente ou < 10KB |

## 4. Relatório Parcial
Se Investigador coletar >= 2 tópicos com itens, continuar mesmo com falhas parciais.
Fallback de Design: se Validador falhar, usar output do Curador (sem fact_status).
PDF parcial inclui banner: "RELATÓRIO PARCIAL — PIPELINE INCOMPLETO".

## 5. Log JSON
`outputs/raw/pipeline_log_YYYY-MM-DD.json`
```json
{
  "date": "YYYY-MM-DD",
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "status": "success|partial|failed",
  "llm_cost_usd": 0.0,
  "steps": [{
    "agent": "string",
    "status": "success|failed|skipped",
    "items_in": 0,
    "items_out": 0,
    "retries": 0,
    "errors": [],
    "start_time": "ISO8601",
    "end_time": "ISO8601",
    "tokens_used": 0
  }]
}
```
Log salvo incrementalmente após cada step.

## 6. E-mail de Erro
- Subject: `[ERRO] Relatório Patrimonial YYYY-MM-DD`
- Body: etapa com falha, tentativas, resumo de erros das etapas anteriores, custo LLM acumulado

## 7. Monitoramento de Custo
- Acumula via `CostTracker` por agente
- Se custo > `LLM_COST_THRESHOLD_USD` (padrão $0.50): aviso no e-mail de entrega

## 8. Variáveis de Ambiente Requeridas
- `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `REPORT_EMAIL_TO`, `REPORT_EMAIL_FROM`
- Opcionais: `LLM_COST_THRESHOLD_USD` (default 0.50), `SERPER_API_KEY`
