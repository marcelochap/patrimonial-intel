# Skill: Design

## Quando usar
Implementar, depurar ou modificar `src/agents/design.py`, ajustar template HTML ou debugar geração de PDF com Playwright.

## O que faz
1. Lê `outputs/raw/validador_YYYY-MM-DD.json`
2. Envia JSON ao claude-sonnet-4-6 com instrução de design editorial
3. LLM retorna HTML completo (strip de preamble antes de `<!DOCTYPE`)
4. Playwright headless renderiza HTML → PDF A4, margens 20mm, `print_background=True`
5. Verifica tamanho >= 10KB; retry completo (LLM + Playwright) até 3x em falha
6. Salva `outputs/reports/report_YYYY-MM-DD.pdf`

## Ferramentas
- `src/agents/design.py`
- `src/utils/report_template.html` — template Jinja2 base
- `directives/personas/design.md`
- `specs/agents/design.spec.md` — estrutura visual, badges, cores

## Relação com outros agentes
- Recebe de: **Validador**
- Entrega para: **Chefe** (caminho do PDF)
