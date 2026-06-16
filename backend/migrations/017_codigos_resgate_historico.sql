-- Jornada Real: permite historico de codigos de resgate por resgate.
-- Ao renovar codigo, o codigo antigo fica cancelado e um novo codigo ativo e gerado.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'codigos_resgate_resgate_id_key'
    ) THEN
        ALTER TABLE codigos_resgate
        DROP CONSTRAINT codigos_resgate_resgate_id_key;
    END IF;
END $$;

DROP INDEX IF EXISTS codigos_resgate_resgate_id_key;

CREATE INDEX IF NOT EXISTS idx_codigos_resgate_resgate_id
    ON codigos_resgate(resgate_id);
