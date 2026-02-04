-- ============================================================
-- MIGRATION: Correção do Sistema de Pontos
-- Data: 21/12/2024
-- Descrição: Adiciona relacionamentos bidirecionais e campos
--            de rastreabilidade no sistema de pontos
-- ============================================================

-- ⚠️ IMPORTANTE: Fazer backup do banco antes de executar!
-- pg_dump -U usuario -d hotel_cabo_frio > backup_antes_migration_pontos.sql

BEGIN;

-- ============================================================
-- STEP 1: Criar ENUMs
-- ============================================================

DO $$ BEGIN
    CREATE TYPE "TipoTransacaoPontos" AS ENUM (
        'CREDITO',
        'DEBITO',
        'AJUSTE',
        'ESTORNO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE "OrigemTransacaoPontos" AS ENUM (
        'RESERVA',
        'AJUSTE_MANUAL',
        'CONVITE',
        'RESGATE',
        'EXPIRACAO',
        'CANCELAMENTO'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================
-- STEP 2: Adicionar novos campos em transacoes_pontos
-- ============================================================

-- Adicionar cliente_id (relacionamento direto)
ALTER TABLE transacoes_pontos 
ADD COLUMN IF NOT EXISTS cliente_id INTEGER;

-- Adicionar funcionario_id (rastrear quem fez ajuste)
ALTER TABLE transacoes_pontos 
ADD COLUMN IF NOT EXISTS funcionario_id INTEGER;

-- Adicionar reserva_id (se ainda não existe)
ALTER TABLE transacoes_pontos 
ADD COLUMN IF NOT EXISTS reserva_id INTEGER;

-- Adicionar saldos para auditoria
ALTER TABLE transacoes_pontos 
ADD COLUMN IF NOT EXISTS saldo_anterior INTEGER;

ALTER TABLE transacoes_pontos 
ADD COLUMN IF NOT EXISTS saldo_posterior INTEGER;

-- Modificar tipo para aceitar valores negativos (débitos)
-- pontos já é INTEGER, então aceita negativos

-- ============================================================
-- STEP 3: Atualizar dados existentes
-- ============================================================

-- Preencher cliente_id baseado no usuario_id
UPDATE transacoes_pontos tp
SET cliente_id = up.cliente_id
FROM usuarios_pontos up
WHERE tp.usuario_id = up.id
  AND tp.cliente_id IS NULL;

-- ============================================================
-- STEP 4: Adicionar constraints e foreign keys
-- ============================================================

-- Foreign key para cliente
ALTER TABLE transacoes_pontos
ADD CONSTRAINT IF NOT EXISTS fk_transacoes_pontos_cliente
FOREIGN KEY (cliente_id) REFERENCES clientes(id)
ON DELETE CASCADE;

-- Foreign key para funcionário (opcional)
ALTER TABLE transacoes_pontos
ADD CONSTRAINT IF NOT EXISTS fk_transacoes_pontos_funcionario
FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
ON DELETE SET NULL;

-- Foreign key para reserva (opcional)
ALTER TABLE transacoes_pontos
ADD CONSTRAINT IF NOT EXISTS fk_transacoes_pontos_reserva
FOREIGN KEY (reserva_id) REFERENCES reservas(id)
ON DELETE SET NULL;

-- Tornar cliente_id obrigatório (após preencher dados existentes)
ALTER TABLE transacoes_pontos
ALTER COLUMN cliente_id SET NOT NULL;

-- ============================================================
-- STEP 5: Criar índices para performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_cliente_id 
ON transacoes_pontos(cliente_id);

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_reserva_id 
ON transacoes_pontos(reserva_id);

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_funcionario_id 
ON transacoes_pontos(funcionario_id);

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_created_at 
ON transacoes_pontos(created_at);

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_tipo 
ON transacoes_pontos(tipo);

CREATE INDEX IF NOT EXISTS idx_transacoes_pontos_origem 
ON transacoes_pontos(origem);

-- ============================================================
-- STEP 6: Atualizar valores de tipo e origem para ENUMs
-- ============================================================

-- Mapear valores antigos para novos ENUMs
UPDATE transacoes_pontos
SET tipo = CASE 
    WHEN tipo = 'GANHO' THEN 'CREDITO'
    WHEN tipo = 'credito' THEN 'CREDITO'
    WHEN tipo = 'debito' THEN 'DEBITO'
    WHEN tipo = 'ajuste' THEN 'AJUSTE'
    ELSE tipo
END
WHERE tipo IN ('GANHO', 'credito', 'debito', 'ajuste');

UPDATE transacoes_pontos
SET origem = CASE 
    WHEN origem = 'checkout_reserva' THEN 'RESERVA'
    WHEN origem = 'convite' THEN 'CONVITE'
    WHEN origem = 'convite_indicacao' THEN 'CONVITE'
    WHEN origem = 'ajuste_manual' THEN 'AJUSTE_MANUAL'
    WHEN origem = 'resgate' THEN 'RESGATE'
    ELSE origem
END
WHERE origem IN ('checkout_reserva', 'convite', 'convite_indicacao', 'ajuste_manual', 'resgate');

-- ============================================================
-- STEP 7: Validações finais
-- ============================================================

-- Verificar se todos os registros têm cliente_id
DO $$
DECLARE
    count_sem_cliente INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_sem_cliente
    FROM transacoes_pontos
    WHERE cliente_id IS NULL;
    
    IF count_sem_cliente > 0 THEN
        RAISE EXCEPTION 'Existem % transações sem cliente_id!', count_sem_cliente;
    END IF;
    
    RAISE NOTICE 'Validação OK: Todas as transações têm cliente_id';
END $$;

-- ============================================================
-- STEP 8: Estatísticas finais
-- ============================================================

DO $$
DECLARE
    total_transacoes INTEGER;
    transacoes_com_reserva INTEGER;
    transacoes_com_funcionario INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_transacoes FROM transacoes_pontos;
    SELECT COUNT(*) INTO transacoes_com_reserva FROM transacoes_pontos WHERE reserva_id IS NOT NULL;
    SELECT COUNT(*) INTO transacoes_com_funcionario FROM transacoes_pontos WHERE funcionario_id IS NOT NULL;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION CONCLUÍDA COM SUCESSO!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total de transações: %', total_transacoes;
    RAISE NOTICE 'Transações com reserva: %', transacoes_com_reserva;
    RAISE NOTICE 'Transações com funcionário: %', transacoes_com_funcionario;
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================
-- ROLLBACK (caso necessário)
-- ============================================================
-- Para reverter esta migration, execute:
-- 
-- BEGIN;
-- ALTER TABLE transacoes_pontos DROP CONSTRAINT IF EXISTS fk_transacoes_pontos_cliente;
-- ALTER TABLE transacoes_pontos DROP CONSTRAINT IF EXISTS fk_transacoes_pontos_funcionario;
-- ALTER TABLE transacoes_pontos DROP CONSTRAINT IF EXISTS fk_transacoes_pontos_reserva;
-- ALTER TABLE transacoes_pontos DROP COLUMN IF EXISTS cliente_id;
-- ALTER TABLE transacoes_pontos DROP COLUMN IF EXISTS funcionario_id;
-- ALTER TABLE transacoes_pontos DROP COLUMN IF EXISTS saldo_anterior;
-- ALTER TABLE transacoes_pontos DROP COLUMN IF EXISTS saldo_posterior;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_cliente_id;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_reserva_id;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_funcionario_id;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_created_at;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_tipo;
-- DROP INDEX IF EXISTS idx_transacoes_pontos_origem;
-- DROP TYPE IF EXISTS "TipoTransacaoPontos" CASCADE;
-- DROP TYPE IF EXISTS "OrigemTransacaoPontos" CASCADE;
-- COMMIT;

