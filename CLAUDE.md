# Patrimonial Intel — CLAUDE.md

## Visão Geral
Sistema multiagente de monitoramento jurídico-patrimonial que coleta, filtra, valida e formata um relatório diário em PDF enviado por e-mail às 06h.

## Stack
- **Runtime de agentes**: Python 3.12 + Anthropic SDK (claude-sonnet-4-6)
- **Frontend/Dashboard**: Next.js 15 (App Router)
- **Orquestração**: GitHub Actions (cron `0 3 * * *` UTC = 06h BRT)
- **PDF**: WeasyPrint ou Playwright headless
- **Scraping**: httpx + BeautifulSoup4 / Playwright para sites JS-heavy
- **E-mail**: SendGrid ou Resend

## Agentes e Responsabilidades

| Agente        | Arquivo                  | Função                                                        |
|---------------|--------------------------|---------------------------------------------------------------|
| **Chefe**     | `src/agents/chefe.py`    | Orquestra o pipeline, valida entregas, solicita retrabalho    |
| **Investigador** | `src/agents/investigador.py` | Busca links e fatos brutos nas fontes obrigatórias      |
| **Reporter**  | `src/agents/reporter.py` | Consolida dados brutos em texto estruturado                   |
| **Curador**   | `src/agents/curador.py`  | Filtra duplicatas e irrelevâncias                             |
| **Validador** | `src/agents/validador.py`| Verifica links, separa fato de especulação                   |
| **Design**    | `src/agents/design.py`   | Renderiza o PDF final com layout profissional                 |

## Metodologia
- **SDD**: Toda feature começa com spec em `specs/`
- **TDD**: Testes em `tests/` são escritos antes da implementação
- **Paralelismo**: Investigador roda em paralelo por tópico (5 workers)

## Fontes Obrigatórias
Ver `directives/sources.md`

## Estrutura de Pastas
```
patrimonial-intel/
├── .github/workflows/     # GitHub Actions
├── .claude/skills/        # Skills dos agentes (SKILL.md)
├── specs/                 # Especificações SDD
│   └── agents/            # Spec individual de cada agente
├── directives/            # Prompts/personas dos agentes
│   └── personas/
├── src/
│   ├── app/               # Next.js dashboard
│   ├── agents/            # Scripts Python dos agentes
│   ├── scrapers/          # Scrapers por fonte
│   └── utils/             # PDF, email, validação de links
├── tests/
│   ├── unit/
│   └── integration/
└── outputs/               # Artefatos gerados (não comitar)
    ├── raw/
    ├── processed/
    └── reports/
```
