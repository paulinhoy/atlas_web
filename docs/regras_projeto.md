# 📌 Guia de Contexto, Regras e Convenções do Projeto — Atlas Web (PELTMG / CODEMGE)

Este documento registra o contexto histórico, escolhas arquiteturais, regras de versionamento no Git/GitHub e diretrizes técnicas para continuidade do desenvolvimento nas próximas etapas ou em novos chats.

---

## 1. Visão Geral do Projeto

* **Nome do Projeto:** `atlas_web`
* **Repositório GitHub:** `https://github.com/paulinhoy/atlas_web.git`
* **Objetivo:** Converter o Atlas de Empreendimentos (gerado originalmente no QGIS para o Plano Estadual de Logística e Transportes de Minas Gerais — PELTMG / CODEMGE) em uma aplicação web interativa em Python com Streamlit.
* **Perfil do Desenvolvedor/Usuário:** Cientista de Dados (trabalha exclusivamente com Python).

---

## 2. Tecnologias e Versões Estritas

* **Python:** Utilizando o ambiente virtual `.venv` no diretório raiz do projeto (`.venv\Scripts\python.exe`).
* **Streamlit:** **`streamlit==1.36.0`** (VERSÃO FIXA exata exigida pelo servidor de hospedagem do cliente).
* **Processamento de Dados:** `pandas`, `pyarrow` (compressão Snappy para arquivos `.parquet`).
* **Mapeamento & SIG:** `geopandas`, `folium`, `streamlit-folium`.
* **Outras dependências:** `SQLAlchemy`, `openpyxl`.

---

## 3. Estrutura de Pastas e Modulariedade

```
atlas_web/
├── app.py                      # Roteador principal do Streamlit (navegação entre Home, Atlas e Chatbot)
├── .streamlit/                 # CONFIGURAÇÕES DE SERVIDOR E PRODUÇÃO
│   └── config.toml             # Configurações de porta, segurança (XSRF/CORS), telemetria e tema
├── .venv/                      # Ambiente virtual Python (ignorado pelo Git)
│
├── views/                      # TELAS MODULARES DA APLICAÇÃO
│   ├── home.py                 # Tela 1: Painel Executivo, KPIs, busca, tabela e botão do assistente
│   ├── atlas.py                # Tela 2: Ficha Técnica do Atlas (layout réplica do QGIS)
│   └── chatbot.py              # Tela 3: Assistente Virtual isolado (interface moderna de chat)
│
├── services/                   # SERVIÇOS DE DADOS E GEOESPACIAL
│   ├── data_loader.py          # Leitor otimizado com @st.cache_data (leves) e @st.cache_resource (geo pesado)
│   ├── formatters.py           # Formatadores padronizados (BRL, inteiros, datas) e fix_mojibake
│   └── map_service.py          # Módulo exclusivo de renderização geoespacial (Folium / WKT)
│
├── data/                       # ARMAZENAMENTO DE DADOS (ignorado pelo Git)
│   ├── raw/                    # CSVs e JSONs brutos extraídos do PostGIS (suporta subpastas por data)
│   └── processed/              # Arquivos .parquet otimizados gerados pelo pipeline ETL
│
├── scripts/                    # SCRIPTS AUXILIARES E PIPELINE ETL
│   ├── process_data.py         # Mapeia CSVs brutos para Parquet com tratamento de Mojibake e pré-cálculos
│   ├── process_geo.py          # Mapeia JSON bruto de geometrias WKT para Parquet otimizado
│   └── fix_encoding.py         # Utilitário de correção de codificação dupla
│
├── logos/                      # ATIVOS VISUAIS INSTITUCIONAIS
│   ├── logo_pelt_branco.png
│   ├── logo codemge - branco.png
│   ├── logo peltmg branco.png
│   └── (outras variações de logos oficiais)
│
├── docs/                       # DOCUMENTAÇÃO E REGRAS DO PROJETO
│   ├── plano_implementacao.md  # Plano de etapas e modelo conceitual
│   ├── regras_projeto.md       # Este documento de contexto e convenções
│   ├── diagnostico_projeto.md  # Diagnóstico técnico, arquitetural e decisões de produção
│   └── erros_solucoes.md       # Base de conhecimento de erros e soluções adotadas
│
└── requirements.txt            # Dependências com streamlit==1.36.0
```

---

## 4. Pipeline de Dados e Dicionário de Mapeamentos (CSV / JSON ➔ Parquet)

