# Skill: Chefe

## Quando usar
Implementar, depurar ou modificar `src/agents/chefe.py`, ajustar critérios de validação, retry logic, envio de e-mail ou geração de logs.

## O que faz
1. Inicia log `outputs/raw/pipeline_log_YYYY-MM-DD.json`
2. Executa sequência: Investigador → Reporter → Curador → Validador → Design
3. Após cada agente: valida output com critérios específicos (ver spec seção 3)
4. Falha: retry 3x com backoff `2^attempt`s; se persistir → relatório parcial ou e-mail de erro
5. Sucesso: envia PDF por e-mail via Resend
6. Salva log final com custo LLM acumulado via `CostTracker`

## Ferramentas
- `src/agents/chefe.py`
- `src/utils/cost_tracker.py`
- `specs/agents/chefe.spec.md` — pseudocódigo completo, critérios, template de e-mail de erro
- `.github/workflows/daily-report.yml` — trigger cron 03:00 UTC

## Relação com outros agentes
- **Instancia e coordena** todos os agentes
- Responsável por: logs, e-mails, retry global, custo total
