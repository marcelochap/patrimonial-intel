# Spec: Agente Curador

## 1. Objetivo
Recebe itens do Reporter e aplica dois estágios: (1) deduplicação Python puro e (2) scoring LLM. Resultado: máximo 3 itens por tópico ordenados por relevância.

## 2. Entradas
`outputs/raw/reporter_YYYY-MM-DD.json`

## 3. Saídas
`outputs/raw/curador_YYYY-MM-DD.json` — mesmo schema do Reporter + campo `relevance_score: float`

## 4. Etapa 1 — Deduplicação (Python puro)

### 4.1 URL exata
```python
seen_urls: set[str] = set()
# normalizar URL: lowercase scheme+host, strip trailing slash
```

### 4.2 Similaridade de título
```python
from difflib import SequenceMatcher
# threshold > 0.80 = duplicata
# entre duplicatas: manter maior reporter_confidence
# empate: prioridade STF/STJ/DOU > ConJur/Migalhas/JOTA > demais
```

### 4.3 Cache cross-dia
- Carregar `outputs/seen_urls.json` antes de deduplicar
- URLs com mais de 7 dias: remover do cache
- Ao final: atualizar cache com URLs dos itens selecionados

## 5. Etapa 2 — Scoring LLM (claude-sonnet-4-6)

Critérios ponderados:
| Critério | Peso |
|---|---|
| Impacto prático | 0.35 |
| Abrangência | 0.25 |
| Novidade | 0.25 |
| Aplicabilidade holdings/seguros | 0.15 |

Prompt: ver `directives/personas/curador.md`

Seleção: top 3 por tópico; se < 3 disponíveis, publicar todos.

## 6. Casos de Uso

### UC-01 — Sem duplicatas, >= 3 itens por tópico
- Resultado: exatamente 3 itens por tópico

### UC-02 — Duplicatas cross-fonte
- Migalhas e JOTA com mesma notícia → título similarity > 0.80 → manter maior confidence

### UC-03 — Tópico com menos de 3 itens
- Publicar todos os disponíveis; pipeline não falha

## 7. Tratamento de Erros
- LLM timeout: retry 3x → fallback `relevance_score = 0.5` para todos
- `seen_urls.json` corrompido: ignorar cache, registrar warning, recriar ao final
