# Spec: Agente Design

## 1. Objetivo
Recebe JSON validado e produz PDF final. LLM (sonnet) gera HTML; Playwright renderiza PDF A4 com margens 20mm.

## 2. Entradas
`outputs/raw/validador_YYYY-MM-DD.json`

## 3. Saídas
`outputs/reports/report_YYYY-MM-DD.pdf`
- Formato: A4, margens 20mm, RGB, links clicáveis ativos
- Tamanho mínimo: 10KB

## 4. Estrutura Visual

### Cabeçalho
```
PATRIMONIAL INTEL — Relatório Jurídico-Patrimonial Diário
Data: DD/MM/YYYY | Gerado às HH:MM BRT
"Olá. Aqui está o seu relatório jurídico consolidado das últimas 24 horas."
```

### Sumário
Lista dos 5 tópicos com contagem de itens.

### Cards por Item
```
[BADGE TÓPICO]                              [BADGE FACT STATUS]
TÍTULO
Fonte | Data | Link

RESUMO
{summary}

BASE LEGAL (fundo cinza claro)
• artigos / processos / resoluções

INSIGHT ESTRATÉGICO (borda azul escuro)
{strategic_insight}

MUDANÇA DE ENTENDIMENTO (só se comparison_table)
| ANTES        | DEPOIS       |
```

### Badges de Fact Status
| `fact_status` | Badge | Cor |
|---|---|---|
| `fact` | ✓ VERIFICADO | Verde #2D7D46 |
| `opinion` | ◈ ANÁLISE | Azul #1A5276 |
| `speculation` | ⚠ ESPECULAÇÃO | Amarelo #D4AC0D + faixa lateral amarela no card |

### Badges de Link
- `ok` → link clicável normal
- `broken` → "Link indisponível" em vermelho, não clicável
- `timeout` → link + "(não verificado)" em cinza

## 5. Fluxo

1. LLM recebe JSON + instrução de design → retorna HTML completo
2. Strip de preamble antes de `<!DOCTYPE`
3. Playwright: `page.set_content()` → `page.pdf()` com `print_background=True`
4. Verificar tamanho >= 10KB
5. Salvar em `outputs/reports/`

## 6. Casos de Uso

### UC-01 — PDF gerado com sucesso
- HTML válido → PDF > 10KB → Chefe envia por e-mail

### UC-02 — Item com tabela comparativa
- `comparison_table` renderizada como tabela HTML com cabeçalhos ANTES/DEPOIS em negrito

### UC-03 — Falha de renderização
- HTML inválido ou Playwright timeout → retry completo (LLM + Playwright) até 3x
- Após 3 falhas: Chefe recebe erro, envia e-mail de alerta

## 7. Playwright Config
```python
await page.pdf(
    path=str(output_path),
    format="A4",
    margin={"top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm"},
    print_background=True,
)
```
