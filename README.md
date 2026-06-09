# 📋 Patrimonial Intel

> Seu consultor jurídico-patrimonial trabalhando enquanto você dorme.

**Patrimonial Intel** é um sistema de inteligência automatizada que varre a internet toda madrugada, coleta as notícias jurídicas mais relevantes do dia anterior, filtra o que realmente importa para quem tem patrimônio, holding familiar ou seguros de vida — e entrega tudo num relatório PDF profissional direto no seu e-mail às **6h da manhã**.

Nenhuma assinatura. Nenhum login. Só o relatório chegando todo dia.

---

## O que você recebe todo dia

Um PDF com até 15 notícias organizadas em 5 áreas:

| Área | O que cobre |
|------|-------------|
| 🏛️ **Patrimonial e Sucessório** | ITCMD, inventários, trusts, planejamento de herança |
| 💰 **Tributário** | IRPF, dividendos, ganho de capital, decisões do CARF |
| 🏠 **Imobiliário e Família** | Contratos, regimes de bens, incorporação |
| 🏢 **Holdings** | Governança, acordos de sócios, proteção patrimonial |
| 🛡️ **Seguros** | Vida, invalidez, saúde internacional, decisões ANS/SUSEP |

Cada notícia vem com **resumo em linguagem clara**, a **lei ou processo** envolvido, e um **insight prático** sobre o que isso significa para quem tem patrimônio ou holding.

---

## Como funciona por baixo do capô

O sistema é composto por 6 "agentes" de inteligência artificial que trabalham em sequência toda madrugada:

```
🔍 INVESTIGADOR  →  Varre 14 fontes jurídicas e coleta as notícias do dia
📝 REPORTER      →  Transforma cada notícia num verbete jurídico estruturado
✂️  CURADOR       →  Remove duplicatas e seleciona as 3 mais relevantes por área
✅ VALIDADOR     →  Verifica se os links existem e separa fato de especulação
🎨 DESIGN        →  Monta o PDF com layout profissional
👔 CHEFE         →  Coordena tudo, cuida dos erros e dispara o e-mail
```

Isso roda automaticamente todo dia via **GitHub Actions** — um serviço gratuito do GitHub que executa código na nuvem em horários programados.

---

## O que você precisa para colocar no ar

### Pré-requisitos

Você vai precisar de contas (todas gratuitas para este uso):

