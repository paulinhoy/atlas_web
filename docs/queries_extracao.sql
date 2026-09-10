-- =============================================================================
-- PELTMG / Atlas de Empreendimentos - Queries de Extração SQL (PostGIS)
-- Arquivo: docs/queries_extracao.sql
-- Registrado em: 10/09/2026
-- =============================================================================

-- 1. Priorizações (mvw_8_calcula_impacto_3_pond_cenario)
-- Origem do arquivo bruto: data/raw/priorizacao*.csv
-- Processado para: data/processed/empreendimentos_priorizacao.parquet
SELECT *,
 'priorizacao geral' AS fonte_priorizacao
FROM priorizacao_peltlp.mvw_8_calcula_impacto_3_pond_cenario -- Cenario geral
UNION ALL 
SELECT *,
 'cenario otimizado' AS fonte_priorizacao
FROM cenario_recomendado_1.cr0_mvw_8_calcula_impacto_3_pond_cenario  -- Cenario otimizado 
UNION ALL 
SELECT *,
 'cenario recomendado' AS fonte_priorizacao
FROM cenario_recomendado_2.cr0_mvw_8_calcula_impacto_3_pond_cenario; -- Cenario recomendado


-- 2. Alocação de Fluxos 2055 (tbl_alocacaoempreendimento)
-- Origem do arquivo bruto: data/raw/alocacao_total*.csv
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
