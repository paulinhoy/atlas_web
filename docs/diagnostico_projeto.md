# 🩺 Diagnóstico Técnico e Arquitetural — Atlas Web (PELTMG / CODEMGE)

* **Data do Diagnóstico:** 16 de Agosto de 2026
* **Versão Base do Streamlit:** `1.36.0` (exigência estrita do ambiente do cliente)
* **Objetivo:** Mapear duplicações, inconsistências arquiteturais, gargalos de performance, medidas de segurança mínima e requisitos para deploy em produção em servidor corporativo.

---

## 📋 Resumo Executivo

A aplicação **Atlas Web** apresenta uma base visual e funcional sólida, cumprindo com excelência a replicação visual das fichas técnicas do QGIS e o consumo rápido de dados em Parquet. No entanto, foram identificados pontos que requerem atenção antes da ida para produção corporativa:

1. **Duplicação de Código Crítica:** Definição duplicada de função (`render` em `home.py`) e fragmentação de funções utilitárias (`fix_mojibake` e formatadores brasileiros).
2. **Acoplamento de Regras de Negócio na View:** Consultas e agregações complexas de custos sendo calculadas dentro de `views/atlas.py`.
3. **Gestão de Memória em Concorrência:** O arquivo de geometrias `empreendimento_geo.parquet` (~114 MB) pode gerar picos de RAM com múltiplos usuários caso não haja controle refinado de cache e projeção de colunas.
4. **Ausência de Configurações de Produção:** Falta do arquivo `.streamlit/config.toml` com travas de segurança (XSRF, CORS, telemetria).
5. **Segurança e Sanitização:** Necessidade de validação estrita do parâmetro de URL `?id=` contra injeções e verificação de escape XSS em todas as saídas HTML.

---

## 🔍 Detalhamento dos Pontos Avaliados

### 1. Duplicações e Código Morto (Dead Code)

| Item | Localização | Descrição | Impacto | Ação Recomendada |
| :--- | :--- | :--- | :--- | :--- |
| **1.1** | `views/home.py`<br>(L504–579) | Função `render()` duplicada. A primeira definição ficou órfã quando a paginação foi implementada mais abaixo (L671–782). | Manutenibilidade e legibilidade comprometidas. | Remover a primeira definição órfã de `render()`. |
| **1.2** | Múltiplos arquivos | Função `fix_mojibake` duplicada em 4 locais (`services/data_loader.py`, `scripts/process_data.py`, `scripts/process_geo.py`, `scripts/fix_encoding.py`). | Inconsistência caso a lógica precise ser estendida. | Centralizar em um módulo compartilhado (ex: `services/formatters.py` ou `services/utils.py`). |
| **1.3** | `views/home.py` e `views/atlas.py` | Funções de formatação de valores brasileiros dispersas (`format_br_int` no `home.py`; `fmt_brl`, `fmt_int_br`, `fmt_decimal_br`, etc. no `atlas.py`). | Duplicação de lógica de apresentação. | Centralizar todos os formatadores em `services/formatters.py`. |
| **1.4** | `scripts/fix_encoding.py` | Script redundante com `scripts/process_data.py`. | Código obsoleto no repositório. | Unificar e remover script redundante ou transformá-lo em utilitário de validação. |

---

### 2. Arquitetura e Separação de Responsabilidades

* **2.1 Lógica de Agregação de Custos na View (`views/atlas.py`):**
  * *Situação:* A tabela de obras (`render_tabela_obras`) calcula em tempo de renderização o agrupamento por obra e cenário para determinar o custo máximo:
    ```python
    soma_por_cenario = custos_emp.groupby(["id_obra", "id_cenario"])["valor_adotado"].sum().reset_index()
    valor_por_obra = soma_por_cenario.groupby("id_obra")["valor_adotado"].max().to_dict()
    ```
  * *Problema:* A camada de apresentação (View) deve apenas receber os dados prontos para exibição.
  * *Solução:* Mover o cálculo para uma função de serviço em `services/data_loader.py` ou `services/empreendimento_service.py`.

* **2.2 Desacoplamento do Serviço Geoespacial (`services/map_service.py`):**
  * *Situação:* O módulo já está bem isolado com Shapely/Folium.
  * *Melhoria:* Adicionar bloco defensivo `try/except` com fallback seguro para WKTs corrompidos ou tipos geométricos não suportados, garantindo que o mapa nunca interrompa o restante da ficha técnica.

---

### 3. Prontidão para Produção (Deploy Corporativo)

