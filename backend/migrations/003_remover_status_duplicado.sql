-- ============================================================
-- MIGRATION: Remover Duplicacao de Status em Reservas
-- Data: 21/12/2024
-- Descricao: Remove campo statusReserva, mantem apenas status
-- ============================================================

-- IMPORTANTE: Fazer backup do banco antes de executar!

BEGIN;

-- ============================================================
-- STEP 1: Sincronizar dados (garantir que ambos estao iguais)
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reservas' AND column_name = 'status'
    ) THEN
        UPDATE reservas
        SET status = status_reserva
        WHERE status IS NULL OR status != status_reserva;

        -- Remover statusReserva (status_reserva no banco)
        ALTER TABLE reservas
        DROP COLUMN IF EXISTS status_reserva;

        -- Garantir indice no campo status
        CREATE INDEX IF NOT EXISTS idx_reservas_status
        ON reservas(status);
    ELSE
        RAISE NOTICE 'Coluna status nao existe em reservas. Migration ignorada.';
    END IF;
END $$;

-- ============================================================
-- STEP 2: Validacao
-- ============================================================

DO $$
DECLARE
    count_reservas INTEGER;
    count_sem_status INTEGER;
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reservas' AND column_name = 'status'
    ) THEN
        SELECT COUNT(*) INTO count_reservas FROM reservas;

        SELECT COUNT(*) INTO count_sem_status
        FROM reservas
        WHERE status IS NULL OR status = '';

        IF count_sem_status > 0 THEN
            RAISE EXCEPTION 'Existem % reservas sem status!', count_sem_status;
        END IF;

        RAISE NOTICE '========================================';
        RAISE NOTICE 'MIGRATION CONCLUIDA COM SUCESSO!';
        RAISE NOTICE '========================================';
        RAISE NOTICE 'Total de reservas: %', count_reservas;
        RAISE NOTICE 'Todas com status valido: OK';
        RAISE NOTICE 'Campo statusReserva removido: OK';
        RAISE NOTICE '========================================';
    ELSE
        RAISE NOTICE 'Validacao ignorada: coluna status nao existe em reservas.';
    END IF;
END $$;

COMMIT;
