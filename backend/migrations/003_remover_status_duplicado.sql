-- ============================================================
-- MIGRATION: Remover Duplicacao de Status em Reservas
-- Data: 21/12/2024
-- Descricao: Introduz coluna status e prepara migracao do status_reserva
-- ============================================================

BEGIN;

-- Garantir coluna status
ALTER TABLE reservas
ADD COLUMN IF NOT EXISTS status VARCHAR(50);

-- Sincronizar dados (status <- status_reserva)
UPDATE reservas
SET status = status_reserva
WHERE (status IS NULL OR status = '')
  AND status_reserva IS NOT NULL;

-- Garantir default e NOT NULL quando possivel
ALTER TABLE reservas
ALTER COLUMN status SET DEFAULT 'PENDENTE';

DO $$
DECLARE
    count_sem_status INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_sem_status
    FROM reservas
    WHERE status IS NULL OR status = '';

    IF count_sem_status = 0 THEN
        ALTER TABLE reservas
        ALTER COLUMN status SET NOT NULL;
    END IF;
END $$;

-- Indice para status
CREATE INDEX IF NOT EXISTS idx_reservas_status ON reservas(status);

-- Observacao: Mantendo status_reserva por compatibilidade
-- Para remover, atualize codigo e rode:
-- ALTER TABLE reservas DROP COLUMN status_reserva;

COMMIT;
