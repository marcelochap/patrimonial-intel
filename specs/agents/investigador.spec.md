# Spec: Agente Investigador

## Objetivo
Coletar itens jurídico-patrimoniais publicados nas últimas 24h nas fontes obrigatórias.

## Entradas
- Lista de tópicos (5 categorias)
- Lista de fontes por categoria
- Janela de tempo: últimas 24h

## Saídas
- JSON com itens por tópico (schema em `directives/personas/investigador.md`)
- Arquivo: `outputs/raw/investigador_YYYY-MM-DD.json`

## Casos de Uso

### UC-01: Busca bem-sucedida
- Dado que a fonte está acessível
- Quando o agente busca pelo tópico
- Então retorna ≥ 1 item com URL direta válida

### UC-02: Fonte indisponível
- Dado que a fonte retorna erro 4xx/5xx
- Quando o agente tenta acessar
- Então registra o erro e passa para a próxima fonte

### UC-03: Link sem URL direta
- Dado que o artigo é encontrado mas sem URL canônica
- Quando 3 tentativas falham
- Então registra `link_status: "unavailable"` e mantém o item

## Testes
- `tests/unit/test_investigador.py`
- Mock de respostas HTTP para cada fonte
- Testar timeout, retry e fallback
