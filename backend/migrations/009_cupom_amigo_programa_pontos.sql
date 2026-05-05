-- Cupom amigo e suporte ao programa de pontos por nivel.

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS tipo_campanha VARCHAR(50);

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS cliente_indicador_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'cupons_cliente_indicador_id_fkey'
    ) THEN
        ALTER TABLE cupons
            ADD CONSTRAINT cupons_cliente_indicador_id_fkey
            FOREIGN KEY (cliente_indicador_id)
            REFERENCES clientes(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_cupons_tipo_campanha
    ON cupons(tipo_campanha);

CREATE INDEX IF NOT EXISTS idx_cupons_cliente_indicador_id
    ON cupons(cliente_indicador_id);
