-- =============================================================================
-- PELTMG / Atlas de Empreendimentos - Queries de Extração SQL (PostGIS)
-- Arquivo: docs/queries_extracao.sql
-- Registrado em: 10/09/2026
-- =============================================================================

-- 1. Carteiras (vw_dadosgerais_plataformaonline) — um arquivo por schema
-- Origem dos arquivos brutos (nome = <schema>_vw_dadosgerais_plataformaonline_<data>.csv):
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


-- 3. Dados Financeiros Consolidados (resumo_financeiro)
-- Origem do arquivo bruto: data/raw/resumo_financeiro*.csv
-- Processado para: data/processed/resumo_financeiro.parquet
SELECT *
FROM cenario_recomendado_1.resumo_financeiro_otimizado_1
WHERE receita_codemge IS NOT NULL AND id_cenario >= 4
UNION ALL 
SELECT *
FROM cenario_recomendado_2.resumo_financeiro_otimizado_2
WHERE receita_codemge IS NOT NULL AND id_cenario >= 4;
