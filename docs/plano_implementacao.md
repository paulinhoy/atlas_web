# 🗺️ Plano de Implementação - Atlas Web de Empreendimentos (PELTMG / CODEMGE)

Documento base com o modelo conceitual, arquitetura de dados e planejamento das telas da aplicação web.

---

## 1. Visão Geral e Objetivos

* **Objetivo:** Transformar a ficha técnica do Atlas (originalmente gerada no QGIS) em uma **aplicação web interativa em Python (Streamlit)**.
* **Escopo Inicial:** Focar exclusivamente nos empreendimentos da carteira priorizada contidos em `mvw_8_calcula_impacto_3_pond_cenario` (~1.682 empreendimentos).
* **Vantagens em relação ao QGIS:**
  * Sem limitação de quantidade de obras por empreendimento (anteriormente limitado a 4).
  * Navegação rápida entre projetos via busca e lista interativa.
  * Performance em milissegundos através do pipeline de dados em **Parquet**.
  * Espaço reservado para visualização geoespacial (mapas interativos futuros via GeoPandas/Folium).

---

## 2. Modelo Relacional e Chaves de Dados

```
┌────────────────────────────────────────────────────────┐
│  mvw_8_calcula_impacto (empreendimentos_priorizacao)  │
│  PK: id_empreendimento                                 │
│  - Metadados, Setor, Esfera, Dimensões de Priorização  │
└──────────┬─────────────────────────┬───────────────────┘
           │ (1 : 1)                 │ (1 : N)
           ▼                         ▼
┌──────────────────────────┐  ┌───────────────────────────────────┐
│  dados_financeiro        │  │  tbl_alocacaoempreendimento       │
│  PK: id_empreendimento   │  │  FK: id_empreendimento            │
│  - CAPEX, OPEX, Receita  │  │  - Cenários (1 a 4), CGC, TKU...  │
└──────────────────────────┘  └───────────────────────────────────┘
           │
           │ (1 : N)
           ▼
┌────────────────────────────────────────────────────────┐
│  vw_obra (obras_priorizacao)                           │
│  PK: id_obra | FK: id_empreendimento                   │
│  - Descrição da Obra, Intervenção, Tipo Infraestrutura │
└──────────┬─────────────────────────────────────────────┘
           │ (1 : N)
           ▼
┌────────────────────────────────────────────────────────┐
│  vw_custo_economico (custo_obra)                       │
│  FK: id_obra, id_empreendimento, id_cenario            │
│  - Valores adotados/estimados de CAPEX e OPEX por obra │
└────────────────────────────────────────────────────────┘
```

---

## 3. Arquitetura do Projeto

```
atlas_web/
├── app.py                      # Roteador Streamlit (alterna entre Home, Atlas e Chatbot)
│
├── views/                      # Telas modulares
│   ├── home.py                 # Tela 1: Lista e busca dos empreendimentos priorizados
│   ├── atlas.py                # Tela 2: Ficha Técnica completa (cópia fiel do layout QGIS)
│   └── chatbot.py              # Tela 3: Assistente Virtual / Chatbot isolado do Atlas
│
├── services/                   # Camada de serviços e dados
│   ├── data_loader.py          # Leitor otimizado dos arquivos .parquet com cache
│   └── map_service.py          # 🌟 Módulo exclusivo e isolado de renderização geoespacial (Folium)
│
├── data/
│   ├── raw/                    # CSVs brutos e JSON geoespacial extraídos do PostGIS
│   └── processed/              # Arquivos .parquet gerados pelo ETL (Snappy)
│
├── scripts/
│   ├── process_data.py         # Conversão CSV -> Parquet com tratamento de acentuação
│   └── process_geo.py          # Conversão JSON Geoespacial -> Parquet com WKT
│
├── docs/
│   ├── plano_implementacao.md  # Este documento de referência e arquitetura
│   ├── regras_projeto.md       # Guia de regras, convenções e fluxo Git
│   └── erros_solucoes.md       # Base de conhecimento de erros e soluções
└── requirements.txt            # Dependências Python (com streamlit==1.36.0)
```

---

## 4. Estrutura da Página do Atlas (Réplica do QGIS)

A página de detalhe (`views/atlas.py`) é dividida nas seguintes seções:

### 1. Cabeçalho Institucional
* **Logos:** PELTMG e CODEMGE.
* **Título:** `[id_empreendimento] - [nome_empreendimento]`.
* **Sub-cabeçalho:** Setor (`setor`) | Esfera (`esfera_acao`).
* **Botão Flutuante de Retorno:** Acompanha toda a rolagem da tela no canto inferior esquerdo.

### 2. Seção Superior (Dividida em 2 Colunas)
* **Coluna Esquerda (Metadados Técnicos):**
  * Origem (`origem_ajustada`)
  * Status (`descr_status_empreendimento`)
  * Natureza (`natureza_empreendimento`)
  * Extensão total em Km (calculada a partir da soma das obras)
  * Grupo de Modelagem (`grupo_modelagem`)
  * Responsável atual da infraestrutura (`responsavel_gestao_infraestrutura`)
  * Duração estimada (`data_inicio_obra` - `data_conclusao_obra`)
* **Coluna Direita (Espaço Geoespacial Modular):**
  * Mapa interativo gerado por `services/map_service.py` via Folium (CartoDB Positron).
  * Renderização de intervenções lineares (traçado azul escuro) e pontuais (marcadores circulares).
  * Enquadramento automático (*bounding box*) focado no traçado do projeto.
  * Legenda institucional das intervenções e camadas socioambientais.

