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
├── app.py                      # Roteador Streamlit (alterna entre Home e Atlas)
│
├── views/                      # Telas modulares
│   ├── home.py                 # Tela 1: Lista e busca dos empreendimentos priorizados
│   └── atlas.py                # Tela 2: Ficha Técnica completa (cópia fiel do layout QGIS)
│
├── components/                 # Componentes visuais reutilizáveis
│   ├── header.py               # Cabeçalho institucional (logos, título, badges)
│   ├── metadata_card.py        # Painel esquerdo com metadados do projeto
│   ├── map_container.py        # Painel direito (espaço reservado para mapa geoespacial)
│   └── tables.py               # Tabelas formatadas (Priorização, Finanças, Alocação, Obras)
│
├── services/                   # Camada de dados com cache do Streamlit
│   └── data_loader.py          # Leitor otimizado dos arquivos .parquet
│
├── data/
│   ├── raw/                    # CSVs brutos extraídos do banco PostGIS
│   └── processed/              # Arquivos .parquet gerados pelo ETL
│
├── scripts/
│   └── process_data.py         # Script de conversão CSV -> Parquet com tratamento de nomes
│
├── docs/
│   └── plano_implementacao.md  # Este documento de referência
└── requirements.txt            # Dependências Python
```

---

## 4. Estrutura da Página do Atlas (Réplica do QGIS)

A página de detalhe (`views/atlas.py`) será dividida nas seguintes seções:

### 1. Cabeçalho Institucional
* **Logos:** PELTMG e CODEMGE.
* **Título:** `[id_empreendimento] - [nome_empreendimento]`.
* **Sub-cabeçalho:** Setor (`setor`) | Esfera (`esfera_acao`).

### 2. Seção Superior (Dividida em 2 Colunas)
* **Coluna Esquerda (Metadados Técnicos):**
  * Origem (`origem_ajustada`)
  * Status (`descr_status_empreendimento`)
  * Natureza (`natureza_empreendimento`)
  * Extensão total em Km (calculada a partir da soma das obras)
  * Grupo de Modelagem (`grupo_modelagem`)
  * Responsável atual da infraestrutura (`responsavel_gestao_infraestrutura`)
  * Duração estimada (`data_inicio_obra` - `data_conclusao_obra`)
* **Coluna Direita (Espaço Geoespacial):**
  * Container reservado para visualização cartográfica interativa (GeoPandas / Folium).
  * Legenda de intervenções lineares, pontuais e camadas socioambientais.

### 3. Seção Inferior (Tabelas e Indicadores)
1. **Resultados da Priorização:**
   * Estratégica | Financeira | Socioeconômica | Comercial | Gerencial | Índice de Classificação (`ic_3_pond`) | Impacto.
2. **Dados Financeiros:**
   * CAPEX (R$) | OPEX (R$) | Valor Total (R$) | Receita Total (R$) | TIRM (%) | Viabilidade.
3. **Dados de Alocação 2055:**
   * Tabela por cenário (1 a 4) com: Cenário, CGC, CGNC, GL, GSA, GSM, OGSM, TKU Total.
4. **Detalhamento das Obras:**
   * Tabela completa com todas as obras vinculadas ao empreendimento (sem limitação de 4):
   * Descrição da Obra | Intervenção | Tipo da Infraestrutura | Extensão (Km) | Valor da Obra (R$).

---

## 5. Roteiro de Entregas e Próximos Passos

- [x] **Etapa 1:** Configuração da estrutura modular de pastas e pipeline de dados (`scripts/process_data.py` -> Parquet).
- [x] **Etapa 2:** Montar a **Tela 1 (Home)** com a tabela de seleção rápida dos empreendimentos priorizados, busca, filtros e navegação.
- [ ] **Etapa 3:** Montar a **Tela 2 (Atlas)** com a estrutura visual fiel à imagem do QGIS (cabeçalho, metadados, espaço do mapa e as 4 tabelas de dados).
- [ ] **Etapa 4:** Refinamentos de formatação monetária (R$), design institucional, busca na Home e futura integração das geometrias.