* **3.1 Gestão de Memória e Concorrência:**
  * O arquivo `empreendimento_geo.parquet` possui **~114 MB**.
  * No modelo multi-threaded do Streamlit, cada sessão de usuário acessa os dados através de `@st.cache_data`.
  * *Cuidados:* Evitar mutações em DataFrames em cache e carregar apenas as colunas estritamente necessárias para o mapa (`id_empreendimento`, `geom_linha`, `geom_ponto`, `nome_empreendimento`), economizando dezenas de megabytes de RAM.

* **3.2 Arquivo de Configuração de Produção (`.streamlit/config.toml`):**
  * Criar o arquivo `.streamlit/config.toml` com os parâmetros recomendados para ambiente corporativo:
    ```toml
    [server]
    headless = true
    port = 8501
    address = "0.0.0.0"
    enableCORS = false
    enableXsrfProtection = true
    maxUploadSize = 200

    [browser]
    gatherUsageStats = false

    [theme]
    base = "light"
    primaryColor = "#0b2545"
    backgroundColor = "#ffffff"
    secondaryBackgroundColor = "#f8fafc"
    textColor = "#0f172a"
    ```

* **3.3 Requisitos de Infraestrutura / Servidor:**
  * **Reverse Proxy (Nginx / IIS):** Configurar repasse obrigatório de WebSockets (`Upgrade` e `Connection "upgrade"`), fundamentais para o funcionamento estável do Streamlit.
  * **Gerenciador de Processos:** Configurar serviço via `Systemd` (Linux) ou `NSSM` (Windows Server) com reinicialização automática em caso de falha.
  * **HTTPS / SSL:** Terminação criptografada no proxy para segurança do tráfego corporativo.

---

### 4. Segurança Mínima

* **4.1 Sanitização de Query Params (`?id=` em `app.py`):**
  * Validar se o `id` recebido na URL é estritamente alfanumérico ou numérico antes de consultar os DataFrames e renderizar o Atlas, evitando comportamentos anômalos.
* **4.2 Proteção contra XSS em Renderizações HTML:**
  * O projeto já utiliza `html.escape()` em muitos pontos. Garantir cobertura de 100% em qualquer valor dinâmico interpolado em tags HTML via `unsafe_allow_html=True`.
* **4.3 Controle de Acesso Corporativo (Opcional / A Decidir):**
  * Avaliar se a aplicação exige camada de login/autenticação interna (ex: LDAP, SSO corporativo via OAuth2-Proxy ou senha de acesso restrito).

---

## 🗂️ Painel de Decisões e Plano de Ação

Utilizaremos a tabela abaixo para acompanhar cada item e registrar as decisões tomadas:

| ID | Área | Ação Proposta | Status | Decisão / Notas |
| :---: | :--- | :--- | :---: | :--- |
| **D01** | Limpeza | Remover bloco de código duplicado da função `render()` em `views/home.py` | 🛠️ Implementado | Bloco órfão removido (redução de 76 linhas redundantes). |
| **D02** | Refatoração | Criar `services/formatters.py` e unificar formatação brasileira e `fix_mojibake` | 🛠️ Implementado | Centralizado em `services/formatters.py` e consumido por views e scripts ETL. |
| **D03** | Arquitetura | Otimização Inteligente no ETL: pré-cálculo de custo máximo de obras | 🛠️ Implementado | Pré-cálculo movido para `scripts/process_data.py`; `views/atlas.py` simplificada sem overhead de runtime. |
| **D04** | Produção | Criar `.streamlit/config.toml` com travas de segurança e performance | 🛠️ Implementado | Arquivo `.streamlit/config.toml` criado com travas de telemetria, XSRF, CORS e tema institucional. |
| **D05** | Segurança | Sanitizar entrada de `query_params` no `app.py` e revisar `html.escape` geral | ⏳ Pendente | |
| **D06** | Performance | Otimizar carregamento do `empreendimento_geo.parquet` (~108 MB disco / ~255 MB RAM) | 🛠️ Implementado | Projeção de colunas descartada (ganho de apenas 0,1% — as geometrias WKT dominam a RAM). Adotado `@st.cache_resource` em `data_loader._load_geo_shared()`, mantendo objeto único compartilhado entre todas as sessões (economia de ~255 MB por sessão concorrente). Auditoria confirmou uso read-only no `map_service.py`. |
| **D07** | Infra | Definir modelo de deploy no servidor (Nginx + Systemd vs Docker vs Windows Service) | ⏳ Pendente | |
| **D08** | Acesso | Definir se haverá necessidade de autenticação corporativa (login/senha ou SSO) | ⏳ Pendente | |

---

> **Nota de Governança do Projeto:** Toda e qualquer implementação decorrente deste diagnóstico seguirá estritamente o fluxo de branches temáticas (`fix/...`, `feat/...`), aguardando teste local e aprovação expressa antes de qualquer commit ou merge na branch `main`.
