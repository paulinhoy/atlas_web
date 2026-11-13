-- =============================================================================
-- PELTMG / Atlas de Empreendimentos - Queries de Extração SQL (PostGIS)
-- Arquivo: docs/queries_extracao.sql
-- Registrado em: 10/09/2026 | Atualizado em: 13/11/2026 (rodada em data/raw/atualizacao_dados_atlas/)
-- =============================================================================

-- 1. Carteiras (vw_dadosgerais_plataformaonline) — um arquivo por schema
-- Origem dos arquivos brutos (nome = <schema>_vw_dadosgerais_plataformaonline.csv):
--   data/raw/cenario_recomendado_2_vw_dadosgerais*.csv  -> Carteira Recomendada
--   data/raw/cenario_recomendado_1_vw_dadosgerais*.csv  -> Carteira Otimizada
--   data/raw/priorizacao_peltlp_vw_dadosgerais*.csv     -> Carteira de Análise
-- Processado para: data/processed/carteiras.parquet
-- A view traz natureza_empreendimento, grupo_modelagem (nome) e data_inicio/data_conclusao.
-- O id_grupo_modelagem é deduzido do nome pelo dicionário ID_GRUPO_MODELAGEM em scripts/process_data.py.
-- (Consulta registrada a partir dos nomes dos arquivos; confirmar com a exportação real.)
SELECT * FROM cenario_recomendado_2.vw_dadosgerais_plataformaonline;
SELECT * FROM cenario_recomendado_1.vw_dadosgerais_plataformaonline;
SELECT * FROM priorizacao_peltlp.vw_dadosgerais_plataformaonline;


-- 2. Alocação de Fluxos 2055 (tbl_alocacaoempreendimento)
-- Origem do arquivo bruto: data/raw/cenario_recomendado_2_alocacao_geral.csv (compilado pelo responsável,
-- com o Otimizado como cenário 8; a consulta abaixo é a antiga, em que o Otimizado era o 7)
-- Processado para: data/processed/alocacao_empreendimento.parquet
SELECT *
FROM financeiro.tbl_alocacaoempreendimento ta -- Cenarios oficiais (1 a 4)
UNION ALL 
SELECT *
FROM cenario_recomendado_1.tbl_alocacaoempreendimento_otimizado_1 taa  -- id_cenario = 7 (Otimizado)
UNION ALL 
SELECT *
FROM cenario_recomendado_2.tbl_alocacaoempreendimento_otimizado_2 tab  -- id_cenario = 10 (Recomendado)
ORDER BY id_empreendimento, id_cenario;


-- 3. Financeiro completo (CAPEX, OPEX, receita e TIRM em %), um arquivo por schema, sem id_cenario
-- Origem dos arquivos brutos:
--   cenario_recomendado_1_vw_financeiro_completo.csv  -> id_cenario 8 (Otimizado), atribuído pelo ETL
--   cenario_recomendado_2_vw_financeiro_completo.csv  -> id_cenario 10 (Recomendado), atribuído pelo ETL
-- Processado para: data/processed/financeiro_completo.parquet
SELECT * FROM cenario_recomendado_1.vw_financeiro_completo;
SELECT * FROM cenario_recomendado_2.vw_financeiro_completo;


-- 4. Custo econômico das obras (vw_custo_economico), um arquivo por schema
-- Origem dos arquivos brutos:
--   carteira_vw_custo_economico.csv                -> cenários oficiais 1 a 4 (id_cenario do arquivo)
--   cenario_recomendado_1_vw_custo_economico.csv   -> chega com id_cenario 7; o ETL grava 8 (Otimizado)
--   cenario_recomendado_2_vw_custo_economico.csv   -> id_cenario 10 (Recomendado)
-- Processado para: data/processed/custo_obra.parquet (e valor_calculado/origem_valor em obras_priorizacao)
SELECT * FROM carteira.vw_custo_economico;
SELECT * FROM cenario_recomendado_1.vw_custo_economico;
SELECT * FROM cenario_recomendado_2.vw_custo_economico;


-- 5. Obras (vw_obra) e Custo Econômico LP do empreendimento
-- Origem dos arquivos brutos: carteira_vw_obra.csv e carteira_vw_empreendimento_custo_economico_lp.csv
-- Processado para: data/processed/obras_priorizacao.parquet e data/processed/dados_financeiro.parquet
SELECT * FROM carteira.vw_obra;
SELECT * FROM carteira.vw_empreendimento_custo_economico_lp;


-- [DESATIVADO em 13/11/2026] Resumo financeiro antigo, substituído pelo financeiro completo (item 3)
-- Arquivo bruto antigo: data/raw/resumo_financeiro*.csv
SELECT *
FROM cenario_recomendado_1.resumo_financeiro_otimizado_1
WHERE receita_codemge IS NOT NULL AND id_cenario >= 4
UNION ALL 
SELECT *
FROM cenario_recomendado_2.resumo_financeiro_otimizado_2
WHERE receita_codemge IS NOT NULL AND id_cenario >= 4;