Os dados são extraídos do banco de dados PostGIS (codificação original ISO-8859-1/Latin1) e convertidos para Parquet UTF-8 otimizado pelos scripts `scripts/process_data.py` e `scripts/process_geo.py`:

| Visão/Tabela Original PostGIS | Parquet Otimizado em `data/processed/` | Chave(s) Principal(is) | Função no Sistema |
| :--- | :--- | :--- | :--- |
| `mvw_8_calcula_impacto_*` | `empreendimentos_priorizacao.parquet` | `id_empreendimento` | Tabela mestra dos ~1.682 projetos priorizados + Notas/Índice de Priorização |
| `vw_empreendimento_custo_economico_lp_*` | `dados_financeiro.parquet` | `id_empreendimento` | Dados financeiros consolidados (CAPEX, OPEX, Receita, Mês Base) |
| `tbl_alocacaoempreendimento_*` | `alocacao_empreendimento.parquet` | `id_empreendimento`, `id_cenario` | Dados de alocação de tráfego/fluxo para 2055 por Cenário (1 a 4) |
| `vw_obra_*` | `obras_priorizacao.parquet` | `id_obra`, `id_empreendimento` | Cadastro e detalhamento individual de cada obra |
| `vw_custo_economico_*` | `custo_obra.parquet` | `id_obra`, `id_empreendimento`, `id_cenario` | Custos detalhados por obra e cenário |
| `mvw_empreendimento_geo_*` | `empreendimento_geo.parquet` | `id_empreendimento` | Geometrias WKT de traçados (`geom_linha`) e intervenções (`geom_ponto`) |

### ⚠️ Regras Cruciais de Tratos com Dados:
1. **Sem limite de obras na Web:** Diferente da versão física do QGIS que limitava em 4 obras, a versão web deve exibir **todas** as obras relacionadas na tabela de detalhamento.
2. **Custo Máximo de Obras por Cenário:** Na tabela de obras, o valor adotado de cada intervenção deve considerar a soma de custos e adotar o valor do **cenário em que a obra for mais cara**.
3. **Formatação Brasileira:** Exibir números inteiros com ponto de milhar (`1.682`), números decimais e índices com vírgula (`0,4031`) e valores financeiros formatados em Reais (`R$ 289.892.422,00`).
4. **Tratamento de Mojibake:** Sempre utilizar a função `fix_mojibake` para tratar codificações duplas provenientes da exportação do banco.

### ⚙️ Estratégia de Cache em Memória (Decisão Arquitetural):
1. **Datasets pequenos (< 2 MB):** Utilizam `@st.cache_data` em `services/data_loader.py`. Este decorator entrega uma **cópia isolada** por sessão — seguro contra mutações acidentais entre usuários.
2. **Dataset geoespacial (`empreendimento_geo.parquet`, ~108 MB em disco / ~255 MB em RAM):** Utiliza `@st.cache_resource` via função `_load_geo_shared()`. Este decorator mantém um **objeto ÚNICO compartilhado** entre todas as sessões do servidor — economia de ~255 MB por usuário concorrente.
3. **Regra de Imutabilidade Obrigatória:** Todo DataFrame retornado por `get_empreendimento_geo()` é **READ-ONLY**. Nunca utilizar `inplace=True`, atribuição direta de colunas (`df["x"] = ...`) ou `.drop()` sem antes criar uma cópia com `df_local = df.copy()`. Violações corrompem os dados de todos os usuários conectados ao servidor.

---

## 5. Fluxo de Trabalho com Git e GitHub (Regras Estritas)

1. **Estratégia de Branches Temáticas:**
   * A branch `main` é mantida **sempre estável e funcional**.
   * **Toda grande tarefa, nova tela ou refatoração relevante DEVE ser desenvolvida em uma nova branch temática** (ex: `feat/tela-atlas`, `feat/estilizacao-tabela-home`, `feat/mapa-geopandas`, `fix/ajuste-tabelas`).
2. **Regra de Ouro para Commits:**
   * ⚠️ **COMMITS SÓ DEVEM SER REALIZADOS APÓS TESTE E APROVAÇÃO EXPLÍCITA DO USUÁRIO.**
   * O assistente deve implementar as alterações, deixar os arquivos na working tree / rascunho, informar o usuário e aguardar a validação no navegador (`http://localhost:8501`).
   * Somente após o usuário testar e autorizar expressamente (ex: *"pode commitar"*, *"aprovado"*), o assistente executa o `git commit` e `git push`.
