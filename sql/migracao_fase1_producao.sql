-- =========================================================
-- MIGRACAO FASE 1 - PRODUCAO
-- Execute cada bloco EM ORDEM, validando antes de seguir
-- =========================================================

-- =========================================================
-- BLOCO A: Criar campos em TB_INSTITUICAO
-- =========================================================
ALTER TABLE TB_INSTITUICAO
ADD COLUMN IF NOT EXISTS COD_COMPARTILHADO DECIMAL(10,0) NULL,
ADD COLUMN IF NOT EXISTS DT_CORTE_INICIAL DATETIME NULL,
ADD COLUMN IF NOT EXISTS FREQUENCIA_CORTE VARCHAR(20) NULL;

-- Validacao:
-- SHOW COLUMNS FROM TB_INSTITUICAO
-- WHERE Field IN ('COD_COMPARTILHADO','DT_CORTE_INICIAL','FREQUENCIA_CORTE');

-- =========================================================
-- BLOCO B: Popular cod_compartilhado
-- =========================================================
UPDATE TB_INSTITUICAO i
JOIN (
    SELECT
        COD_INSTITUICAO,
        MAX(COD_COMPARTILHADO) AS COD_COMPARTILHADO
    FROM TB_CONTRATO
    GROUP BY COD_INSTITUICAO
) c ON c.COD_INSTITUICAO = i.COD_INSTITUICAO
SET i.COD_COMPARTILHADO = c.COD_COMPARTILHADO
WHERE i.COD_COMPARTILHADO IS NULL;

-- =========================================================
-- BLOCO C: Popular dt_corte_inicial e frequencia_corte
-- =========================================================
UPDATE TB_INSTITUICAO i
JOIN (
    SELECT
        COD_INSTITUICAO,
        MAX(DT_CORTE_INICIAL) AS DT_CORTE_INICIAL,
        MAX(FREQUENCIA_CORTE) AS FREQUENCIA_CORTE
    FROM TB_CONTRATO
    GROUP BY COD_INSTITUICAO
) c ON c.COD_INSTITUICAO = i.COD_INSTITUICAO
SET
    i.DT_CORTE_INICIAL = c.DT_CORTE_INICIAL,
    i.FREQUENCIA_CORTE = c.FREQUENCIA_CORTE
WHERE i.DT_CORTE_INICIAL IS NULL
   OR i.FREQUENCIA_CORTE IS NULL;

-- Validacao:
-- SELECT
--     SUM(i.COD_COMPARTILHADO IS NULL) AS sem_cod_compartilhado,
--     SUM(i.DT_CORTE_INICIAL IS NULL) AS sem_dt_corte_inicial,
--     SUM(i.FREQUENCIA_CORTE IS NULL) AS sem_frequencia_corte
-- FROM TB_INSTITUICAO i
-- JOIN TB_CONTRATO c ON c.COD_INSTITUICAO = i.COD_INSTITUICAO;

-- =========================================================
-- BLOCO D: Ajustar collation de FREQUENCIA_CORTE
-- =========================================================
ALTER TABLE TB_INSTITUICAO
MODIFY COLUMN FREQUENCIA_CORTE VARCHAR(20)
CHARACTER SET latin1
COLLATE latin1_swedish_ci
NULL;

-- Validacao:
-- SELECT TABLE_NAME, COLUMN_NAME, COLLATION_NAME
-- FROM information_schema.COLUMNS
-- WHERE TABLE_SCHEMA = DATABASE()
--   AND TABLE_NAME = 'TB_INSTITUICAO'
--   AND COLUMN_NAME = 'FREQUENCIA_CORTE';

-- =========================================================
-- BLOCO E: Sincronizar divergencias DT_FIM
-- =========================================================
UPDATE TB_CONTRATO c
JOIN TB_INSTITUICAO i ON i.COD_INSTITUICAO = c.COD_INSTITUICAO
SET c.DT_FIM = i.DT_FIM
WHERE c.COD_INSTITUICAO IN (
    2007021321, 2011030401, 2020060901, 2023092201
)
  AND NOT (c.DT_FIM <=> i.DT_FIM);

