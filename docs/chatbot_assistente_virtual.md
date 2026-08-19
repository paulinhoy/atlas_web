# 🤖 Documentação do Assistente Virtual / Chatbot — Atlas Web (PELTMG / CODEMGE)

Documento técnico de referência sobre a arquitetura, ferramentas, segurança, configuração e modelo de dados do assistente virtual integrado ao **Atlas Web**.

---

## 1. Visão Geral

O **Assistente Virtual do Atlas Web** transforma as consultas estáticas aos dados do PELTMG em uma experiência conversacional interativa e analítica. Construído com **LangChain** e integrado à interface nativa do Streamlit, ele permite que gestores e analistas façam perguntas em linguagem natural e recebam respostas precisas extraídas diretamente dos arquivos Parquet do projeto.

* **Framework de Orquestração:** `langchain>=0.3.0`
* **Provedores Suportados:** OpenAI (`langchain-openai`) e Google Gemini (`langchain-google-genai`)
* **Modelo Ativo Padrão:** `gpt-5.6-luna` (com compatibilidade para `gemini-2.0-flash`, `gpt-4o-mini`, etc.)
* **Método de Consulta:** *Function Calling / Tool Use* (consultas seguras sem execução arbitrária de código Python)
* **Governança:** Rate limiting por sessão, teto de orçamento diário (Kill-Switch) e logging em JSONL.

---

## 2. Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────┐
│                    views/chatbot.py                         │
│  ├─ Layout em tela cheia (100% largura para respostas)      │
│  ├─ Identificador de sessão único por aba (UUID)            │
│  └─ Spinner interativo de consulta                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ prompt do usuário
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              services/chatbot_service.py                    │
│  ├─ 1. Sanitização e Anti-Injection (re.search)             │
│  ├─ 2. Rate Limiting por Sessão (6 req/min, 100 req/dia)    │
│  ├─ 3. Verificação de Budget Diário (data/budget.json)      │
│  ├─ 4. Instanciação Dinâmica de LLM (OpenAI / Gemini)       │
│  ├─ 5. Orquestração com Function Calling (Loop de 3 etapas) │
│  └─ 6. Cálculo de Custo Estimado e Envio para Log           │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
        Chama ferramentas             Grava auditoria
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│   5 Ferramentas de Consulta  │ │   services/chat_logger.py   │
│   (services/data_loader.py)  │ │   (data/chat_logs/*.jsonl)  │
│  ├─ buscar_empreendimento    │ └─────────────────────────────┘
│  ├─ listar_empreendimentos   │
│  ├─ consultar_financeiro     │
│  ├─ contar_empreendimentos   │
│  └─ listar_obras             │
└──────────────────────────────┘
```

---

## 3. As 5 Ferramentas de Consulta (Function Calling)

As ferramentas conectam a LLM aos DataFrames em memória (`services/data_loader.py`). Todas retornam **strings limpas e delimitadas**, impedindo sobrecarga de tokens.

| # | Ferramenta | Parâmetros | Fonte de Dados | Descrição / Retorno |
|:---|:---|:---|:---|:---|
| **1** | `buscar_empreendimento` | `id_empreendimento: int` | `empreendimentos_priorizacao.parquet` | Ficha técnica resumida (nome, setor, esfera, status, natureza, vocação, IC e impacto). |
| **2** | `listar_empreendimentos` | `setor: str`, `esfera: str`, `impacto: str`, `limite: int` (máx 20) | `empreendimentos_priorizacao.parquet` | Filtra e lista projetos da carteira priorizada por critérios combinados. |
| **3** | `consultar_financeiro` | `id_empreendimento: int` | `dados_financeiro.parquet` | CAPEX atualizado, OPEX atualizado, Valor Total, Receita Total e Mês Base de atualização. |
| **4** | `contar_empreendimentos` | `agrupar_por: str` (`setor`, `esfera` ou `impacto`) | `empreendimentos_priorizacao.parquet` | Distribuição estatística com quantidades absolutas e percentuais da base (~1.682 projetos). |
| **5** | `listar_obras` | `id_empreendimento: int`, `limite: int` (máx 30) | `obras_priorizacao.parquet` | Detalhamento das obras vinculadas: tipo de intervenção, infraestrutura, extensão em km e valor estimado. |

---

## 4. Configuração Fácil via `.env`

Todas as variáveis operacionais e limites foram desacoplados do código e centralizados no arquivo `.env`:

```ini
# === Chaves de API ===
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=AIzaSy...

# === Provedor e Modelos ===
LLM_PROVIDER=openai               # "openai" ou "gemini"
LLM_MODEL_OPENAI=gpt-5.6-luna
LLM_MODEL_GEMINI=gemini-2.0-flash
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=800

# === Rate Limiting (por aba/sessão) ===
RATE_LIMIT_PER_MINUTE=6           # Limite por minuto
RATE_LIMIT_PER_DAY=100            # Limite por dia
MAX_INPUT_CHARS=1000              # Tamanho máximo do prompt
MAX_HISTORY_MESSAGES=20           # Histórico de contexto enviado à LLM

# === Orçamento e Kill-Switch ===
BUDGET_DAILY_BRL=5.00             # Limite máximo de gasto por dia em Reais
```

---

## 5. Medidas de Segurança e Proteção de Créditos

1. **Anti-Prompt Injection:** O sistema analisa a entrada do usuário contra padrões de override (`ignore previous instructions`, `you are now`, `system:`) antes de chamar a API.
2. **Compatibilidade com Reasoning Models:** Para modelos como `gpt-5.6-luna`, o serviço configura `reasoning_effort="none"` para viabilizar Function Calling sem erros na API.
3. **Limitação de Saída (`max_tokens`):** Respostas limitadas a 800 tokens evitam cobranças desproporcionais.
4. **Kill-Switch Financeiro:** Se o acumulado diário em `data/budget.json` atingir o limite estipulado em `BUDGET_DAILY_BRL`, o assistente bloqueia novas chamadas e informa amigavelmente o usuário.

---

## 6. Sistema de Auditoria e Logging (JSONL)

Para fins de governança e melhoria contínua das respostas, todas as interações são salvas em arquivos diários:

* **Caminho:** `data/chat_logs/YYYY-MM-DD.jsonl` (ignorado pelo Git).
* **Estrutura de cada registro:**
```json
{
  "timestamp": "2026-08-18T23:33:53.123456",
  "session_id": "a1b2c3d4",
  "role": "assistant",
  "content": "O Atlas possui 1.682 empreendimentos...",
  "model": "gpt-5.6-luna",
  "provider": "openai",
  "tokens_in": 15,
  "tokens_out": 42,
  "cost_estimate_brl": 0.000183,
  "tools_used": ["contar_empreendimentos"]
}
```

---

## 7. Design e Layout da Interface (`views/chatbot.py`)

* **Aproveitamento Total da Tela:** As respostas da IA utilizam 100% da largura do container, ideal para tabelas, listas de obras e resumos extensos sem quebras de linha artificiais.
* **Borda Lateral Institucional:** Balões do assistente com fundo neutro suave (`#f8fafc`) e faixa esquerda azul marinho (`#0b2545`).
* **Mensagens do Usuário:** Compactas e alinhadas à direita em gradiente institucional.
* **Botão Flutuante de Retorno:** Acesso síncrono para retornar à tela inicial (`?`).
