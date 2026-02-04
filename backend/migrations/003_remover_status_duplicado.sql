-- ============================================================
-- MIGRATION: Remover Duplicação de Status em Reservas
-- Data: 21/12/2024
-- Descrição: Remove campo statusReserva, mantém apenas status
-- ============================================================

-- ⚠️ IMPORTANTE: Fazer backup do banco antes de executar!

BEGIN;

-- ============================================================
-- STEP 1: Sincronizar dados (garantir que ambos estão iguais)
-- ============================================================

-- Copiar valores de statusReserva para status (caso divergente)
UPDATE reservas
SET status = status_reserva
WHERE status != status_reserva OR status IS NULL;

-- ============================================================
-- STEP 2: Remover coluna duplicada
-- ============================================================

-- Remover statusReserva (status_reserva no banco)
ALTER TABLE reservas
DROP COLUMN IF EXISTS status_reserva;

-- ============================================================
-- STEP 3: Garantir índice no campo status
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_reservas_status 
ON reservas(status);

-- ============================================================
-- STEP 4: Validação
-- ============================================================

DO $$
DECLARE
    count_reservas INTEGER;
    count_sem_status INTEGER;
BEGIN
    -- Contar total de reservas
    SELECT COUNT(*) INTO count_reservas FROM reservas;
    
    -- Contar reservas sem status
    SELECT COUNT(*) INTO count_sem_status
    FROM reservas
    WHERE status IS NULL OR status = '';
    
    IF count_sem_status > 0 THEN
        RAISE EXCEPTION 'Existem % reservas sem status!', count_sem_status;
    END IF;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION CONCLUÍDA COM SUCESSO!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total de reservas: %', count_reservas;
    RAISE NOTICE 'Todas com status válido: OK';
    RAISE NOTICE 'Campo statusReserva removido: OK';
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================
-- ROLLBACK (caso necessário)
-- ============================================================
-- Para reverter esta migration, execute:
-- 
-- BEGIN;
-- ALTER TABLE reservas ADD COLUMN status_reserva VARCHAR(50);
-- UPDATE reservas SET status_reserva = status;
-- ALTER TABLE reservas ALTER COLUMN status_reserva SET DEFAULT 'PENDENTE';
-- COMMIT;