-- =========================================================
-- BLOCO E2: Sincronizar divergencias DT_CORTE_INICIAL e FREQUENCIA_CORTE
-- =========================================================
UPDATE TB_CONTRATO c
JOIN TB_INSTITUICAO i ON i.COD_INSTITUICAO = c.COD_INSTITUICAO
SET
    c.DT_CORTE_INICIAL = i.DT_CORTE_INICIAL,
    c.FREQUENCIA_CORTE = i.FREQUENCIA_CORTE
WHERE c.COD_INSTITUICAO = 2024062501;

-- =========================================================
-- BLOCO F: Popular NUM_CONTRATO da instituicao
-- =========================================================
UPDATE TB_INSTITUICAO i
JOIN (
    SELECT
        COD_INSTITUICAO,
        MIN(TRIM(NUM_CONTRATO)) AS NUM_CONTRATO
    FROM TB_CONTRATO
    WHERE NUM_CONTRATO IS NOT NULL
      AND TRIM(NUM_CONTRATO) <> ''
      AND TRIM(NUM_CONTRATO) <> '0'
    GROUP BY COD_INSTITUICAO
    HAVING COUNT(DISTINCT TRIM(NUM_CONTRATO)) = 1
) src ON src.COD_INSTITUICAO = i.COD_INSTITUICAO
SET i.NUM_CONTRATO = src.NUM_CONTRATO
WHERE NOT (i.NUM_CONTRATO <=> src.NUM_CONTRATO);

-- Validacao final alinhamento:
-- SELECT
--     SUM(NOT (i.COD_COMPARTILHADO <=> c.COD_COMPARTILHADO)) AS diverg_compartilhado,
--     SUM(NOT (i.DT_CORTE_INICIAL <=> c.DT_CORTE_INICIAL)) AS diverg_corte,
--     SUM(NOT (i.FREQUENCIA_CORTE <=> c.FREQUENCIA_CORTE)) AS diverg_frequencia,
--     SUM(NOT (i.NUM_CONTRATO <=> c.NUM_CONTRATO)) AS diverg_contrato,
--     SUM(NOT (i.DT_INI <=> c.DT_INI)) AS diverg_dt_ini,
--     SUM(NOT (i.DT_FIM <=> c.DT_FIM)) AS diverg_dt_fim
-- FROM TB_CONTRATO c
-- JOIN TB_INSTITUICAO i ON i.COD_INSTITUICAO = c.COD_INSTITUICAO;

-- =========================================================
-- BLOCO G: Normalizar servicos (opcional - apenas se nao executou)
--   Este bloco explode linhas multi-servico em linhas individuais
--   Execute apenas UMA vez
-- =========================================================
-- CREATE TABLE BKP_TB_CONTRATO_PRE_NORMALIZACAO LIKE TB_CONTRATO;
-- INSERT INTO BKP_TB_CONTRATO_PRE_NORMALIZACAO SELECT * FROM TB_CONTRATO;

-- UPDATE TB_CONTRATO SET SERVICOS_CONTRATADOS = 'Individual'
-- WHERE SERVICOS_CONTRATADOS = 'Individual, Lote, API';
--
-- INSERT INTO TB_CONTRATO (...) SELECT ... 'Lote' ...
-- FROM BKP_TB_CONTRATO_PRE_NORMALIZACAO
-- WHERE SERVICOS_CONTRATADOS = 'Individual, Lote, API';
--
-- INSERT INTO TB_CONTRATO (...) SELECT ... 'API' ...
-- FROM BKP_TB_CONTRATO_PRE_NORMALIZACAO
-- WHERE SERVICOS_CONTRATADOS = 'Individual, Lote, API';
--
-- REPETIR PARA 'Individual, Lote' (inserir Lote)
-- REPETIR PARA 'Individual, API'  (inserir API)
--
-- Detalhes completos em: sql/normalizar_servicos.sql
