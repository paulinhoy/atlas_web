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
├── app.py                      # Roteador principal do Streamlit (navegação entre Home e Atlas)
├── .venv/                      # Ambiente virtual Python (ignorado pelo Git)
│
├── views/                      # TELAS MODULARES DA APLICAÇÃO
│   ├── home.py                 # Tela 1: Painel Executivo, KPIs, busca e tabela de empreendimentos
│   └── atlas.py                # Tela 2: Ficha Técnica do Atlas (layout réplica do QGIS)
│
├── services/                   # SERVIÇOS DE DADOS
│   └── data_loader.py          # Leitor otimizado com @st.cache_data e limpeza defensiva de strings
│
├── data/                       # ARMAZENAMENTO DE DADOS (ignorado pelo Git)
│   ├── raw/                    # CSVs brutos extraídos do PostGIS (suporta subpastas por data)
│   └── processed/              # Arquivos .parquet otimizados gerados pelo script ETL
│
├── scripts/                    # SCRIPTS AUXILIARES E PIPELINE ETL
│   ├── process_data.py         # Mapeia CSVs brutos para Parquet com tratamento de Mojibake
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
│   └── regras_projeto.md       # Este documento de contexto e convenções
│
└── requirements.txt            # Dependências com streamlit==1.36.0
```

---

## 4. Pipeline de Dados e Dicionário de Mapeamentos (CSV ➔ Parquet)

Os dados são extraídos do banco de dados PostGIS (codificação original ISO-8859-1/Latin1) e convertidos para Parquet UTF-8 otimizado pelo script `scripts/process_data.py`:

| Visão/Tabela Original PostGIS | Parquet Otimizado em `data/processed/` | Chave(s) Principal(is) | Função no Sistema |
| :--- | :--- | :--- | :--- |
| `mvw_8_calcula_impacto_*` | `empreendimentos_priorizacao.parquet` | `id_empreendimento` | Tabela mestra dos ~1.682 projetos priorizados + Notas/Índice de Priorização |
| `vw_empreendimento_custo_economico_lp_*` | `dados_financeiro.parquet` | `id_empreendimento` | Dados financeiros consolidados (CAPEX, OPEX, Receita, Mês Base) |
| `tbl_alocacaoempreendimento_*` | `alocacao_empreendimento.parquet` | `id_empreendimento`, `id_cenario` | Dados de alocação de tráfego/fluxo para 2055 por Cenário (1 a 4) |
| `vw_obra_*` | `obras_priorizacao.parquet` | `id_obra`, `id_empreendimento` | Cadastro e detalhamento individual de cada obra |
| `vw_custo_economico_*` | `custo_obra.parquet` | `id_obra`, `id_empreendimento`, `id_cenario` | Custos detalhados por obra e cenário |

### ⚠️ Regras Cruciais de Tratos com Dados:
1. **Sem limite de obras na Web:** Diferente da versão física do QGIS que limitava em 4 obras, a versão web deve exibir **todas** as obras relacionadas na tabela de detalhamento.
2. **Formatação Brasileira:** Exibir números inteiros com ponto de milhar (`1.682`), números decimais e índices com vírgula (`0,4031`) e valores financeiros formatados em Reais (`R$ 289.892.422,00`).
3. **Tratamento de Mojibake:** Sempre utilizar a função `fix_mojibake` para tratar codificações duplas provenientes da exportação do banco.

---

## 5. Fluxo de Trabalho com Git e GitHub

1. **Estratégia de Branches:**
   * A branch `main` é mantida **sempre estável e funcional**.
   * Cada nova funcionalidade/etapa deve ser desenvolvida em uma nova branch temática (ex: `feat/tela-atlas`, `feat/mapa-geopandas`, `fix/ajuste-tabelas`).
2. **Passo a Passo de Desenvolvimento:**
   * Criar branch: `git checkout -b feat/nome-da-feature`
   * Implementar e validar as mudanças localmente.
   * Realizar commits claros com mensagens no padrão Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`).
   * Fazer push da branch: `git push -u origin feat/nome-da-feature`
   * Fazer merge na `main`: `git checkout main` -> `git merge feat/nome-da-feature` -> `git push origin main`

---

## 6. Layout e Design da Tela do Atlas (`views/atlas.py`) — Próxima Etapa

