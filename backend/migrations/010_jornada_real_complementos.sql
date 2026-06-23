-- Complementos Jornada Real: niveis configuraveis, codigos rastreados,
-- resgates inutilizaveis e dedupe operacional.

CREATE TABLE IF NOT EXISTS niveis_fidelidade (
    id SERIAL PRIMARY KEY,
    codigo INTEGER NOT NULL UNIQUE,
    nome VARCHAR(80) NOT NULL UNIQUE,
    pontos_minimos INTEGER NOT NULL DEFAULT 0,
    bonus_percentual NUMERIC(5,2) NOT NULL DEFAULT 0,
    beneficios JSONB,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_niveis_fidelidade_ativo_pontos
    ON niveis_fidelidade(ativo, pontos_minimos);

INSERT INTO niveis_fidelidade (
    codigo, nome, pontos_minimos, bonus_percentual, beneficios, ordem, ativo, created_at, updated_at
)
VALUES
    (0, 'INICIAL', 0, 0, '{"descricao": "Entrada na Jornada Real"}', 0, TRUE, NOW(), NOW()),
    (1, 'EXPERIENCIA', 20, 20, '{"pontos_por_reserva": "+20%"}', 1, TRUE, NOW(), NOW()),
    (2, 'REAL', 60, 40, '{"pontos_por_reserva": "+40%"}', 2, TRUE, NOW(), NOW())
ON CONFLICT (codigo) DO UPDATE
SET nome = EXCLUDED.nome,
    bonus_percentual = EXCLUDED.bonus_percentual,
    beneficios = EXCLUDED.beneficios,
    ordem = EXCLUDED.ordem,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'active';

ALTER TABLE cupons
    ADD COLUMN IF NOT EXISTS tracking_slug VARCHAR(80);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cupons_tracking_slug_unique
    ON cupons(tracking_slug)
    WHERE tracking_slug IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cupons_status
    ON cupons(status);

UPDATE cupons
SET status = CASE
    WHEN ativo = FALSE THEN 'cancelled'
    WHEN data_fim < NOW() THEN 'expired'
    WHEN limite_total_usos IS NOT NULL AND total_usos >= limite_total_usos THEN 'max_usage_reached'
    ELSE 'active'
END
WHERE status IS NULL OR status = 'active';

ALTER TABLE resgates_premios
    ADD COLUMN IF NOT EXISTS codigo_resgate VARCHAR(40);

ALTER TABLE resgates_premios
    ADD COLUMN IF NOT EXISTS codigo_status VARCHAR(30) NOT NULL DEFAULT 'active';

ALTER TABLE resgates_premios
    ADD COLUMN IF NOT EXISTS usado_em TIMESTAMP;

ALTER TABLE resgates_premios
    ADD COLUMN IF NOT EXISTS expira_em TIMESTAMP;

CREATE UNIQUE INDEX IF NOT EXISTS idx_resgates_premios_codigo_resgate_unique
    ON resgates_premios(codigo_resgate)
    WHERE codigo_resgate IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_resgates_premios_codigo_status
    ON resgates_premios(codigo_status);

UPDATE resgates_premios
SET codigo_resgate = CONCAT('RES-', LPAD(id::TEXT, 6, '0'))
WHERE codigo_resgate IS NULL;

UPDATE resgates_premios
SET expira_em = created_at + INTERVAL '30 days'
WHERE expira_em IS NULL;