3. **Passo a Passo de Desenvolvimento:**
   * Criar branch: `git checkout -b feat/nome-da-feature`
   * Implementar e validar as mudanças localmente.
   * Solicitar teste e aprovação do usuário.
   * Após aprovação: realizar commits claros no padrão Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`).
   * Fazer push da branch: `git push -u origin feat/nome-da-feature`
   * Fazer merge na `main`: `git checkout main` -> `git merge feat/nome-da-feature` -> `git push origin main`
4. **Registro de Erros e Soluções (`docs/erros_solucoes.md`):**
   * Sempre que encontrar um erro mais complicado, comportamento atípico de bibliotecas ou bug que possa impactar o desenvolvimento futuro, **atualizar obrigatoriamente o arquivo `docs/erros_solucoes.md`** logo após o push ou merge na `main`.

---

## 6. Layout e Design do Sistema (Padrão Visual Consolidado)

Todas as telas (**Home**, **Atlas** e **Chatbot**) compartilham a mesma identidade visual institucional e hierarquia de informação:

* **Paleta de Cores Institucional:** Azul marinho profundo (`#0b2545` e `#133b63`), fundos claros (`#ffffff` e `#f8fafc`), cinzas de apoio (`#64748b`, `#e2e8f0`).
* **Paleta Específica do Assistente Virtual:** Tom claro de fundo (`#BAD6D9` com leve transparência / gradiente) e borda de realce em ardósia suave (`#9BA0BF`), diferenciando com elegância as respostas da IA.
* **Hierarquia Tipográfica Padronizada:**
  * **Título Principal / PELT:** `28px` (negrito institucional)
  * **Subtítulos de Cabeçalho:** `24px` a `26px` (peso leve/médio para equilíbrio estético)
  * **Títulos de Seção, Caixas e Pesquisa:** `20px` (com sublinhado sólido de 2px `#0b2545` nas seções de dados)
  * **Títulos das Colunas (Tabelas `th`):** `16px` (fundo `#0b2545`, texto branco, negrito)
  * **Valores e Células de Dados (Tabelas `td`):** `12px` (tipografia compacta e densa para alta legibilidade de dados)
  * **Badges e Tags:** `11px` a `12px`
* **Badges Contextuais:**
  * *Impacto:* Alto (verde `#dcfce7`/`#166534`), Médio (âmbar `#fef3c7`/`#92400e`), Baixo (cinza `#f1f5f9`/`#475569`).
  * *Esfera:* Federal (azul `#e0f2fe`/`#0369a1`), Estadual (verde `#f0fdf4`/`#15803d`), Municipal (amarelo `#fef9c3`/`#a16207`), Privado (roxo `#f5f3ff`/`#6d28d9`).
* **Navegação:** Links nativos com `target="_self"` e sincronização de query params (`?id=...` e `?page=chatbot`) via `app.py`.

---

## 7. Instruções para Inicialização de Novo Chat / Sessão

Para iniciar um novo chat com o assistente para próximas etapas, basta enviar o comando/prompt inicial fazendo referência a este documento:

> *"Estou continuando o desenvolvimento do projeto atlas_web. Por favor, leia o arquivo `docs/regras_projeto.md`, `docs/plano_implementacao.md` e `docs/erros_solucoes.md` para entender o contexto, padrões de código, fluxo de branches/commits, bibliotecas (streamlit==1.36.0) e o modelo de dados."*

---

## 8. Diretrizes de Renderização HTML e Tabelas Estilizadas (Streamlit 1.36.0)

Para detalhes completos, consulte o arquivo [`docs/erros_solucoes.md`](./erros_solucoes.md).

### Resumo das Melhores Práticas:
1. **Escape Defensivo:** Sempre utilizar `html.escape(str(valor))` em todo dado textual dinâmico inserido em templates HTML.
2. **Construção de Strings sem Indentação:** Para evitar que o Markdown converta HTML em `<pre><code>`, concatenar o HTML em linha única ou sem espaços no início da linha.
3. **Navegação sem Iframes:** Para tabelas com links navegáveis, renderizar via `st.markdown(..., unsafe_allow_html=True)` e links com `target="_self"` (evitar `components.html` para tabelas navegáveis devido ao sandbox do iframe).
4. **Estilos Inline para Cards:** Usar `style="..."` diretamente nas tags `<div>` para painéis e cartões de metadados.