Ao construir a **Tela 2 (Atlas)** na Etapa 3, respeitar fielmente o arranjo visual da imagem de referência do QGIS (`Atlasref.jpeg`):

```
┌────────────────────────────────────────────────────────────────────────┐
│ CABEÇALHO INSTITUCIONAL: Logos PELTMG / CODEMGE | Título | Setor | Esfera │
├───────────────────────────────────┬────────────────────────────────────┤
│ PAINEL ESQUERDO (Ficha Técnica)   │ PAINEL DIREITO (Visualização Mapa) │
│ • Origem, Status, Natureza        │ • Espaço reservado para o mapa     │
│ • Extensão (km), Grupo Modelagem  │ • Legenda de intervenções lineares,│
│ • Responsável, Período de Duração │   pontuais e camadas socioamb.     │
├───────────────────────────────────┴────────────────────────────────────┤
│ TABELA 1: Resultados da Priorização (Estratégica, Financeira, IC, etc.)│
├────────────────────────────────────────────────────────────────────────┤
│ TABELA 2: Dados Financeiros (CAPEX, OPEX, Valor Total, Receita, TIRM)  │
├────────────────────────────────────────────────────────────────────────┤
│ TABELA 3: Dados de Alocação 2055 (Cenários 1, 2, 3 e 4)                │
├────────────────────────────────────────────────────────────────────────┤
│ TABELA 4: Detalhamento de Obras (Todas as obras vinculadas, com filtro)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Instruções para Inicialização de Novo Chat / Sessão

Para iniciar um novo chat com o assistente para próximas etapas, basta enviar o comando/prompt inicial fazendo referência a este documento:

> *"Estou continuando o desenvolvimento do projeto atlas_web. Por favor, leia o arquivo `docs/regras_projeto.md` e `docs/plano_implementacao.md` para entender o contexto, padrões de código, bibliotecas (streamlit==1.36.0) e o modelo de dados."*

---

## 8. Diretrizes de Renderização HTML e Tabelas Estilizadas (Streamlit 1.36.0)

Durante o desenvolvimento do Atlas Web, identificamos comportamentos críticos do parser de Markdown do Streamlit ao renderizar HTML customizado (`st.markdown(..., unsafe_allow_html=True)`):

### ⚠️ Problemas Identificados:
1. **Indentação interpretada como Bloco de Código (`<pre><code>`):** O parser do Markdown interpreta qualquer bloco de texto/HTML indentado com 4 ou mais espaços como código pré-formatado, exibindo as tags HTML cruas na tela (ex: `<tr>`, `<td>`).
2. **Volumes Grandes de Dados em `st.markdown`:** Tabelas com muitas linhas ou estruturas HTML complexas concatenadas em f-strings multi-linha tendem a quebrar ou ter tags escapadas pelo parser.
3. **Caracteres Especiais nos Dados:** Textos provenientes do banco com caracteres como `&`, `<`, `>`, `"`, `'` quebram o parsing HTML se inseridos diretamente.

### ✅ Soluções Padrão Adotadas no Projeto:
1. **Escape Defensivo Obrigatório:** Sempre utilizar `html.escape(str(valor))` em todo dado textual dinâmico inserido em templates HTML.
2. **Construção de Strings sem Indentação:** Para pequenos blocos ou tabelas curtas (ex: Alocação, Priorização), concatenar o HTML sem espaços no início da linha:
   ```python
   # CORRETO:
   rows_html += f"<tr><td>{dado1}</td><td>{dado2}</td></tr>"
   # INCORRETO (gera <pre><code> no markdown):
   rows_html += f"""
       <tr>
           <td>{dado1}</td>
       </tr>
   """
   ```
3. **Estilos Inline para Cards e Metadados:** Usar `style="..."` diretamente nas tags `<div>` para evitar dependência de CSS global não carregado ou sobrescrito.
4. **Uso de `streamlit.components.v1.html` para Tabelas Grandes:** Para tabelas com grande volume de linhas (como o *Detalhamento das Obras* ou listagens completas), utilizar `components.html(table_html, height=..., scrolling=...)` com CSS autocontido (`<style>` dentro da string). Isso garante renderização em sandbox isolado sem interferência do parser Markdown.