| Serviço | Para que serve | Link |
|---------|---------------|-------|
| **GitHub** | Hospedar o código e rodar o sistema automaticamente | [github.com](https://github.com) |
| **Anthropic** | A IA que lê e escreve os relatórios | [console.anthropic.com](https://console.anthropic.com) |
| **Serper.dev** | Buscar notícias no Google | [serper.dev](https://serper.dev) |
| **Resend** | Enviar o e-mail com o PDF | [resend.com](https://resend.com) |

No computador local você precisa ter instalado:
- [Python 3.12+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

---

## Passo a passo para ativar

### 1. Copie o projeto para sua conta GitHub

Clique em **Fork** no canto superior direito desta página. Isso cria uma cópia do projeto na sua conta, onde você pode rodar e personalizar.

### 2. Obtenha suas chaves de API

**Anthropic (IA):**
1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Vá em **API Keys** → **Create Key**
3. Copie a chave (começa com `sk-ant-...`)

**Serper.dev (buscas):**
1. Acesse [serper.dev](https://serper.dev) e crie uma conta
2. No dashboard, copie sua **API Key**
3. O plano gratuito dá 2.500 buscas/mês — suficiente para rodar por meses

**Resend (e-mail):**
1. Acesse [resend.com](https://resend.com) e crie uma conta
2. Vá em **API Keys** → **Create API Key**
3. Copie a chave

### 3. Configure os secrets no GitHub

No seu repositório (o fork que você criou):

1. Clique em **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret** e adicione cada um abaixo:

| Nome do Secret | O que colocar |
|---------------|---------------|
| `ANTHROPIC_API_KEY` | Sua chave da Anthropic |
| `SERPER_API_KEY` | Sua chave do Serper.dev |
| `RESEND_API_KEY` | Sua chave do Resend |
| `REPORT_EMAIL_TO` | O e-mail onde você quer receber o relatório |
| `REPORT_EMAIL_FROM` | Um e-mail remetente verificado no Resend¹ |

> ¹ No Resend, você precisa verificar um domínio ou usar o e-mail padrão deles (`onboarding@resend.dev`) nos primeiros testes.

### 4. Ative o workflow

1. No seu repositório, clique em **Actions**
2. Se aparecer um aviso pedindo para ativar workflows, clique em **I understand my workflows, go ahead and enable them**
3. O sistema vai rodar automaticamente todo dia às **6h da manhã (horário de Brasília)**

### 5. Teste agora mesmo (opcional)

Para não esperar até amanhã cedo:

1. No GitHub, vá em **Actions** → **Daily Patrimonial Report**
2. Clique em **Run workflow** → **Run workflow**
3. Aguarde ~5 minutos e verifique seu e-mail

---

## Rodando localmente (para testar ou customizar)

Se quiser rodar no seu próprio computador:

```bash
# 1. Clone o repositório
git clone https://github.com/marcelochap/patrimonial-intel.git
cd patrimonial-intel

# 2. Instale as dependências Python
pip install -r requirements.txt

# 3. Instale o Chromium (necessário para gerar o PDF)
playwright install chromium

# 4. Crie o arquivo de configuração local
cp .env.example .env
# Abra o arquivo .env num editor de texto e preencha suas chaves

# 5. Rode o pipeline completo
python src/agents/chefe.py
```

O relatório PDF será gerado em `outputs/reports/`.

---

## Custos estimados

O projeto usa APIs pagas, mas com valores muito baixos:

| Serviço | Custo estimado | Observação |
|---------|---------------|------------|
| Anthropic (IA) | ~R$ 0,25–0,45/dia | ~R$ 7–14/mês |
| Serper.dev | Gratuito | 2.500 buscas grátis/mês |
| Resend | Gratuito | 3.000 e-mails grátis/mês |
| GitHub Actions | Gratuito | 2.000 minutos grátis/mês |

**Custo total estimado: menos de R$ 15/mês.**

O sistema monitora o custo de IA automaticamente. Se um dia estiver acima do esperado, você receberá um aviso no próprio e-mail do relatório.

---

## Personalizando o relatório

### Adicionar ou remover destinatários
Altere o secret `REPORT_EMAIL_TO` no GitHub com o novo endereço.

### Mudar o horário de envio
Edite o arquivo `.github/workflows/daily-report.yml` e ajuste a linha:
```yaml
- cron: '0 9 * * *'   # 09:00 UTC = 06:00 BRT
```
Use [crontab.guru](https://crontab.guru) para calcular o horário desejado.

### Adicionar novas fontes de notícias
Edite `directives/sources.md` e adicione a URL da fonte. Se o site tiver feed RSS, adicione também em `src/scrapers/rss_scraper.py`.

---

## Estrutura do projeto

```
patrimonial-intel/
├── .github/workflows/      # Agendamento automático (GitHub Actions)
├── src/
│   ├── agents/             # Os 6 agentes de IA (Python)
│   ├── scrapers/           # Coleta de notícias (RSS, Google, Playwright)
│   └── utils/              # Ferramentas compartilhadas
├── specs/                  # Documentação técnica detalhada de cada agente
├── directives/             # Fontes e instruções para os agentes
├── tests/                  # Testes automatizados
└── outputs/                # Relatórios gerados (criado automaticamente)
```

---

## Problemas comuns

**Não recebi o e-mail:**
- Verifique a pasta de spam
- Confirme que o `REPORT_EMAIL_FROM` está verificado no Resend
- Acesse **Actions** no GitHub e veja se o workflow rodou com sucesso (ícone verde ✅)

**Erro no GitHub Actions:**
- Clique no workflow com erro (ícone vermelho ❌) para ver o log detalhado
- Os erros mais comuns são chaves de API incorretas ou expiradas

**Relatório chegou incompleto:**
- Normal em dias com poucos eventos jurídicos relevantes
- O sistema envia o que encontrou com uma nota informando as áreas sem novidades

---

## Tecnologias utilizadas

- **Python 3.12** — linguagem principal dos agentes
- **Anthropic Claude** — modelos de linguagem para análise e redação
- **Playwright** — automação de navegador para scraping e geração de PDF
- **GitHub Actions** — execução automática na nuvem
- **Resend** — envio de e-mail transacional

---

## Licença

MIT — use, modifique e distribua livremente.

---

*Construído com Claude Code · Anthropic*