### 3. Seção Inferior (Tabelas e Indicadores)
1. **Resultados da Priorização:**
   * Estratégica | Financeira | Socioeconômica | Comercial | Gerencial | Índice de Classificação (`ic_3_pond`) | Impacto.
2. **Dados Financeiros:**
   * CAPEX (R$) | OPEX (R$) | Valor Total (R$) | Receita Total (R$) | TIRM (%) | Viabilidade.
3. **Dados de Alocação 2055:**
   * Tabela por cenário (1 a 4) com: Cenário, CGC, CGNC, GL, GSA, GSM, OGSM, TKU Total.
4. **Detalhamento das Obras:**
   * Tabela completa com todas as obras vinculadas ao empreendimento (sem limitação de 4).
   * **Ordenação automática decrescente pelo Valor da Obra (do mais caro ao mais barato)**.
   * Cabeçalho fixo (*sticky*) para rolagem confortável.

---

## 5. Arquitetura da Implementação do Mapa Geoespacial

A integração do mapa foi projetada para ser **100% modular, desacoplada e de alta performance**:

1. **Pipeline de Dados Geoespaciais (`scripts/process_geo.py`):**
   * Entrada: `mvw_empreendimento_geo_*.json` (~267 MB) contendo geometrias em formato WKT (Well-Known Text).
   * Saída: `data/processed/empreendimento_geo.parquet` (~108 MB) comprimido com **Snappy**.
   * Normalização: Conversão de tipos numéricos e limpeza de *Mojibake* nas colunas textuais.

2. **Carregamento Otimizado (`services/data_loader.py`):**
   * Função `get_empreendimento_geo()` decorada com `@st.cache_data(show_spinner=False)`.
   * Leitura sob demanda com cache permanente em memória RAM, dispensando conexões com banco durante a navegação.

3. **Módulo de Renderização Geoespacial (`services/map_service.py`):**
   * **Responsabilidade Única:** O módulo cuida exclusivamente da lógica SIG.
   * **Parser Shapely:** Converte os WKTs `geom_linha` (`MultiLineString`) e `geom_ponto` (`MultiPoint`) em objetos geométricos.
   * **Bounding Box Dinâmico:** Calcula a envolvente (`get_combined_bounds`) e aplica `m.fit_bounds()` com padding para enquadramento perfeito.
   * **Estilização Folium:** Camada base *CartoDB Positron* (fundo neutro claro), traçados lineares em `#1a5276` (espessura 4.5) e círculos pontuais com borda azul marinho `#0b2545`.
   * **Renderização Segura:** Utiliza `streamlit_folium.folium_static` com altura fixa de 330px, encaixando-se perfeitamente ao lado do card de metadados sem provocar re-execuções na navegação.
   * **Fallback Elegante:** Caso o empreendimento não possua geometrias vetorizadas, exibe um painel amigável de aviso.

4. **Integração Plug-and-Play no Atlas (`views/atlas.py`):**
   * A view apenas invoca `map_service.render_map(empreendimento_id)` dentro da coluna direita.

---

## 6. Arquitetura da Tela do Assistente Virtual / Chatbot (`views/chatbot.py`)

A interface do chatbot foi implementada de forma **100% isolada e modular**:

1. **Roteamento por Query Param (`?page=chatbot`):**
   * O arquivo `app.py` direciona a renderização para `views/chatbot.py` sem afetar as rotas da Home (`/`) e do Atlas (`/?id=X`).
2. **Botões Flutuantes Sincronizados:**
   * Na **Home**, um botão flutuante estilizado no padrão `.atlas-floating-chat-btn` direciona para o assistente.
   * No **Chatbot**, o botão flutuante `.atlas-floating-back-btn` com texto *"Voltar para a Lista"* retorna de forma síncrona para a Home (`?`).
3. **Design Moderno:**
   * Alinhamento universal: mensagens do usuário à direita (em azul PELT) e respostas do assistente à esquerda (em fundo claro).
   * Ocultação de avatares genéricos para foco exclusivo no conteúdo.
   * Campo de digitação em formato de cápsula com botão de envio alinhado e sem caixas cinzas/bege residuais.

---

## 7. Roteiro de Entregas e Próximos Passos

- [x] **Etapa 1:** Configuração da estrutura modular de pastas e pipeline de dados (`scripts/process_data.py` -> Parquet).
- [x] **Etapa 2:** Montar a **Tela 1 (Home)** com a tabela de seleção rápida dos empreendimentos priorizados, busca, filtros e navegação.
- [x] **Etapa 3:** Montar a **Tela 2 (Atlas)** com a estrutura visual fiel à imagem do QGIS (cabeçalho, metadados, espaço do mapa e as 4 tabelas de dados).
- [x] **Etapa 4:** Refinamentos de formatação monetária (R$), design institucional, botão flutuante, ordenação decrescente de obras e integração do mapa geoespacial modular.
- [x] **Etapa 5:** Criação da interface modular e estilizada do **Assistente Virtual (Chatbot)** com navegação flutuante.
- [x] **Etapa 6:** Integração analítica do Chatbot com os dados locais (`data_loader`), LangChain com Function Calling (5 tools), multi-provider (Gemini e OpenAI) e logging de conformidade.
- [ ] **Etapa 7:** Adequação dinâmica das legendas e camadas socioambientais adicionais no mapa.
